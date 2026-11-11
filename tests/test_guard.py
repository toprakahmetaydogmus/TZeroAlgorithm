# -*- coding: utf-8 -*-
"""Unit tests for T-Zero Git Pre-Commit Zero-Leak & Token Guard."""

import os
import shutil
import tempfile
import unittest

from tzero.tzero_guard import GitSecurityGuard


class TestGitSecurityGuard(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="tzero_guard_test_")
        self.git_dir = os.path.join(self.test_dir, ".git")
        os.makedirs(os.path.join(self.git_dir, "hooks"), exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_install_hook_success(self):
        res = GitSecurityGuard.install_hook(self.test_dir)
        self.assertTrue(res["success"])
        self.assertIn("pre-commit", res["hook_path"])
        self.assertTrue(os.path.exists(res["hook_path"]))
        
        # Verify hook file content contains tzero check command
        with open(res["hook_path"], "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("tzero_guard", content)

    def test_install_hook_non_git_repo(self):
        empty_dir = tempfile.mkdtemp(prefix="tzero_nogit_")
        try:
            res = GitSecurityGuard.install_hook(empty_dir)
            self.assertFalse(res["success"])
            self.assertIn("missing .git", res["message"].lower())
        finally:
            shutil.rmtree(empty_dir, ignore_errors=True)

    def test_scan_staged_content_clean(self):
        files = {
            "app.py": "def hello():\n    return 'Hello, World!'\n",
            "utils.py": "def add(a: int, b: int) -> int:\n    return a + b\n"
        }
        res = GitSecurityGuard.scan_staged_content(files)
        self.assertTrue(res["clean"])
        self.assertEqual(len(res["violations"]), 0)

    def test_scan_staged_content_blocks_secret_leaks(self):
        files = {
            "config.py": "OPENAI_API_KEY = 'sk-proj-9999888877776666555544443333222211110000'\n",
            "service.py": "user_pass = 'SuperSecretPassword123!'"
        }
        res = GitSecurityGuard.scan_staged_content(files)
        self.assertFalse(res["clean"])
        self.assertGreaterEqual(len(res["violations"]), 1)
        files_flagged = [v["file"] for v in res["violations"]]
        self.assertIn("config.py", files_flagged)


if __name__ == "__main__":
    unittest.main()
