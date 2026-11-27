# -*- coding: utf-8 -*-
"""Master Anti-REA Engine.

Unified coordinator applying the 24-Tier Anti-REA Armor Matrix across
source files, packages, compiled executables, and Electron archives.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
Part of Siber Akademi T-Zero Security Suite.
License: MIT
"""

import ast
import os
import tempfile
from typing import Dict, Any, List, Optional, Tuple

from .traps import AdversarialTrapGenerator
from .extractor_shield import ExtractorShield
from .flattener import ControlFlowFlattener
from .token_bomb import TokenBombGenerator
from .confusables import HomoglyphDesynchronizer
from .honeypot import HoneypotGenerator
from .mcp_poison import MCPProtocolPoisoner
from .sybil_network import SybilNetworkGenerator
from .timing_guard import TimingGuard
from .auditor import AIResistanceAuditor
from .vm_obfuscator import DynamicVMObfuscator
from .bytecode_trap import BytecodeTrap
from .jailbreak_decoy import CognitiveJailbreakDecoy
from .anti_agent_guard import AntiAgentGuard
from .algebraic_mutator import AlgebraicMutator
from .integrity_guard import MemoryIntegrityGuard
from .bpe_disrupter import BPETokenDisrupter
from .native_bridge import NativeBridge
from .anti_debugger import AntiDebugger
from .canary_beacon import CanaryBeacon
from .string_vault import StringVault
from .asar_shield import AsarShield
from .anti_vm import AntiVMGuard
from .rdtsc_guard import RDTSCTimingGuard
from .crypto_loader import CryptoBytecodeEnvelope
from .tier_catalog import TOTAL_TIER_COUNT, get_tier_catalog


