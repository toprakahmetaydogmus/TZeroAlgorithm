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
from anti_rea.extractor_shield import PYINSTALLER_COOKIE, ExtractorShield
from anti_rea.flattener import ControlFlowFlattener
from anti_rea.traps import AdversarialTrapGenerator
from anti_rea.honeypot import HoneypotGenerator
from anti_rea.vm_obfuscator import DynamicVMObfuscator
from anti_rea.bytecode_trap import BytecodeTrap
from anti_rea.jailbreak_decoy import CognitiveJailbreakDecoy
from anti_rea.anti_agent_guard import AntiAgentGuard


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


if __name__ == "__main__":
    unittest.main()
