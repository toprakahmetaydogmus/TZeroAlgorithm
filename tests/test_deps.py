# -*- coding: utf-8 -*-
"""Tests for the dependency bootstrap and the --doctor report (no real pip installs happen here)."""

import contextlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tzero import tzero_deps
from tzero.tzero_deps import Dependency

FAKE_MISSING = Dependency("definitely_not_a_real_module_xyz", "fake-package", "1.0.0", "test")


class TestVersionHelpers(unittest.TestCase):
    def test_version_tuple_ordering(self):
        self.assertLess(tzero_deps._version_tuple("2.9.1"), tzero_deps._version_tuple("2.28.0"))
        self.assertEqual(tzero_deps._version_tuple("1.0.0rc1"), (1, 0, 0))
        self.assertEqual(tzero_deps._version_tuple("23.13.1"), (23, 13, 1))

    def test_check_dependency_statuses(self):
        self.assertEqual(tzero_deps.check_dependency(FAKE_MISSING)[0], "missing")
        outdated = Dependency("requests", "requests", "999.0.0", "test")
        self.assertEqual(tzero_deps.check_dependency(outdated)[0], "outdated")
        present = Dependency("requests", "requests", "0.0.1", "test")
        self.assertEqual(tzero_deps.check_dependency(present)[0], "ok")


class TestEnsureDependencies(unittest.TestCase):
    def test_noop_when_everything_is_installed(self):
        with mock.patch("subprocess.run", side_effect=AssertionError("pip must not run")):
            self.assertTrue(tzero_deps.ensure_dependencies())

    def test_frozen_build_never_installs(self):
        with mock.patch.object(sys, "frozen", True, create=True), \
                mock.patch.object(tzero_deps, "REQUIRED", [FAKE_MISSING]), \
                mock.patch("subprocess.run", side_effect=AssertionError("pip must not run")):
            self.assertTrue(tzero_deps.ensure_dependencies())

    def test_missing_packages_do_not_install_or_change_path_by_default(self):
        with mock.patch.object(tzero_deps, "REQUIRED", [FAKE_MISSING]), \
                mock.patch("subprocess.run", side_effect=AssertionError("pip must not run")), \
                mock.patch.dict(os.environ, {"PATH": ""}), \
                contextlib.redirect_stderr(io.StringIO()) as stderr:
            self.assertFalse(tzero_deps.ensure_dependencies())
            self.assertEqual(os.environ["PATH"], "")
        self.assertIn("Install manually", stderr.getvalue())

    def test_opt_out_env_blocks_install(self):
        stderr = io.StringIO()
        with mock.patch.object(tzero_deps, "REQUIRED", [FAKE_MISSING]), \
                mock.patch.dict(os.environ, {tzero_deps.OPT_OUT_ENV: "1"}), \
                mock.patch("subprocess.run", side_effect=AssertionError("pip must not run")), \
                contextlib.redirect_stderr(stderr):
            self.assertFalse(tzero_deps.ensure_dependencies(install=True))
        self.assertIn("fake-package>=1.0.0", stderr.getvalue())

    def test_successful_install_path(self):
        done = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
        statuses = [("missing", None), ("ok", "1.0.0")]
        with mock.patch.object(tzero_deps, "REQUIRED", [FAKE_MISSING]), \
                mock.patch.dict(os.environ, {}, clear=False), \
                mock.patch("subprocess.run", return_value=done) as run, \
                mock.patch.object(tzero_deps, "check_dependency", side_effect=statuses), \
                contextlib.redirect_stderr(io.StringIO()):
            os.environ.pop(tzero_deps.OPT_OUT_ENV, None)
            self.assertTrue(tzero_deps.ensure_dependencies(install=True))
        command = run.call_args[0][0]
        self.assertEqual(command[1:4], ["-m", "pip", "install"])
        self.assertIn("fake-package>=1.0.0", command)

    def test_failed_install_reports_manual_command(self):
        failed = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="boom")
        stderr = io.StringIO()
        with mock.patch.object(tzero_deps, "REQUIRED", [FAKE_MISSING]), \
                mock.patch("subprocess.run", return_value=failed), \
                contextlib.redirect_stderr(stderr):
            os.environ.pop(tzero_deps.OPT_OUT_ENV, None)
            self.assertFalse(tzero_deps.ensure_dependencies(install=True))
        self.assertIn("Install manually", stderr.getvalue())

    def test_install_output_never_touches_stdout(self):
        """stdout is the MCP protocol channel, so the installer must only write to stderr."""
        done = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
        stdout = io.StringIO()
        with mock.patch.object(tzero_deps, "REQUIRED", [FAKE_MISSING]), \
                mock.patch("subprocess.run", return_value=done), \
                mock.patch.object(tzero_deps, "check_dependency", side_effect=[("missing", None), ("ok", "1")]), \
                contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(io.StringIO()):
            os.environ.pop(tzero_deps.OPT_OUT_ENV, None)
            tzero_deps.ensure_dependencies(install=True)
        self.assertEqual(stdout.getvalue(), "")


