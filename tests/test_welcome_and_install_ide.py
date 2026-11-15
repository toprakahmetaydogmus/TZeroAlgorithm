# -*- coding: utf-8 -*-
"""Verification tests for T-Zero Welcome Star Banner, Git Hooks, and IDE Installers."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent


class TestWelcomeAndInstallIde(unittest.TestCase):
    def test_welcome_banner_content(self):
        from tzero.tzero_welcome import get_welcome_banner, REPO_URL
        banner = get_welcome_banner()
        self.assertIn("T-ZERO CONTEXT ARCHITECT & MCP SUITE", banner)
        self.assertIn(REPO_URL, banner)
        self.assertIn("Toprak Ahmet Aydoğmuş", banner)
        self.assertIn("tzero install-ide", banner)

    def test_git_star_hooks_installation(self):
        from tzero.tzero_welcome import install_git_star_hooks
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            # Initialize a bare mock .git dir
            (tmp_path / ".git").mkdir()
            success = install_git_star_hooks(tmp_path)
            self.assertTrue(success)
            githooks = tmp_path / ".githooks"
            self.assertTrue(githooks.is_dir())
            self.assertTrue((githooks / "post-checkout").is_file())
            self.assertTrue((githooks / "post-merge").is_file())
            content = (githooks / "post-checkout").read_text(encoding="utf-8")
            self.assertIn("https://github.com/toprakahmetaydogmus/TZeroAlgorithm", content)

    def test_git_hooks_recursive_discovery(self):
        from tzero.tzero_welcome import find_git_root
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".git").mkdir()
            nested = root / "subdir1" / "subdir2"
            nested.mkdir(parents=True)
            found = find_git_root(nested)
            self.assertEqual(found, root.resolve())

    def test_tzero_addmcp_module_import(self):
        from tzero import addmcp
        self.assertTrue(hasattr(addmcp, "run_init"))
        self.assertTrue(hasattr(addmcp, "run_cli"))
        self.assertTrue(hasattr(addmcp, "build_client_targets"))

    def test_cli_subcommand_install_ide_list(self):
        res = subprocess.run(
            [sys.executable, str(ROOT_DIR / "tzero" / "tzero_v3.py"), "install-ide", "--list"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(ROOT_DIR)
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("T-ZERO 1-CLICK MCP INITIALIZATION", res.stdout)
        self.assertIn("cursor", res.stdout.lower())

    def test_cli_flag_install_ide_list(self):
        res = subprocess.run(
            [sys.executable, str(ROOT_DIR / "tzero" / "tzero_v3.py"), "--install-ide", "--list"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(ROOT_DIR)
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("T-ZERO 1-CLICK MCP INITIALIZATION", res.stdout)

    def test_mcp_cli_install_flag(self):
        res = subprocess.run(
            [sys.executable, str(ROOT_DIR / "tzero" / "tzero_mcp.py"), "--install", "--list"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(ROOT_DIR)
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("cursor", res.stdout.lower())

    def test_postinstall_node_script(self):
        env = os.environ.copy()
        env["TEST_POSTINSTALL"] = "1"
        env["TZERO_NO_BANNER"] = "0"
        res = subprocess.run(
            ["node", str(ROOT_DIR / "installers" / "npm" / "bin" / "postinstall.js")],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(ROOT_DIR),
            env=env,
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("T-ZERO MCP INSTALLED SUCCESSFULLY", res.stdout)
        self.assertIn("https://github.com/toprakahmetaydogmus/TZeroAlgorithm", res.stdout)

    def test_setup_py_execution(self):
        res = subprocess.run(
            [sys.executable, str(ROOT_DIR / "setup.py"), "--version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(ROOT_DIR),
        )
        self.assertEqual(res.returncode, 0, f"setup.py stderr: {res.stderr}")
        self.assertIn("11.12.1", res.stdout)


if __name__ == "__main__":
    unittest.main()
