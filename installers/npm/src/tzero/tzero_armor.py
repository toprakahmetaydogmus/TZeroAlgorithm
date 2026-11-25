# -*- coding: utf-8 -*-
"""Siber Akademi T-Zero — Anti-REA Defense & Armor Engine.

Military-grade defense engine protecting codebases and executables
against AI-driven automated reverse engineering (e.g. morluto/rea,
Ghidra MCP bridge, IDA Pro LLM plugins, pyinstxtractor) and uncensored/jailbroken LLMs.
Includes native Ring-3 anti-debugging against x64dbg, IDA Pro, WinDbg, and Cheat Engine,
stealth canary beacon telemetry, in-flight string vault, and Electron asar shielding.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
Part of Siber Akademi T-Zero Context Architect v12.2.1 Master Edition.
License: MIT
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Attempt import from tzero.anti_rea, packages/anti_rea, or standalone anti_rea
PACKAGE_ROOT = Path(__file__).resolve().parent.parent / "packages" / "anti_rea"
if str(PACKAGE_ROOT) not in sys.path and PACKAGE_ROOT.is_dir():
    sys.path.insert(0, str(PACKAGE_ROOT))

try:
    from tzero.anti_rea.engine import AntiREAEngine
    from tzero.anti_rea.auditor import AIResistanceAuditor
    from tzero.anti_rea.extractor_shield import ExtractorShield
    from tzero.anti_rea.traps import AdversarialTrapGenerator
    from tzero.anti_rea.flattener import ControlFlowFlattener
    from tzero.anti_rea.token_bomb import TokenBombGenerator
    from tzero.anti_rea.confusables import HomoglyphDesynchronizer
    from tzero.anti_rea.honeypot import HoneypotGenerator
    from tzero.anti_rea.mcp_poison import MCPProtocolPoisoner
    from tzero.anti_rea.sybil_network import SybilNetworkGenerator
    from tzero.anti_rea.timing_guard import TimingGuard
    from tzero.anti_rea.vm_obfuscator import DynamicVMObfuscator
    from tzero.anti_rea.bytecode_trap import BytecodeTrap
    from tzero.anti_rea.jailbreak_decoy import CognitiveJailbreakDecoy
    from tzero.anti_rea.anti_agent_guard import AntiAgentGuard
    from tzero.anti_rea.algebraic_mutator import AlgebraicMutator
    from tzero.anti_rea.integrity_guard import MemoryIntegrityGuard
    from tzero.anti_rea.bpe_disrupter import BPETokenDisrupter
    from tzero.anti_rea.native_bridge import NativeBridge
    from tzero.anti_rea.anti_debugger import AntiDebugger
    from tzero.anti_rea.canary_beacon import CanaryBeacon
    from tzero.anti_rea.string_vault import StringVault
    from tzero.anti_rea.asar_shield import AsarShield
    from tzero.anti_rea.anti_vm import AntiVMGuard
    from tzero.anti_rea.rdtsc_guard import RDTSCTimingGuard
except ImportError:
    try:
        from anti_rea.engine import AntiREAEngine
        from anti_rea.auditor import AIResistanceAuditor
        from anti_rea.extractor_shield import ExtractorShield
        from anti_rea.traps import AdversarialTrapGenerator
        from anti_rea.flattener import ControlFlowFlattener
        from anti_rea.token_bomb import TokenBombGenerator
        from anti_rea.confusables import HomoglyphDesynchronizer
        from anti_rea.honeypot import HoneypotGenerator
        from anti_rea.mcp_poison import MCPProtocolPoisoner
        from anti_rea.sybil_network import SybilNetworkGenerator
        from anti_rea.timing_guard import TimingGuard
        from anti_rea.vm_obfuscator import DynamicVMObfuscator
        from anti_rea.bytecode_trap import BytecodeTrap
        from anti_rea.jailbreak_decoy import CognitiveJailbreakDecoy
        from anti_rea.anti_agent_guard import AntiAgentGuard
        from anti_rea.algebraic_mutator import AlgebraicMutator
        from anti_rea.integrity_guard import MemoryIntegrityGuard
        from anti_rea.bpe_disrupter import BPETokenDisrupter
        from anti_rea.native_bridge import NativeBridge
        from anti_rea.anti_debugger import AntiDebugger
        from anti_rea.canary_beacon import CanaryBeacon
        from anti_rea.string_vault import StringVault
        from anti_rea.asar_shield import AsarShield
        from anti_rea.anti_vm import AntiVMGuard
        from anti_rea.rdtsc_guard import RDTSCTimingGuard
    except ImportError:
        sys.path.append(str(Path(__file__).resolve().parent))
        from anti_rea.engine import AntiREAEngine
        from anti_rea.auditor import AIResistanceAuditor
        from anti_rea.extractor_shield import ExtractorShield
        from anti_rea.anti_vm import AntiVMGuard
        from anti_rea.rdtsc_guard import RDTSCTimingGuard


def protect_path_with_armor(
    path: str,
    output_path: Optional[str] = None,
    seed: int = 42,
    **options: Any
) -> Dict[str, Any]:
    """Protects target Python file, directory, or archive with Anti-REA military armor."""
    p = Path(path)
    if not p.exists():
        return {"success": False, "error": f"Path not found: {path}"}

    if p.is_file():
        return AntiREAEngine.protect_file(str(p), output_path=output_path, seed=seed, **options)

    # If directory, protect all .py files within
    results = []
    count = 0
    for py_file in p.rglob("*.py"):
        if "__pycache__" in str(py_file) or ".venv" in str(py_file):
            continue
        res = AntiREAEngine.protect_file(str(py_file), seed=seed, **options)
        if res.get("success"):
            count += 1
            results.append(res)

    return {
        "success": count > 0,
        "directory": str(p),
        "files_protected": count,
        "details": results
    }


def audit_path_rea_resistance(path: str) -> Dict[str, Any]:
    """Audits target file or codebase for resistance against AI reverse-engineering agents."""
    p = Path(path)
    if not p.exists():
        return {"success": False, "error": f"Path not found: {path}", "score": 0}

    if p.is_file():
        return AIResistanceAuditor.audit_file(str(p))

    # If directory, compute average resistance score across python files
    scores = []
    findings = []
    py_files = list(p.rglob("*.py"))
    for py_file in py_files:
        if "__pycache__" in str(py_file) or ".venv" in str(py_file):
            continue
        audit = AIResistanceAuditor.audit_file(str(py_file))
        if "score" in audit:
            scores.append(audit["score"])
        if audit.get("findings"):
            findings.extend(audit["findings"])

    avg_score = round(sum(scores) / max(1, len(scores)), 1)
    rating = (
        "MILITARY_GRADE_IMPREGNABLE" if avg_score >= 90 else
        "MILITARY_GRADE" if avg_score >= 80 else
        "STRONG" if avg_score >= 60 else
        "MODERATE" if avg_score >= 40 else
        "VULNERABLE"
    )

    return {
        "success": True,
        "directory": str(p),
        "files_scanned": len(scores),
        "score": avg_score,
        "max_score": 100,
        "rating": rating,
        "status": "PASS" if avg_score >= 60 else "RECOMMEND_HARDENING",
        "sample_findings": list(set(findings))[:5]
    }


def shield_executable(binary_path: str, output_path: Optional[str] = None) -> Dict[str, Any]:
    """Shields a compiled PyInstaller executable against pyinstxtractor archive parsing."""
    return ExtractorShield.shield_file(binary_path, output_path=output_path)
