# -*- coding: utf-8 -*-
"""Comprehensive end-to-end CLI commands and tool verification suite."""

import os
import sys
import unittest
import subprocess
import tempfile
import shutil

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class TestComprehensiveCLI(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _run_cli(self, args):
        cmd = [sys.executable, os.path.join(ROOT_DIR, "tzero_v3.py")] + args
        return subprocess.run(
            cmd,
            cwd=ROOT_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

    def test_cli_version(self):
        res = self._run_cli(["--version"])
        self.assertEqual(res.returncode, 0)
        self.assertIn("4.1.0", res.stdout)
        self.assertIn("7.3.1", res.stdout)

    def test_cli_info(self):
        res = self._run_cli(["--info"])
        self.assertEqual(res.returncode, 0)
        self.assertIn("QUICKSTART", res.stdout)

    def test_cli_doctor(self):
        res = self._run_cli(["--doctor"])
        self.assertEqual(res.returncode, 0)
        self.assertIn("Doctor: environment check", res.stdout)
        self.assertIn("All required checks passed", res.stdout)

    def test_cli_scan(self):
        res = self._run_cli(["--scan", "."])
        self.assertEqual(res.returncode, 0)
        self.assertIn("T-ZERO CODEBASE SCANNER", res.stdout)
        self.assertIn("Total:", res.stdout)

    def test_cli_audit(self):
        res = self._run_cli(["--audit", "."])
        self.assertEqual(res.returncode, 0)
        self.assertIn("T-ZERO AST STATIC CODE AUDITOR", res.stdout)

    def test_cli_savings(self):
        res = self._run_cli(["--savings", "--dir", "."])
        self.assertEqual(res.returncode, 0)
        self.assertIn("Token Reduction & Economic ROI Report", res.stdout)

    def test_cli_diff(self):
        res = self._run_cli(["--diff", "HEAD"])
        self.assertEqual(res.returncode, 0)
        self.assertTrue(
            ("T-Zero Incremental PR Context" in res.stdout) or ("No Git Changes Detected" in res.stdout),
            f"Unexpected diff output: {res.stdout}"
        )

    def test_cli_impact(self):
        res = self._run_cli(["--impact", "TokenReducer", "--dir", "."])
        self.assertEqual(res.returncode, 0)
        self.assertIn("Change Impact & Blast Radius", res.stdout)

    def test_cli_search(self):
        res = self._run_cli(["--search", "TokenReducer", "--dir", "."])
        self.assertEqual(res.returncode, 0)
        self.assertIn("Semantic Code Search", res.stdout)

    def test_cli_dry_run(self):
        out_file = os.path.join(self.temp_dir, "offline_readme.md")
        res = self._run_cli(["--dry-run", "--dir", ".", "--output", out_file])
        self.assertEqual(res.returncode, 0)
        self.assertTrue(os.path.exists(out_file))
        with open(out_file, encoding="utf-8") as f:
            content = f.read()
        self.assertIn("T-Zero Context Tree", content)

    def test_cli_export_agents(self):
        out_file = os.path.join(self.temp_dir, "agents_test.md")
        res = self._run_cli(["--export-agents", out_file, "--dir", "."])
        self.assertEqual(res.returncode, 0)
        self.assertTrue(os.path.exists(out_file))
        with open(out_file, encoding="utf-8") as f:
            content = f.read()
        self.assertIn("AI ASSISTANT BLUEPRINT", content)

    def test_cli_export_arch(self):
        out_file = os.path.join(self.temp_dir, "arch_test.md")
        res = self._run_cli(["--export-arch", out_file, "--dir", "."])
        self.assertEqual(res.returncode, 0)
        self.assertTrue(os.path.exists(out_file))
        with open(out_file, encoding="utf-8") as f:
            content = f.read()
        self.assertIn("mermaid", content)

    def test_cli_export_repomap(self):
        out_file = os.path.join(self.temp_dir, "repomap_test.txt")
        res = self._run_cli(["--export-repomap", out_file, "--dir", "."])
        self.assertEqual(res.returncode, 0)
        self.assertTrue(os.path.exists(out_file))
        with open(out_file, encoding="utf-8") as f:
            content = f.read()
        self.assertIn("REPO MAP", content)

    def test_cli_export_html(self):
        out_file = os.path.join(self.temp_dir, "preview_test.html")
        res = self._run_cli(["--export-html", out_file, "--dir", "."])
        self.assertEqual(res.returncode, 0)
        self.assertTrue(os.path.exists(out_file))
        with open(out_file, encoding="utf-8") as f:
            content = f.read()
        self.assertIn("<!DOCTYPE html>", content)

    def test_cli_export_agent_rules(self):
        res = self._run_cli(["--export-agent-rules", "--dir", self.temp_dir])
        self.assertEqual(res.returncode, 0)
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, ".cursorrules")))
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir, ".clinerules")))

    def test_cli_enforce_boundaries(self):
        rules_path = os.path.join(ROOT_DIR, "tzero.rules.json")
        res = self._run_cli(["--enforce-boundaries", rules_path, "--dir", "."])
        self.assertEqual(res.returncode, 0)
        self.assertIn("[ARCH PASS]", res.stdout)

    def test_cli_audit_sarif(self):
        res = self._run_cli(["--audit", ".", "--format", "sarif"])
        self.assertEqual(res.returncode, 0)
        self.assertIn('"version": "2.1.0"', res.stdout)
        self.assertIn("StaticCodeAnalyzer", res.stdout)

    def test_cli_audit_json(self):
        import json
        res = self._run_cli(["--audit", ".", "--format", "json"])
        self.assertEqual(res.returncode, 0)
        data = json.loads(res.stdout)
        self.assertIn("total_issues", data)
        self.assertIn("issues", data)

    def test_cli_pr_report(self):
        res = self._run_cli(["--pr-report", "HEAD"])
        self.assertEqual(res.returncode, 0)
        self.assertIn("T-Zero Autonomous PR Architecture & Security Report", res.stdout)


if __name__ == "__main__":
    unittest.main()
