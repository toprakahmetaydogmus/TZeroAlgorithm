# -*- coding: utf-8 -*-
"""Verification tests for multi-OS CI workflow completeness."""

import pathlib
import unittest

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent


class TestCIWorkflow(unittest.TestCase):
    def test_github_actions_covers_multi_os_node_and_sync_gates(self):
        ci_text = (ROOT_DIR / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        self.assertIn("ubuntu-24.04", ci_text)
        self.assertIn("windows-latest", ci_text)
        self.assertIn("macos-latest", ci_text)
        self.assertIn("setup-node", ci_text)
        self.assertIn("node --test installers/npm/test/package.test.js", ci_text)
        self.assertIn("node --test extensions/vscode/test/extension.test.js", ci_text)
        self.assertIn("scripts/sync_release_metadata.py --check", ci_text)
        self.assertIn("tests/audit_secrets.py", ci_text)


if __name__ == "__main__":
    unittest.main()
