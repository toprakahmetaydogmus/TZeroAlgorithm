# -*- coding: utf-8 -*-
"""Integration tests for CLI execution."""

import os
import sys
import subprocess
import unittest


class TestCLI(unittest.TestCase):
    def test_version_flag(self):
        res = subprocess.run(
            [sys.executable, "tzero_v3.py", "--version"],
            capture_output=True,
            text=True
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("3.0.0", res.stdout)

    def test_scan_flag(self):
        res = subprocess.run(
            [sys.executable, "tzero_v3.py", "--scan", "."],
            capture_output=True,
            text=True
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("T-ZERO CODEBASE SCANNER", res.stdout)
        self.assertIn("Total:", res.stdout)

    def test_audit_flag(self):
        res = subprocess.run(
            [sys.executable, "tzero_v3.py", "--audit", "."],
            capture_output=True,
            text=True
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("T-ZERO AST STATIC CODE AUDITOR", res.stdout)

    def test_tzero_backward_compatibility_entrypoint(self):
        res = subprocess.run(
            [sys.executable, "tzero.py", "--version"],
            capture_output=True,
            text=True
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("3.0.0", res.stdout)


if __name__ == "__main__":
    unittest.main()
