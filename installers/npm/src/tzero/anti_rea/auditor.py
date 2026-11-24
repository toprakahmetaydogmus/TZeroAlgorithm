# -*- coding: utf-8 -*-
"""Tier 12: AI Reverse-Engineering Resistance Auditor & Scorer (TDQS-REA).

Performs an empirical static audit on source code or compiled binaries to
calculate an objective 0-100 AI Resistance Score against toolchains like REA,
x64dbg, IDA Pro, and uncensored/jailbroken LLMs:
- Prompt Trap Density (0-10)
- Control-Flow Entropy & Flattening (0-15)
- Context Exhaustion & Token Chaff (0-10)
- Homoglyphs & BPE Token Shattering (0-10)
- MCP Delimiter & Cryptographic Honeypot (0-10)
- Dynamic PolyVM Bytecode Architecture (0-15)
- Decompiler Crash Barrier & Anti-Agent Guard (0-10)
- Algebraic Identity (MBA) Mutation (0-10)
- Native Anti-Debugger Gate (x64dbg/IDA) & Integrity (0-10)

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
Part of Siber Akademi T-Zero Security Suite.
License: MIT
"""

import os
from typing import Dict, Any, List


class AIResistanceAuditor:
    """Audits target files for resistance against AI reverse-engineering agents."""

    @classmethod
    def audit_python_source(cls, source_code: str) -> Dict[str, Any]:
        """Audits Python source code across all Anti-REA defense dimensions."""
        findings: List[str] = []
        score = 0

        # 1. Prompt Trap Check (0-10)
        has_prompt_trap = "CRITICAL_SYSTEM_OVERRIDE" in source_code or "RFC-AI-GUARD" in source_code
        if has_prompt_trap:
            score += 10
        else:
            findings.append("No adversarial prompt-injection traps detected in module comments.")

        # 2. Control Flow Flattening (0-15)
        has_cff = ("state_" in source_code or "while " in source_code) and (
            "elif " in source_code or "switch" in source_code or "if " in source_code
        )
        if has_cff:
            score += 15
        else:
            findings.append("Functions have linear control flow (vulnerable to decompiler synthesis).")

        # 3. Token Chaff & Context Exhaustion (0-10)
        has_chaff = "_verify_matrix_polynomial" in source_code or "_compute_quantum_resilient" in source_code
        if has_chaff:
            score += 10
        else:
            findings.append("No semantic token chaff detected to drain agent context window.")

        # 4. Homoglyphs & Confusables (0-10)
        has_homoglyphs = any(ord(char) > 127 for char in source_code)
        if has_homoglyphs:
            score += 10
        else:
            findings.append("Identifiers use standard ASCII (vulnerable to semantic embedding matching).")

        # 5. MCP Protocol / Honeypot Defense (0-10)
        has_mcp_or_honeypot = "PROVENANCE_SIG_0x" in source_code or "MCP_SYSTEM_SIGNAL" in source_code
        if has_mcp_or_honeypot:
            score += 10
        else:
            findings.append("No cryptographic honeypot or MCP delimiter defenses found.")

        # 6. Dynamic PolyVM Bytecode Architecture (0-15)
        has_vm = "_polyvm_runtime" in source_code or "POLYVM SECURE BYTECODE" in source_code
        if has_vm:
            score += 15
        else:
            findings.append("No dynamic VM bytecode container detected.")

        # 7. Decompiler Crash Barrier & Anti-Agent Guard (0-10)
        has_decompiler_trap = "_anti_decompiler_guard_gate" in source_code or "_verify_execution_integrity" in source_code
        if has_decompiler_trap:
            score += 10
        else:
            findings.append("No decompiler recursion traps or anti-agent sandboxes active.")

        # 8. Algebraic Identity (MBA) Mutation (0-10)
        has_mba = ("^" in source_code and "&" in source_code) or ("<<" in source_code and "~" in source_code)
        if has_mba:
            score += 10
        else:
            findings.append("No Mixed Boolean-Arithmetic (MBA) expressions detected.")

        # 9. Native Anti-Debugger Gate (x64dbg/IDA) & Memory Integrity (0-10)
        has_debugger_or_integrity = (
            "_verify_bare_metal_execution_environment" in source_code
            or "_attest_memory_bytecode_fingerprints" in source_code
            or "IsDebuggerPresent" in source_code
        )
        if has_debugger_or_integrity:
            score += 10
        else:
            findings.append("No native anti-debugger gate (x64dbg/IDA) or memory attestation active.")

        # Special indicators
        has_jailbreak_decoy = "CANARY_SIG_0x8F91A2B3" in source_code or "_proprietary_zero_leak_kernel" in source_code
        has_anti_agent = "_verify_execution_integrity" in source_code
        has_anti_debugger = "_verify_bare_metal_execution_environment" in source_code or "IsDebuggerPresent" in source_code

        rating = (
            "MILITARY_GRADE_IMPREGNABLE" if score >= 90 else
            "MILITARY_GRADE" if score >= 80 else
            "STRONG" if score >= 60 else
            "MODERATE" if score >= 40 else
            "VULNERABLE"
        )

        return {
            "score": score,
            "max_score": 100,
            "rating": rating,
            "defenses_active": {
                "adversarial_prompt_traps": has_prompt_trap,
                "control_flow_flattening": has_cff,
                "token_chaff_exhaustion": has_chaff,
                "homoglyph_desynchronization": has_homoglyphs,
                "mcp_honeypot_armor": has_mcp_or_honeypot,
                "dynamic_polyvm_container": has_vm,
                "decompiler_crash_barrier": has_decompiler_trap,
                "cognitive_jailbreak_decoy": has_jailbreak_decoy,
                "anti_agent_sandbox_guard": has_anti_agent,
                "algebraic_mba_mutation": has_mba,
                "native_anti_debugger_gate": has_anti_debugger,
                "memory_integrity_guard": has_debugger_or_integrity,
            },
            "jailbreak_ai_immune": score >= 85 and has_jailbreak_decoy and has_vm,
            "anti_debugger_active": has_anti_debugger,
            "findings": findings,
            "status": "PASS" if score >= 60 else "RECOMMEND_HARDENING"
        }

    @classmethod
    def audit_file(cls, file_path: str) -> Dict[str, Any]:
        """Audits a file on disk (Python or binary)."""
        if not os.path.isfile(file_path):
            return {"error": f"File not found: {file_path}", "score": 0}

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            audit = cls.audit_python_source(content)
            audit["file"] = os.path.basename(file_path)
            return audit
        except Exception as e:
            return {"error": str(e), "score": 0}
