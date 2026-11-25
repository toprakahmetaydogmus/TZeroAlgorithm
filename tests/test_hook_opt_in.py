"""Regression coverage for issue #43: install/startup must preserve user hooks."""

import contextlib
import io
import os
import runpy
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import ModuleType
from unittest.mock import Mock, patch

from tzero import tzero_welcome as welcome

ROOT = Path(__file__).resolve().parents[1]


class TestHookOptIn(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.environment = patch.dict(os.environ, {
            "GIT_CONFIG_GLOBAL": str(self.root / "global.gitconfig"),
            "GIT_CONFIG_NOSYSTEM": "1",
        })
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.git("init")

    def git(self, *args, cwd=None, check=True):
        return subprocess.run(
            ["git", *args], cwd=cwd or self.repo, check=check,
            text=True, capture_output=True,
        )

    def snapshot(self):
        return {p.relative_to(self.repo): p.read_bytes()
                for p in self.repo.rglob("*") if p.is_file()}

    def test_setup_has_no_install_or_develop_side_effects(self):
        before = self.snapshot()
        # setuptools is a build dependency, absent from clean Python 3.12+ runtimes.
        setuptools = ModuleType("setuptools")
        setuptools.setup = Mock()
        with patch.dict("sys.modules", {"setuptools": setuptools}), \
             patch.object(welcome, "install_git_star_hooks") as install:
            runpy.run_path(str(ROOT / "setup.py"), run_name="__main__")
        self.assertNotIn("cmdclass", setuptools.setup.call_args.kwargs)
        install.assert_not_called()
        self.assertEqual(before, self.snapshot())

    def test_banner_and_default_welcome_do_not_install_hooks(self):
        before = self.snapshot()
        with patch.object(welcome, "install_git_star_hooks") as install, \
             patch.object(welcome, "check_first_launch_repo_open"), \
             contextlib.redirect_stdout(io.StringIO()):
            welcome.print_star_banner(force=True)
            self.assertEqual(welcome.main([]), 0)
        install.assert_not_called()
        self.assertEqual(before, self.snapshot())

    def test_welcome_command_requires_explicit_flag(self):
        with patch.object(welcome, "print_star_banner"), \
             patch.object(welcome, "install_git_star_hooks", return_value=True) as install, \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(welcome.main(["--install-star-hooks"]), 0)
        install.assert_called_once_with()

    def test_explicit_failure_is_visible_and_nonzero(self):
        with patch.object(welcome, "print_star_banner"), \
             patch.object(welcome, "install_git_star_hooks", return_value=False):
            self.assertEqual(welcome.main(["--install-star-hooks"]), 1)

    def test_local_and_global_hook_managers_are_preserved(self):
        for scope in ("--local", "--global"):
            with self.subTest(scope=scope):
                self.git("config", scope, "core.hooksPath", ".husky/_")
                before = self.snapshot()
                with self.assertWarnsRegex(UserWarning, "already configured"):
                    self.assertFalse(welcome.install_git_star_hooks(self.repo))
                self.assertEqual(before, self.snapshot())
                self.assertEqual(self.git("config", "--get", "core.hooksPath").stdout.strip(), ".husky/_")
                self.git("config", scope, "--unset", "core.hooksPath")

    def test_empty_configured_hooks_path_is_preserved(self):
        self.git("config", "core.hooksPath", "")
        before = self.snapshot()
        with self.assertWarnsRegex(UserWarning, "already configured"):
            self.assertFalse(welcome.install_git_star_hooks(self.repo))
        self.assertEqual(before, self.snapshot())

    def test_existing_default_hooks_are_preserved(self):
        for name in ("pre-commit", "post-checkout", "post-merge"):
            with self.subTest(hook=name):
                hook = self.repo / ".git" / "hooks" / name
                hook.write_text("#!/bin/sh\necho user hook\n", encoding="utf-8")
                before = self.snapshot()
                with self.assertWarnsRegex(UserWarning, "existing Git hooks"):
                    self.assertFalse(welcome.install_git_star_hooks(self.repo))
                self.assertEqual(before, self.snapshot())
                hook.unlink()

    def test_opt_in_installs_executable_hooks_without_changing_config(self):
        before = (self.repo / ".git" / "config").read_bytes()
        self.assertTrue(welcome.install_git_star_hooks(self.repo))
        self.assertEqual(before, (self.repo / ".git" / "config").read_bytes())
        self.assertFalse((self.repo / ".githooks").exists())
        self.assertEqual(self.git("config", "--get", "core.hooksPath", check=False).returncode, 1)
        for name in ("post-checkout", "post-merge"):
            hook = self.repo / ".git" / "hooks" / name
            self.assertIn(welcome.REPO_URL, hook.read_text(encoding="utf-8"))
            if os.name != "nt":
                self.assertTrue(os.access(hook, os.X_OK))
            sh_bin = shutil.which("sh")
            if sh_bin:
                self.assertEqual(subprocess.run([sh_bin, str(hook)], capture_output=True).returncode, 0)

    def test_linked_worktree_uses_default_shared_hooks_directory(self):
        self.git("-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                 "commit", "--allow-empty", "-m", "fixture")
        worktree = self.root / "worktree"
        self.git("worktree", "add", "-b", "fixture", str(worktree))
        self.assertTrue(welcome.install_git_star_hooks(worktree))
        self.assertTrue((self.repo / ".git" / "hooks" / "post-merge").is_file())
        self.assertFalse((worktree / ".githooks").exists())

    def test_partial_failure_rolls_back_created_hooks(self):
        original_open = Path.open

        def fail_second(path, *args, **kwargs):
            if path.name == "post-merge" and args and args[0] == "x":
                raise PermissionError("simulated write failure")
            return original_open(path, *args, **kwargs)

        before = self.snapshot()
        with patch.object(Path, "open", fail_second), \
             self.assertWarnsRegex(UserWarning, "simulated write failure"):
            self.assertFalse(welcome.install_git_star_hooks(self.repo))
        self.assertEqual(before, self.snapshot())

    def test_non_repository_and_git_errors_are_reported(self):
        with self.assertWarnsRegex(UserWarning, "not inside a Git repository"):
            self.assertFalse(welcome.install_git_star_hooks(self.root))
        with patch.object(welcome.subprocess, "run", side_effect=FileNotFoundError("git missing")), \
             self.assertWarnsRegex(UserWarning, "git missing"):
            self.assertFalse(welcome.install_git_star_hooks(self.repo))

    def test_concurrent_hook_creation_is_never_overwritten(self):
        original_open = Path.open
        hook = self.repo / ".git" / "hooks" / "post-merge"

        def create_second(path, *args, **kwargs):
            if path == hook and args and args[0] == "x":
                with original_open(path, "w", encoding="utf-8") as stream:
                    stream.write("user hook created concurrently")
            return original_open(path, *args, **kwargs)

        with patch.object(Path, "open", create_second), \
             self.assertWarnsRegex(UserWarning, "not installed"):
            self.assertFalse(welcome.install_git_star_hooks(self.repo))
        self.assertEqual(hook.read_text(encoding="utf-8"), "user hook created concurrently")
        self.assertFalse((hook.parent / "post-checkout").exists())

    def test_npm_bundled_module_matches(self):
        relative = Path("tzero/tzero_welcome.py")
        self.assertEqual((ROOT / relative).read_bytes(),
                         (ROOT / "installers/npm/src" / relative).read_bytes())