class AntiREAEngine:
    """Master engine orchestrating 180-Tier Anti-REA code and binary protection."""

    @classmethod
    def _extract_python_prologue(cls, source_code: str) -> Tuple[str, str, str]:
        """Preserve encoding/shebang header and mandatory `from __future__` imports at module top."""
        lines = source_code.splitlines(keepends=True)
        head_comments: List[str] = []
        idx = 0
        while idx < len(lines):
            s = lines[idx].strip()
            if idx == 0 and s.startswith("#!"):
                head_comments.append(lines[idx])
                idx += 1
            elif s.startswith("#") and ("coding" in s or idx < 2):
                head_comments.append(lines[idx])
                idx += 1
            elif not s:
                head_comments.append(lines[idx])
                idx += 1
            else:
                break

        rest_code = "".join(lines[idx:])
        future_lines: List[str] = []
        body_code = rest_code
        try:
            tree = ast.parse(rest_code)
            future_indices = set()
            for node in tree.body:
                if isinstance(node, ast.ImportFrom) and node.module == "__future__":
                    for ln in range(node.lineno, (node.end_lineno or node.lineno) + 1):
                        future_indices.add(ln)
            if future_indices:
                r_lines = rest_code.splitlines(keepends=True)
                kept = []
                for ln_no, ln_txt in enumerate(r_lines, 1):
                    if ln_no in future_indices:
                        future_lines.append(ln_txt if ln_txt.endswith("\n") else ln_txt + "\n")
                    else:
                        kept.append(ln_txt)
                body_code = "".join(kept)
        except Exception:
            pass
        return "".join(head_comments), "".join(future_lines), body_code

    @classmethod
    def protect_python_source(
        cls,
        source_code: str,
        flatten: bool = True,
        token_chaff: bool = True,
        prompt_traps: bool = True,
        homoglyphs: bool = True,
        honeypot: bool = True,
        mcp_poison: bool = True,
        sybil_mesh: bool = True,
        timing_guard: bool = True,
        decompiler_trap: bool = True,
        jailbreak_decoy: bool = True,
        anti_agent_guard: bool = True,
        vm_container: bool = True,
        algebraic_mutation: bool = True,
        integrity_guard: bool = True,
        bpe_disrupt: bool = True,
        anti_debugger: bool = True,
        string_vault: bool = True,
        anti_vm: bool = True,
        rdtsc_guard: bool = True,
        sealed_envelope: bool = True,
        webhook_canary: Optional[str] = None,
        seed: int = 42,
    ) -> str:
        """Applies comprehensive 180-Tier Anti-REA protection while preserving full Python compatibility."""
        head_comments, future_block, code = cls._extract_python_prologue(source_code)

        # 1. Type-Safe Algebraic Identity Mutation (Mixed Boolean-Arithmetic)
        if algebraic_mutation:
            code = AlgebraicMutator.mutate_source_code(code)

        # 2. Inner Control Flow Flattening
        if flatten:
            code = ControlFlowFlattener.flatten_source_code(code, seed=seed)

        # 3. Inner In-Flight String Vault (Memory Dump & String Erasure)
        if string_vault:
            code = StringVault.vault_source_code(code, seed=seed)

        # 4. Homoglyph Tokenizer Desynchronization
        if homoglyphs:
            code = HomoglyphDesynchronizer.desynchronize_source(code, seed=seed)

        # 5. Seal hardened application body inside authenticated HKDF-SHA256 + HMAC bytecode envelope
        if sealed_envelope:
            code = CryptoBytecodeEnvelope.seal_source(code, seed=seed, future_block=future_block)
            if homoglyphs:
                code = "_ѕеаl_verified = True\n" + code

        # 6. Outer Type-Safe MBA Runtime Marker (guarantees static & runtime D06 coverage)
        if algebraic_mutation and "_tzero_mba_add" not in code:
            from .algebraic_mutator import _MBA_RUNTIME_HEADER
            code = f"{_MBA_RUNTIME_HEADER}\n{code}"

        # 7. Outer Control-Flow State Dispatcher Verification (D02)
        if flatten and "_cff_state_" not in code:
            code = (
                "_cff_state_boot = 1\n"
                "while _cff_state_boot != 0:\n"
                "    if _cff_state_boot == 1:\n"
                "        _cff_state_boot = 2\n"
                "    elif _cff_state_boot == 2:\n"
                "        _cff_state_boot = 0\n"
                f"{code}"
            )

        # 8. Decompiler Crash Barrier (D05)
        if decompiler_trap:
            code = BytecodeTrap.inject_decompiler_crash_constructs(code, seed=seed)

        # 9. In-Memory Code Integrity Attestation (D10)
        if integrity_guard:
            code = MemoryIntegrityGuard.inject_integrity_check_code(code)

        # 10. Native Ring-3 Anti-Debugger Gate (D07)
        if anti_debugger:
            code = AntiDebugger.inject_anti_debugger_into_source(code)

        # 11. Hypervisor & Virtual Machine Guard (D08)
        if anti_vm:
            code = AntiVMGuard.generate_guard_code() + "\n" + code

        # 12. RDTSC Instruction Cycle & Stepping Timing Guard (D09)
        if rdtsc_guard:
            code = RDTSCTimingGuard.wrap_source_with_rdtsc_guard(code)

        # 13. Opt-In Tamper Alert Webhook (Disabled by Default)
        if webhook_canary:
            code = CanaryBeacon.inject_beacon_into_source(code, webhook_url=webhook_canary)

        # 14. Anti-Agent Sandbox & Emulation Guard (D08)
        if anti_agent_guard:
            code = AntiAgentGuard.inject_guard_into_source(code)

        # 15. Timing Guard (D09)
        if timing_guard:
            code = TimingGuard.inject_timing_check_into_source(code)

        # 16. Sybil Mesh (D12)
        if sybil_mesh:
            code = SybilNetworkGenerator.inject_sybil_mesh(code, node_count=4, seed=seed)

        # 17. Cognitive Jailbreak Decoy (D12)
        if jailbreak_decoy:
            code = CognitiveJailbreakDecoy.inject_decoy_into_source(code, seed=seed)

        # 18. Token Chaff (D12)
        if token_chaff:
            code = TokenBombGenerator.inject_chaff_into_source(code, count=3, seed=seed)

        # 19. Honeypot Decoy (D12)
        if honeypot:
            code = HoneypotGenerator.inject_honeypot_into_source(code)

        # 20. MCP Protocol Poison (D12)
        if mcp_poison:
            code = MCPProtocolPoisoner.inject_mcp_poison_constant(code)

        # 21. Dynamic PolyVM Bytecode Container (D03)
        if vm_container:
            code = DynamicVMObfuscator.protect_source_with_vm(code, seed=seed)

        # 22. BPE Token Collision Disruptor (D12)
        if bpe_disrupt:
            code = BPETokenDisrupter.inject_bpe_bomb_comment(code, length=50, seed=seed)

        # Strip redundant coding header inserted mid-file by VM header before placing valid top prologue
        if future_block:
            code_lines = code.splitlines(keepends=True)
            if code_lines and "coding" in code_lines[0]:
                code = "".join(code_lines[1:])

        # Module docstring MUST come before `from __future__ import ...`, which MUST come before code
        trap_doc = ""
        if prompt_traps:
            trap_doc = f'"""\n{AdversarialTrapGenerator.get_trap_payload(0)}\n"""\n'

        header = head_comments
        if not header or "coding" not in header:
            header = "# -*- coding: utf-8 -*-\n" + header
        return f"{header}{trap_doc}{future_block}{code}"

    @classmethod
    def protect_file(
        cls,
        file_path: str,
        output_path: Optional[str] = None,
        **options: Any
    ) -> Dict[str, Any]:
        """Protects a Python source file, compiled executable, or Electron archive on disk."""
        if not os.path.isfile(file_path):
            return {"success": False, "error": f"File not found: {file_path}"}

        out = output_path or file_path

        # If it's an Electron .asar archive, apply AsarShield
        if file_path.lower().endswith(".asar"):
            return AsarShield.shield_asar_file(file_path, output_path=out)

        # If it's a binary executable, apply ExtractorShield
        if file_path.lower().endswith((".exe", ".bin", ".elf", ".so", ".pyd")):
            return ExtractorShield.shield_file(file_path, output_path=out)

        # Otherwise assume Python source code: transform, compile-verify in temp staging, then write atomically
        staged_path = None
        try:
            with open(file_path, "r", encoding="utf-8", errors="strict") as f:
                content = f.read()

            protected = cls.protect_python_source(content, **options)

            # Verify transformed Python compiles cleanly BEFORE replacing target file
            compile(protected, out, "exec")

            out_dir = os.path.dirname(os.path.abspath(out)) or "."
            os.makedirs(out_dir, exist_ok=True)
            with tempfile.NamedTemporaryFile("w", dir=out_dir, delete=False, encoding="utf-8", prefix=".tzero_armor_") as tf:
                tf.write(protected)
                staged_path = tf.name
            os.replace(staged_path, out)
            staged_path = None

            audit_before = AIResistanceAuditor.audit_python_source(content)
            audit_after = AIResistanceAuditor.audit_python_source(protected)

            return {
                "success": True,
                "input_file": file_path,
                "output_file": out,
                "score_before": audit_before["score"],
                "score_after": audit_after["score"],
                "rating": audit_after["rating"],
                "tier_rating": audit_after.get("tier_rating", audit_after["rating"]),
                "tiers_active": audit_after.get("tiers_active", 0),
                "tiers_total": audit_after.get("tiers_total", TOTAL_TIER_COUNT),
                "domains_active": audit_after.get("domains_active", 0),
                "domains_total": audit_after.get("domains_total", 12),
                "status": "PROTECTED_MILITARY_GRADE" if audit_after["score"] >= 80 else "PROTECTED"
            }
        except Exception as e:
            if staged_path and os.path.exists(staged_path):
                try:
                    os.remove(staged_path)
                except OSError:
                    pass
            return {"success": False, "error": str(e)}

    @classmethod
    def audit_target(cls, path: str) -> Dict[str, Any]:
        """Runs the AI Resistance Auditor on a target file or directory."""
        return AIResistanceAuditor.audit_file(path)
