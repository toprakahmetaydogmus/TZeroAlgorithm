# -*- coding: utf-8 -*-
"""Acceptance Tests for Ultra 180-Tier Anti-REA v5.0.0 Protection Suite."""

import os
import re
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


class TestAntiREA180Tiers(unittest.TestCase):
    """Validates all 180 Tiers, real-world app preservation, PE scrubbing, and tamper immunity."""

    def test_01_catalog_has_exact_180_unique_tiers_across_12_domains(self):
        from tzero.anti_rea.tier_catalog import ANTI_REA_DOMAINS, ANTI_REA_TIERS, TOTAL_TIER_COUNT, get_tier_catalog

        self.assertEqual(len(ANTI_REA_DOMAINS), 12)
        self.assertEqual(TOTAL_TIER_COUNT, 180)
        self.assertEqual(len(ANTI_REA_TIERS), 180)
        ids = [t["id"] for t in ANTI_REA_TIERS]
        self.assertEqual(ids[0], "REA-001")
        self.assertEqual(ids[-1], "REA-180")
        self.assertEqual(len(set(ids)), 180)
        cat = get_tier_catalog()
        self.assertEqual(cat["total_tiers"], 180)
        self.assertEqual(cat["total_domains"], 12)

    def test_02_real_complex_python_application_runs_100pct_intact_under_180_tier_armor(self):
        """Real classes, async, generators, string +, float *, UTF-8, and CLI execution must remain intact."""
        from tzero.anti_rea.engine import AntiREAEngine
        from tzero.anti_rea.auditor import AIResistanceAuditor

        complex_app = '''# -*- coding: utf-8 -*-
"""Complex proprietary engine sample."""
from __future__ import annotations
import asyncio
import sys
from dataclasses import dataclass

@dataclass
class BaseResult:
    name: str
    score: int

class BaseEngine:
    def prefix(self) -> str:
        return "Türkçe-Başlık: "

class ProEngine(BaseEngine):
    @classmethod
    def compute(cls, x: int, factor: float) -> dict:
        inst = cls()
        label = inst.prefix() + "Aktif"
        scaled = factor * 2
        total = x + 15
        diff = total - 5
        arr = [1] * 2
        return {"label": label, "scaled": scaled, "diff": diff, "arr": arr, "ok": True + False}

def gen_nums(n: int):
    for i in range(n):
        yield i * 2

async def async_ping() -> str:
    await asyncio.sleep(0)
    return "ASYNC_OK"

if __name__ == "__main__":
    res = ProEngine.compute(10, 0.75)
    nums = list(gen_nums(3))
    ares = asyncio.run(async_ping())
    print(f"{res['label']}|{res['scaled']}|{res['diff']}|{nums}|{ares}|{sys.argv[1:]}")
'''
        with tempfile.TemporaryDirectory() as tmp:
            src_path = Path(tmp) / "complex_app.py"
            out_path = Path(tmp) / "complex_app_armored.py"
            src_path.write_text(complex_app, encoding="utf-8")

            res = AntiREAEngine.protect_file(str(src_path), output_path=str(out_path), seed=777)
            self.assertTrue(res["success"], res.get("error"))
            self.assertGreaterEqual(res["score_after"], 95)
            self.assertGreaterEqual(res["tiers_active"], 135)

            armored_text = out_path.read_text(encoding="utf-8")
            # Plaintext proprietary identifiers & secret strings must NOT leak unsealed
            self.assertNotIn("ProEngine", armored_text)
            self.assertNotIn("ASYNC_OK", armored_text)
            self.assertNotIn("Türkçe-Başlık", armored_text)
            self.assertIn("_tzero_decrypt_and_exec", armored_text)

            audit = AIResistanceAuditor.audit_file(str(out_path))
            self.assertEqual(audit["tier_rating"], "SOVEREIGN_180_ULTRA_ARMOR")

            # Execute protected file as an independent real Python CLI process!
            proc = subprocess.run(
                [sys.executable, str(out_path), "--arg1", "merhaba"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=15,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("Türkçe-Başlık: Aktif|1.5|20|[0, 2, 4]|ASYNC_OK|['--arg1', 'merhaba']", proc.stdout)

    def test_03_sealed_envelope_rejects_ciphertext_tampering(self):
        from tzero.anti_rea.crypto_loader import CryptoBytecodeEnvelope

        sealed = CryptoBytecodeEnvelope.seal_source("VALUE = 42\n", seed=123)
        ns = {}
        exec(sealed, ns)
        self.assertEqual(ns["VALUE"], 42)

        # Flip one hex character inside HMAC tag argument in `_tzero_decrypt_and_exec(..., '<hmac>', globals())`
        m = re.search(r"'([0-9a-f]{64})'", sealed)
        self.assertIsNotNone(m)
        orig_hmac = m.group(1)
        bad_hmac = ("0" if orig_hmac[0] != "0" else "1") + orig_hmac[1:]
        tampered = sealed.replace(orig_hmac, bad_hmac, 1)
        with self.assertRaises(RuntimeError):
            exec(tampered, {})

    def test_04_algebraic_mutator_does_not_break_strings_floats_or_lists(self):
        from tzero.anti_rea.algebraic_mutator import AlgebraicMutator

        src = """def mix(a, b, s, f, lst):
    return (a + b, a - b, s + "!", f * 2, lst * 2, 3 + 5, 10 - 3)
"""
        mutated = AlgebraicMutator.mutate_source_code(src)
        self.assertIn("_tzero_mba_add", mutated)
        ns = {}
        exec(mutated, ns)
        self.assertEqual(
            ns["mix"](11, 4, "merhaba", 1.25, [7]),
            (15, 7, "merhaba!", 2.5, [7, 7], 8, 7),
        )

    def test_05_pe_metadata_scrubbing_and_multi_cave_decoy(self):
        from tzero.anti_rea.extractor_shield import ExtractorShield, PYINSTALLER_COOKIE

        # Build minimal synthetic valid PE header (MZ + DanS/Rich + PE + .rdata + .rsrc + PyInstaller cookie)
        buf = bytearray(4096)
        buf[0:2] = b"MZ"
        e_lfanew = 0x100
        struct.pack_into("<I", buf, 0x3C, e_lfanew)
        buf[0x90:0x94] = b"DanS"
        buf[0xB0:0xB4] = b"Rich"
        buf[e_lfanew:e_lfanew + 4] = b"PE\x00\x00"
        struct.pack_into("<H", buf, e_lfanew + 6, 2)  # 2 sections
        struct.pack_into("<I", buf, e_lfanew + 8, 0x6789ABCD)  # TimeDateStamp
        struct.pack_into("<H", buf, e_lfanew + 20, 0xF0)  # OptionalHeader size
        sec_off = e_lfanew + 24 + 0xF0
        # Section 1: .rdata at file offset 0x400, rsize=0x400, vsize=0x100 (slack 0x300)
        buf[sec_off:sec_off + 6] = b".rdata"
        struct.pack_into("<IIII", buf, sec_off + 8, 0x100, 0x1000, 0x400, 0x400)
        # Section 2: .rsrc at file offset 0x800, rsize=0x400, vsize=0x100 (slack 0x300)
        buf[sec_off + 40:sec_off + 45] = b".rsrc"
        struct.pack_into("<IIII", buf, sec_off + 48, 0x100, 0x2000, 0x400, 0x800)
        # Fill non-zero padding just before real cookie at 0xF00 so pre-cookie scan misses it & uses PE slack caves
        buf[0xE00:0xF00] = b"\x55" * 0x100
        buf[0xF00:0xF00 + len(PYINSTALLER_COOKIE)] = PYINSTALLER_COOKIE

        shielded, meta = ExtractorShield.shield_binary_bytes(bytes(buf))
        self.assertTrue(meta["shielded"])
        self.assertEqual(meta["decoy_traps_injected"], 2)
        self.assertEqual(meta["pe_metadata_scrubbed"], 2)
        self.assertNotIn(b"Rich", shielded[:e_lfanew])
        self.assertEqual(struct.unpack_from("<I", shielded, e_lfanew + 8)[0], 0)
        self.assertGreaterEqual(len(ExtractorShield.scan_cookie(shielded)), 3)

    def test_06_asar_js_guard_and_native_antidebug_fast(self):
        import time
        from tzero.anti_rea.anti_debugger import AntiDebugger
        from tzero.anti_rea.asar_shield import AsarShield

        t0 = time.perf_counter()
        scan = AntiDebugger.scan_debugger_environment()
        self.assertLess(time.perf_counter() - t0, 1.5)
        self.assertIn("python_monitoring_active", scan)

        js_out = AsarShield.protect_js_source("console.log('app');")
        self.assertIn("Object.freeze(Object.prototype)", js_out)
        self.assertIn("--inspect", js_out)

    def test_07_cli_matrix_command_outputs_180_tiers(self):
        proc = subprocess.run(
            [sys.executable, "-m", "tzero.anti_rea.cli", "matrix"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=10,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("180 Tiers across 12 Domains", proc.stdout)
        self.assertIn("[D12]", proc.stdout)


if __name__ == "__main__":
    unittest.main()