class TestOptInPath(unittest.TestCase):
    @unittest.skipIf(os.name == "nt", "Bash startup files apply to Unix")
    def test_explicit_bash_update_is_quoted_and_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            scripts = directory / "developer's scripts"
            config = directory / ".bashrc"
            config.write_bytes(b"# keep existing content")
            process_path = os.environ.get("PATH")
            with mock.patch.object(tzero_deps, "_tzero_scripts_directory", return_value=scripts), \
                    mock.patch.object(Path, "home", return_value=directory), \
                    mock.patch.object(sys, "argv", ["tzero_deps", "--add-to-path", "--shell", "bash"]), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(tzero_deps.main(), 0)
                first = config.read_bytes()
                self.assertEqual(tzero_deps.main(), 0)
            self.assertEqual(config.read_bytes(), first)
            self.assertTrue(first.startswith(b"# keep existing content\n"))
            self.assertEqual(os.environ.get("PATH"), process_path)
            bash = shutil.which("bash")
            if bash:
                command = '. "$1"; . "$1"; printf %s "$PATH"'
                result = subprocess.check_output([bash, "-c", command, "_", str(config)], text=True)
                self.assertEqual(result.split(os.pathsep).count(str(scripts)), 1)

    def test_windows_appends_to_user_path_and_preserves_value_type(self):
        registry = mock.MagicMock()
        registry.REG_SZ, registry.REG_EXPAND_SZ = 1, 2
        registry.KEY_READ, registry.KEY_SET_VALUE = 1, 2
        registry.ExpandEnvironmentStrings.side_effect = lambda value: value
        existing = r"C:\Other"
        scripts = Path(r"C:\Tools\Scripts")
        registry.QueryValueEx.return_value = (existing, registry.REG_EXPAND_SZ)
        with mock.patch.dict(sys.modules, {"winreg": registry}):
            self.assertTrue(tzero_deps._append_windows_user_path(scripts))
            key = registry.CreateKeyEx.return_value.__enter__.return_value
            registry.SetValueEx.assert_called_once_with(key, "Path", 0, registry.REG_EXPAND_SZ, f"{existing};{scripts}")
            registry.SetValueEx.reset_mock()
            registry.QueryValueEx.return_value = (f"{existing};{scripts}", registry.REG_EXPAND_SZ)
            self.assertFalse(tzero_deps._append_windows_user_path(scripts))
            registry.SetValueEx.assert_not_called()


class TestDoctor(unittest.TestCase):
    def test_doctor_reports_and_succeeds(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = tzero_deps.run_doctor()
        text = out.getvalue()
        self.assertEqual(code, 0, text)
        self.assertIn("T-Zero Doctor", text)
        self.assertIn("requests", text)
        self.assertIn("All required checks passed", text)

    def test_doctor_cli_flag(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        proc = subprocess.run([sys.executable, "main.py", "--doctor"], cwd=root,
                              capture_output=True, text=True, timeout=300)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("T-Zero Doctor", proc.stdout)


if __name__ == "__main__":
    unittest.main()
