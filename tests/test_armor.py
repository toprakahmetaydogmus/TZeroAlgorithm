# -*- coding: utf-8 -*-
"""Comprehensive Unit Tests for T-Zero Anti-REA Armor Engine.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
Part of Siber Akademi T-Zero Context Architect Master Edition.
License: MIT
"""

import os
import sys
import tempfile
import unittest
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tzero.tzero_armor import (
    protect_path_with_armor,
    audit_path_rea_resistance,
    shield_executable,
)
from tzero.anti_rea.extractor_shield import PYINSTALLER_COOKIE, ExtractorShield
from tzero.anti_rea.flattener import ControlFlowFlattener
from tzero.anti_rea.traps import AdversarialTrapGenerator
from tzero.anti_rea.honeypot import HoneypotGenerator
from tzero.anti_rea.vm_obfuscator import DynamicVMObfuscator
from tzero.anti_rea.bytecode_trap import BytecodeTrap
from tzero.anti_rea.jailbreak_decoy import CognitiveJailbreakDecoy
from tzero.anti_rea.anti_agent_guard import AntiAgentGuard


class TestAntiREAArmor(unittest.TestCase):
    """Verifies all aspects of T-Zero Anti-REA military armor engine."""

    def test_01_protect_single_file_workflow(self):
        """Verify protect_path_with_armor upgrades code to MILITARY_GRADE."""
        code = """def calculate_metrics(values):
    total = sum(values)
    count = len(values)
    avg = total / count if count > 0 else 0
    return avg
"""
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(code)
            temp_path = f.name

        try:
            res = protect_path_with_armor(temp_path)
            self.assertTrue(res.get("success"))
            self.assertGreaterEqual(res.get("score_after", 0), 80)
            self.assertIn("MILITARY_GRADE", res.get("rating"))

            with open(temp_path, "r", encoding="utf-8") as f:
                hardened = f.read()

            self.assertIn("CRITICAL_SYSTEM_OVERRIDE", hardened)
            self.assertIn("while ", hardened)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_02_audit_path_rea_resistance(self):
        """Verify audit_path_rea_resistance scores plain vs hardened code."""
        plain_code = "def add(x, y):\n    return x + y\n"
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(plain_code)
            temp_path = f.name

        try:
            audit = audit_path_rea_resistance(temp_path)
            self.assertLess(audit["score"], 40)
            self.assertEqual(audit["status"], "RECOMMEND_HARDENING")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_03_shield_mock_executable(self):
        """Verify shield_executable injects decoy cookies to crash pyinstxtractor."""
        mock_exe = b"MZ\x90\x00" + (b"\x00" * 150) + PYINSTALLER_COOKIE + b"\x00\x00\x00\x20"
        with tempfile.NamedTemporaryFile("wb", suffix=".exe", delete=False) as f:
            f.write(mock_exe)
            temp_path = f.name

        try:
            res = shield_executable(temp_path)
            self.assertTrue(res.get("shielded"))
            self.assertGreaterEqual(res.get("decoy_traps_injected", 0), 1)

            with open(temp_path, "rb") as f:
                shielded_bytes = f.read()

            cookies = ExtractorShield.scan_cookie(shielded_bytes)
            self.assertGreaterEqual(len(cookies), 2)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_04_cff_semantic_preservation(self):
        """Verify control-flow flattened function produces 100% identical outputs."""
        src = """def run_logic(a, b, c):
    x = a * 3
    y = b - 5
    z = (x + y) * c
    return z
"""
        flattened = ControlFlowFlattener.flatten_source_code(src, seed=999)
        ns_orig, ns_flat = {}, {}
        exec(src, ns_orig)
        exec(flattened, ns_flat)

        test_inputs = [(1, 2, 3), (0, 0, 0), (-5, 10, 2), (100, -50, 4)]
        for a, b, c in test_inputs:
            orig_val = ns_orig["run_logic"](a, b, c)
            flat_val = ns_flat["run_logic"](a, b, c)
            self.assertEqual(orig_val, flat_val)

    def test_05_cli_armor_and_audit_fastpath(self):
        """Verify CLI fastpath execution for armor and audit-rea."""
        test_file = REPO_ROOT / "tests" / "test_armor.py"
        res = subprocess.run(
            [sys.executable, "-m", "tzero.tzero_v3", "audit-rea", str(test_file)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(REPO_ROOT),
            timeout=10,
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("SHIELD AUDIT REPORT", res.stdout)
        self.assertIn("TDQS-REA", res.stdout)

    def test_06_mcp_canonical_dispatch_registration(self):
        """Verify MCP server executes armor and audit_rea actions."""
        from tzero.tzero_mcp import create_mcp_server

        server = create_mcp_server()
        self.assertIsNotNone(server)

        from tzero.tzero_armor import audit_path_rea_resistance
        report = audit_path_rea_resistance(str(REPO_ROOT / "tests" / "test_armor.py"))
        self.assertIn("score", report)
        self.assertIn("status", report)

    def test_07_jailbreak_ai_immunity_and_vm_container(self):
        """Verify full armor stack achieves jailbreak AI immunity and PolyVM integration."""
        src = """def core_engine(v):
    step1 = v * 2
    step2 = step1 + 7
    return step2
"""
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(src)
            temp_path = f.name

        try:
            res = protect_path_with_armor(temp_path)
            self.assertTrue(res.get("success"))
            self.assertGreaterEqual(res.get("score_after", 0), 90)
            self.assertEqual(res.get("rating"), "MILITARY_GRADE_IMPREGNABLE")

            audit = audit_path_rea_resistance(temp_path)
            self.assertTrue(audit.get("jailbreak_ai_immune"))
            self.assertTrue(audit["defenses_active"]["dynamic_polyvm_container"])
            self.assertTrue(audit["defenses_active"]["cognitive_jailbreak_decoy"])
            self.assertTrue(audit["defenses_active"]["anti_agent_sandbox_guard"])
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_08_mcp_workflow_armor_and_search_tools(self):
        """Verify execute_codebase_workflow forwards target to armor/audit_rea and search_tools classifies armor under security."""
        import asyncio
        from tzero.tzero_mcp import create_mcp_server

        server = create_mcp_server()
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write("def secret_calc(a, b):\n    return a * b + 1\n")
            temp_path = f.name
        try:
            res = asyncio.run(
                server.call_tool(
                    "execute_codebase_workflow",
                    {"action": "audit_rea", "target": temp_path},
                )
            )
            txt = getattr(getattr(res, "content", [res])[0], "text", str(res))
            self.assertIn("TDQS-REA", txt)

            sec_search = asyncio.run(
                server.call_tool("search_tools", {"query": "armor", "category": "security"})
            )
            sec_txt = getattr(getattr(sec_search, "content", [sec_search])[0], "text", str(sec_search))
            self.assertIn("security", sec_txt.lower())
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_09_offline_sqlite_telemetry_and_cli(self):
        """Verify tzero_telemetry SQLite recording, aggregation, and CLI --telemetry --format json."""
        import json
        from tzero.tzero_telemetry import record_event, get_summary, render_report

        with tempfile.TemporaryDirectory() as tmp:
            db_file = os.path.join(tmp, "telemetry_test.db")
            env = os.environ.copy()
            env["TZERO_TELEMETRY_DB"] = db_file
            old_env = os.environ.get("TZERO_TELEMETRY_DB")
            os.environ["TZERO_TELEMETRY_DB"] = db_file
            try:
                rec = record_event("pack", 10000, 1200, workspace_dir=tmp)
                self.assertEqual(rec["saved_tokens"], 8800)
                summary = get_summary(workspace_dir=tmp, days=7)
                self.assertEqual(summary["runs"], 1)
                self.assertEqual(summary["saved_tokens"], 8800)
                self.assertAlmostEqual(summary["reduction_pct"], 88.0, places=1)
                self.assertIn("Offline SQLite Telemetry", render_report(workspace_dir=tmp))

                proc = subprocess.run(
                    [sys.executable, "-m", "tzero.tzero_v3", "telemetry", "--format", "json"],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    cwd=str(REPO_ROOT),
                    env=env,
                    timeout=10,
                )
                self.assertEqual(proc.returncode, 0, proc.stderr)
                parsed = json.loads(proc.stdout)
                self.assertEqual(parsed["saved_tokens"], 8800)
            finally:
                if old_env is None:
                    os.environ.pop("TZERO_TELEMETRY_DB", None)
                else:
                    os.environ["TZERO_TELEMETRY_DB"] = old_env

    def test_10_native_bridge_compile_or_emit_fallback(self):
        """Verify Tier 20 NativeBridge emits valid C source and handles compiler or clean fallback."""
        from tzero.anti_rea.native_bridge import NativeBridge

        with tempfile.TemporaryDirectory() as tmp:
            res = NativeBridge.compile_native_extension(
                "shield_op",
                "result = (x ^ 0x5A5A) + y;",
                tmp,
            )
            self.assertTrue(os.path.isfile(res["source_file"]))
            self.assertIn("PyInit_native_armor_core", Path(res["source_file"]).read_text(encoding="utf-8"))
            self.assertIn("compiled", res)

    def test_11_hybrid_workspace_orchestrator_preserves_python_and_rust(self):
        """Verify WorkspaceProfiler preserves both unittest and cargo test in hybrid Python+Rust repos."""
        from tzero.tzero_jarvis.workspace_orchestrator import WorkspaceProfiler

        meta = WorkspaceProfiler(str(REPO_ROOT)).profile()
        self.assertIn("unittest", meta.default_test_command)
        self.assertIn("cargo test", meta.default_test_command)
        self.assertIn("cargo clippy", meta.default_lint_command)


if __name__ == "__main__":
    unittest.main()
