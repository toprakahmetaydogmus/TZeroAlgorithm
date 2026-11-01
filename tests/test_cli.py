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
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("4.1.0", res.stdout)
        self.assertIn("9.8.0", res.stdout)

    def test_mcp_version_flag(self):
        res = subprocess.run(
            [sys.executable, "tzero_mcp.py", "--version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        import tzero_mcp
        self.assertIn(tzero_mcp.SERVER_VERSION, res.stdout)

    def test_addmcp_version_flag(self):
        res = subprocess.run(
            [sys.executable, "addmcp.py", "--version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        self.assertEqual(res.returncode, 0)
        import addmcp
        self.assertIn(addmcp.APP_VERSION, res.stdout)

    def test_scan_flag(self):
        res = subprocess.run(
            [sys.executable, "tzero_v3.py", "--scan", "."],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("T-ZERO CODEBASE SCANNER", res.stdout)
        self.assertIn("Total:", res.stdout)

    def test_audit_flag(self):
        res = subprocess.run(
            [sys.executable, "tzero_v3.py", "--audit", "."],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("T-ZERO AST STATIC CODE AUDITOR", res.stdout)

    def test_tzero_backward_compatibility_entrypoint(self):
        res = subprocess.run(
            [sys.executable, "tzero.py", "--version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("4.1.0", res.stdout)
        self.assertIn("9.8.0", res.stdout)

    def test_quickstart_info(self):
        res = subprocess.run(
            [sys.executable, "tzero_v3.py", "--info"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("QUICKSTART", res.stdout)
        self.assertIn("tzero-add-mcp", res.stdout)

    def test_natural_subcommands_without_dashes(self):
        # 1. 'tzero audit' should map to '--audit'
        res_audit = subprocess.run(
            [sys.executable, "tzero_v3.py", "audit", "tests/test_cli.py"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        self.assertEqual(res_audit.returncode, 0)
        self.assertIn("T-ZERO AST STATIC CODE AUDITOR", res_audit.stdout)

        # 2. 'tzero doctor' should map to '--doctor'
        res_doc = subprocess.run(
            [sys.executable, "tzero_v3.py", "doctor"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        self.assertEqual(res_doc.returncode, 0)
        self.assertIn("T-Zero Doctor", res_doc.stdout)

        # 3. 'tzero cost' should map to '--cost'
        res_cost = subprocess.run(
            [sys.executable, "tzero_v3.py", "cost", "tests"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        self.assertEqual(res_cost.returncode, 0)
        self.assertIn("TOKEN COST & FINANCIAL ROI COCKPIT", res_cost.stdout)

        # 4. 'tzero drift' should map to '--drift'
        res_drift = subprocess.run(
            [sys.executable, "tzero_v3.py", "drift", "tests"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        self.assertEqual(res_drift.returncode, 0)
        self.assertIn("INSTRUCTION & ARCHITECTURAL DRIFT ANALYZER", res_drift.stdout)


if __name__ == "__main__":
    unittest.main()
