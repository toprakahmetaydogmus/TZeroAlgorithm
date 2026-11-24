# -*- coding: utf-8 -*-
"""Unit tests for T-Zero Local CI Suite and Pre-Push Verification Shield.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
Repository: https://github.com/toprakahmetaydogmus/TZeroAlgorithm
"""

import os
import json
import re
import tempfile
import pathlib
import unittest
import subprocess
import sys

from tzero.tzero_ci import LocalCIRunner, LocalCIStepResult, LocalCIReport, CIPipelineGenerator

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent


class TestLocalCI(unittest.TestCase):
    """Verifies all capabilities of the Local CI Runner and Pre-Push Guard."""

    def setUp(self):
        self.runner = LocalCIRunner(repo_dir=str(ROOT_DIR), quick=True)

    def test_runner_initialization(self):
        self.assertEqual(self.runner.repo_dir, str(ROOT_DIR.resolve()))
        self.assertTrue(self.runner.quick)
        self.assertFalse(self.runner.auto_fix)

    def test_step_metadata_sync(self):
        res = self.runner.check_metadata_sync()
        self.assertIsInstance(res, LocalCIStepResult)
        self.assertTrue(res.passed, f"Metadata sync failed: {res.error}")
        self.assertTrue("12." in res.output or "11." in res.output)

    def test_step_zero_leak_security(self):
        res = self.runner.check_zero_leak_security()
        self.assertIsInstance(res, LocalCIStepResult)
        self.assertTrue(res.passed, f"Zero-leak security audit failed: {res.error}")
        self.assertIn("Zero hardcoded secrets", res.output)

    def test_step_ast_and_boundaries(self):
        res = self.runner.check_ast_and_boundaries()
        self.assertIsInstance(res, LocalCIStepResult)
        self.assertTrue(res.passed, f"AST and boundaries check failed: {res.error}")
        self.assertIn("0 syntax faults", res.output)

    def test_step_m8ven_compliance(self):
        res = self.runner.check_m8ven_compliance()
        self.assertIsInstance(res, LocalCIStepResult)
        self.assertTrue(res.passed, f"M8ven compliance failed: {res.error}")
        self.assertIn("M8ven Verified Publisher", res.output)

    def test_full_pipeline_run_quick(self):
        report = self.runner.run()
        self.assertIsInstance(report, LocalCIReport)
        self.assertEqual(report.total_steps, 7)
        self.assertTrue(report.passed, f"Local CI failed with errors: {[s.error for s in report.steps if not s.passed]}")
        self.assertEqual(report.failed_steps, 0)
        self.assertGreaterEqual(report.estimated_actions_minutes_saved, 10.0)

        # JSON dictionary export
        data = report.to_dict()
        self.assertIn("workspace", data)
        self.assertTrue(data["passed"])
        self.assertEqual(len(data["steps"]), 7)

    def test_terminal_report_rendering(self):
        report = self.runner.run()
        rendered = LocalCIRunner.render_terminal_report(report)
        self.assertIn("T-ZERO LOCAL CI & PRE-PUSH VERIFICATION RUNNER", rendered)
        self.assertIn("ALL LOCAL CI GATES PASSED", rendered)
        self.assertIn("Remote CI minutes saved", rendered)

    def test_git_pre_push_hook_lifecycle(self):
        with tempfile.TemporaryDirectory() as td:
            git_hooks_dir = os.path.join(td, ".git", "hooks")
            os.makedirs(git_hooks_dir, exist_ok=True)

            # Install hook
            ok, hook_path = LocalCIRunner.install_git_pre_push_hook(td)
            self.assertTrue(ok)
            self.assertTrue(os.path.exists(hook_path))

            with open(hook_path, "r", encoding="utf-8") as fp:
                content = fp.read()
            self.assertIn("T-Zero Autonomous Local CI Pre-Push Gate", content)
            self.assertIn("local-ci --quick", content)

            # Uninstall hook
            ok_un, msg_un = LocalCIRunner.uninstall_git_pre_push_hook(td)
            self.assertTrue(ok_un)
            self.assertFalse(os.path.exists(hook_path))

    def test_cli_local_ci_flags(self):
        # Run CLI with --version
        cmd_ver = [sys.executable, "-m", "tzero.tzero_ci", "--version"]
        proc_ver = subprocess.run(cmd_ver, cwd=str(ROOT_DIR), capture_output=True, text=True)
        self.assertEqual(proc_ver.returncode, 0, f"--version failed:\n{proc_ver.stderr}\n{proc_ver.stdout}")
        pyproject_text = (ROOT_DIR / "pyproject.toml").read_text(encoding="utf-8")
        ver_match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject_text, re.MULTILINE)
        canonical_ver = ver_match.group(1) if ver_match else "12.2.0"
        self.assertIn(canonical_ver, proc_ver.stdout + proc_ver.stderr)

        # Run CLI with --quick and --json
        cmd = [sys.executable, "-m", "tzero.tzero_ci", "--quick", "--json"]
        proc = subprocess.run(cmd, cwd=str(ROOT_DIR), capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, f"CLI execution failed:\n{proc.stderr}\n{proc.stdout}")
        data = json.loads(proc.stdout)
        self.assertTrue(data["passed"])
        self.assertEqual(data["total_steps"], 7)

    def test_mcp_local_ci_tool_routing(self):
        import asyncio
        from tzero import tzero_mcp
        server = tzero_mcp.create_mcp_server()
        res = asyncio.run(server.call_tool("execute_codebase_workflow", {"action": "ci", "options": {"quick": True}}))
        self.assertTrue(hasattr(res, "content") and len(res.content) > 0)
        text = res.content[0].text
        self.assertIn("T-Zero Local CI Verification Report", text)
        self.assertIn("ALL PASSED", text)


if __name__ == "__main__":
    unittest.main()
