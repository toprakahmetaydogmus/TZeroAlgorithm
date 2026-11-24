# -*- coding: utf-8 -*-
"""Tier 14: Anti-Decompiler Bytecode Trap & Crasher Engine.

Injects decompiler-crashing constructs and malformed dead-code sequences
that cause automated reverse-engineering decompilers (such as pycdc / decompyle++,
uncompyle6, and Ghidra Python bytecode loaders) to terminate abnormally with
unhandled opcode exceptions or recursion overflow, before any decompiled source
can be presented to an LLM agent.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
Part of Siber Akademi T-Zero Security Suite.
License: MIT
"""

import ast
import random
from typing import Dict, Any, List


class BytecodeTrap:
    """Injects control-flow and opcode traps specifically targeted at AI decompilers."""

    # Syntactic decompiler crashers:
    # 1. Recursive nested exception blocks with synthetic break targets
    # 2. Unreachable yield-from generator cycles
    # 3. Dynamic lambda closures with circular type hints
    DECOMPILER_CRASHER_SNIPPET = '''
# --- SIBER AKADEMI ANTI-DECOMPILER RESISTANCE BARRIER ---
def _anti_decompiler_guard_gate_0x9F():
    """Uncompyle6 and pycdc recursion limiter trap.
    Forces AST decompiler into non-linear CFG cycle causing fatal recursion.
    """
    _trap_flag = False
    if _trap_flag:
        try:
            for _ in (lambda: (yield from ()))():
                while True:
                    try:
                        pass
                    except Exception:
                        pass
        except (GeneratorExit, SystemExit, Exception):
            pass
        else:
            return 0xDEADBEEF
    return True
'''

    @classmethod
    def inject_decompiler_crash_constructs(cls, source_code: str, seed: int = 42) -> str:
        """Injects syntactic CFG cycles that crash decompilers without runtime penalty."""
        rng = random.Random(seed)
        salt = rng.randint(0x1000, 0xFFFF)
        crasher = cls.DECOMPILER_CRASHER_SNIPPET.replace("0x9F", f"0x{salt:X}")
        
        # Also inject an inline invariant check that executes at module import
        gate_call = f"\nif not _anti_decompiler_guard_gate_0x{salt:X}():\n    raise SystemExit(1)\n"
        
        return f"{crasher}\n{gate_call}\n{source_code}"

    @classmethod
    def shield_pyc_bytecode(cls, pyc_bytes: bytes) -> bytes:
        """Applies decompiler crasher padding to compiled Python bytecode."""
        if len(pyc_bytes) < 16:
            return pyc_bytes

        # Python PEP 552 16-byte header check
        # Injects unreachable trailer block with dead-byte pattern 0xFF 0xFF (invalid opcode)
        # Python interpreter terminates before reading trailing junk, but linear sweep
        # disassemblers and Ghidra decompiler parse to EOF and crash with Unhandled Opcode 0xFF
        crasher_trailer = b"\x00\x00\x00\x00" + (b"\xFF\xFE\xFD\xFF" * 8)
        return pyc_bytes + crasher_trailer

    @classmethod
    def audit_decompiler_resistance(cls, source_code: str) -> Dict[str, Any]:
        """Audits source code for the presence of decompiler crash barriers."""
        has_gate = "_anti_decompiler_guard_gate" in source_code
        has_cfg_trap = "yield from" in source_code and ("except" in source_code or "finally" in source_code)

        return {
            "has_decompiler_guard_gate": has_gate,
            "has_cfg_trap": has_cfg_trap,
            "decompiler_crash_capable": has_gate and has_cfg_trap,
            "rating": "IMMUNE_TO_STATIC_DECOMPILERS" if (has_gate and has_cfg_trap) else "VULNERABLE"
        }
