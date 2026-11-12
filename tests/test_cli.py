# -*- coding: utf-8 -*-
"""Integration tests for CLI execution."""

import os
import sys
import subprocess
import tomllib
import unittest
from pathlib import Path


with (Path(__file__).resolve().parents[1] / "pyproject.toml").open("rb") as manifest:
    PACKAGE_VERSION = tomllib.load(manifest)["project"]["version"]


class TestCLI(unittest.TestCase):
    def test_version_flag(self):
        res = subprocess.run(
            [sys.executable, "tzero/tzero_v3.py", "--version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("4.1.0", res.stdout)
        self.assertIn(f"v{PACKAGE_VERSION} ", res.stdout)

    def test_mcp_version_flag(self):
        res = subprocess.run(
            [sys.executable, "tzero/tzero_mcp.py", "--version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
        from tzero import tzero_mcp
        self.assertIn(tzero_mcp.SERVER_VERSION, res.stdout)

    def test_legacy_root_mcp_entrypoint(self):
        res = subprocess.run(
            [sys.executable, "tzero_mcp.py", "--version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        from tzero import tzero_mcp
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
            [sys.executable, "tzero/tzero_v3.py", "--scan", "."],
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
            [sys.executable, "tzero/tzero_v3.py", "--audit", "."],
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
        self.assertIn(f"v{PACKAGE_VERSION} ", res.stdout)

    def test_quickstart_info(self):
        res = subprocess.run(
            [sys.executable, "tzero/tzero_v3.py", "--info"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("QUICKSTART", res.stdout)
        self.assertIn("tzero-add-mcp", res.stdout)

    def test_watch_mode(self):
        from tzero import tzero_v3
        res = tzero_v3.run_watch_mode("tests", once_test=True)
        self.assertTrue(res)

    def test_natural_subcommands_without_dashes(self):
        # 1. 'tzero audit' should map to '--audit'
        res_audit = subprocess.run(
            [sys.executable, "tzero/tzero_v3.py", "audit", "tests/test_cli.py"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        self.assertEqual(res_audit.returncode, 0)
        self.assertIn("T-ZERO AST STATIC CODE AUDITOR", res_audit.stdout)

        # 2. 'tzero doctor' should map to '--doctor'
        res_doc = subprocess.run(
            [sys.executable, "tzero/tzero_v3.py", "doctor"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        self.assertEqual(res_doc.returncode, 0)
        self.assertIn("T-Zero Doctor", res_doc.stdout)

        # 3. 'tzero cost' should map to '--cost'
        res_cost = subprocess.run(
            [sys.executable, "tzero/tzero_v3.py", "cost", "tests"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        self.assertEqual(res_cost.returncode, 0)
        self.assertIn("TOKEN COST & FINANCIAL ROI COCKPIT", res_cost.stdout)

        # 4. 'tzero drift' should map to '--drift'
        res_drift = subprocess.run(
            [sys.executable, "tzero/tzero_v3.py", "drift", "tests"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        self.assertEqual(res_drift.returncode, 0)
        self.assertIn("INSTRUCTION & ARCHITECTURAL DRIFT ANALYZER", res_drift.stdout)

        # 5. 'tzero review' should run autonomous code review gate
        import tempfile
        with tempfile.TemporaryDirectory() as review_dir:
            subprocess.run(["git", "init", "-q", review_dir], check=True)
            res_rev = subprocess.run(
                [sys.executable, "tzero/tzero_v3.py", "review", "--dir", review_dir],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        self.assertEqual(res_rev.returncode, 0)
        self.assertIn("T-ZERO AUTONOMOUS CODE REVIEW & REALITY-LOCK GATE", res_rev.stdout)

        # 6. 'tzero demo' should run live instant demo
        res_demo = subprocess.run(
            [sys.executable, "tzero/tzero_v3.py", "demo"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        self.assertEqual(res_demo.returncode, 0)
        self.assertIn("LIVE INSTANT DEMONSTRATION", res_demo.stdout)
        self.assertIn("AST Token Reduction", res_demo.stdout)

        # 7. 'tzero check-arch' should run architecture live audit
        res_arch = subprocess.run(
            [sys.executable, "tzero/tzero_v3.py", "check-arch"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        self.assertEqual(res_arch.returncode, 0)
        self.assertIn("T-ZERO ARCH-AUDIT PASS", res_arch.stdout)

        # 8. 'tzero contracts' should run public API contract guardian
        res_contracts = subprocess.run(
            [sys.executable, "tzero/tzero_v3.py", "contracts", "HEAD"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        self.assertEqual(res_contracts.returncode, 0)
        self.assertIn("T-ZERO CONTRACT GUARDIAN", res_contracts.stdout)

        # 9. 'tzero debt' should run code health and technical debt index
        res_debt = subprocess.run(
            [sys.executable, "tzero/tzero_v3.py", "debt", "tests/test_cli.py"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        self.assertEqual(res_debt.returncode, 0)
        self.assertIn("T-Zero Code Health & Technical Debt Index", res_debt.stdout)

        # 10. 'tzero budget' should run context budget optimizer and compression certifier
        res_budget = subprocess.run(
            [sys.executable, "tzero/tzero_v3.py", "budget", "tests/test_cli.py", "--target-tokens", "5000"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        self.assertEqual(res_budget.returncode, 0)
        self.assertIn("T-Zero Context Budget & Compression Certificate", res_budget.stdout)

        # 11. 'tzero golden' should generate golden baseline
        res_golden = subprocess.run(
            [sys.executable, "tzero/tzero_v3.py", "golden", "generate"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        self.assertEqual(res_golden.returncode, 0)
        self.assertIn("T-ZERO GOLDEN ENGINE", res_golden.stdout)

    def test_export_repomap_stdout_dash(self):
        import tempfile
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "mod.py"), "w", encoding="utf-8") as fh:
                fh.write("def hello_world() -> str:\n    return 'ok'\n")
            res = subprocess.run(
                [sys.executable, os.path.join(root_dir, "tzero", "tzero_v3.py"), "--export-repomap", "-", "--dir", tmp],
                cwd=tmp,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            self.assertEqual(res.returncode, 0)
            self.assertIn("hello_world", res.stdout)
            self.assertFalse(os.path.exists(os.path.join(tmp, "-")))


    def test_scan_json_format(self):
        import json
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "alpha.py"), "w", encoding="utf-8") as fh:
                fh.write(
                    "def process_items(items: list) -> int:\n"
                    "    total = 0\n"
                    "    for x in items:\n"
                    "        total += x * 2\n"
                    "    return total\n"
                )
            with open(os.path.join(tmp, "beta.ts"), "w", encoding="utf-8") as fh:
                fh.write(
                    "export function formatLabel(name: string): string {\n"
                    "    const cleaned = name.trim();\n"
                    "    return cleaned.toUpperCase();\n"
                    "}\n"
                )
            proc = subprocess.run(
                [sys.executable, "tzero/tzero_v3.py", "--scan", tmp, "--format", "json"],
                capture_output=True,
                text=True,
                check=True,
            )
            data = json.loads(proc.stdout)
            self.assertEqual(data["total_files"], 2)
            self.assertGreater(data["raw_tokens"], 0)
            self.assertLessEqual(data["pruned_tokens"], data["raw_tokens"])
            self.assertIn("savings_pct", data)
            self.assertIsInstance(data["files"], list)
            self.assertEqual(len(data["files"]), 2)


if __name__ == "__main__":
    unittest.main()
