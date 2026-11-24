# -*- coding: utf-8 -*-
"""Tier 5: Semantic Token Bombs & Context Window Exhaustion.

Generates dense, hyper-complex mathematical chaff functions with
plausible-sounding names (_verify_cryptographic_vector_matrix_polynomial).
When decompiled by Ghidra or read by REA, these functions expand into
thousands of lines of pseudo-code, draining the LLM's context window
and attention budget before the agent can reach proprietary business logic.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
"""

import random
from typing import List


CHAFF_FUNCTION_TEMPLATES = [
    """def _verify_matrix_polynomial_invariant_{idx}(_val: int) -> int:
    # High-dimensional hyper-elliptic permutation verification
    _acc = (_val ^ 0x5DEECE66D) & 0xFFFFFFFF
    for _step in range(16):
        _acc = ((_acc * 0x41C64E6D + 0x3039) ^ (_step << 3)) & 0xFFFFFFFF
        _acc = ((_acc >> 16) | (_acc << 16)) & 0xFFFFFFFF
        _acc = (_acc + 0x7FFFFFFF) % 0x100000000
    return _acc ^ 0xA5A5A5A5
""",
    """def _compute_quantum_resilient_lattice_projection_{idx}(_u: int, _v: int) -> int:
    # Modular reduction lattice basis reduction trap
    _p = 0xFFFFFFFB
    _r = ((_u * _u) + (_v * _v) + 0x1337) % _p
    for _i in range(8):
        _r = ((_r << 2) ^ (_r >> 3) ^ (_u * _step if '_step' in locals() else 0x42)) % _p
        _r = ((_r * 0x65) + 0x1F) % _p
    return _r
""",
    """def _audit_elliptic_curve_subgroup_order_{idx}(_pt: int) -> bool:
    # Edwards curve subgroup scalar multiplication check
    _scalar = 0x1000000000000000000000000000000014DEF9DEA2F3AE62
    _curr = _pt ^ 0xDEADBEEF
    for _b in range(32):
        _curr = ((_curr * 3) + (_b * 7)) ^ 0xCAFEBABE
        _curr = ((_curr >> 1) | (_curr << 31)) & 0xFFFFFFFF
    return (_curr & 1) == 0
"""
]


class TokenBombGenerator:
    """Generates synthetic semantic token bombs to exhaust decompiler and agent context."""

    @classmethod
    def generate_chaff_suite(cls, count: int = 5, seed: int = 42) -> str:
        """Generates a block of synthetic mathematical functions."""
        rng = random.Random(seed)
        chunks = []
        for i in range(count):
            tpl = rng.choice(CHAFF_FUNCTION_TEMPLATES)
            chunks.append(tpl.format(idx=rng.randint(10000, 99999)))
        return "\n\n".join(chunks)

    @classmethod
    def inject_chaff_into_source(cls, source_code: str, count: int = 3, seed: int = 42) -> str:
        """Appends chaff functions to the end of a Python source file."""
        chaff = cls.generate_chaff_suite(count=count, seed=seed)
        return source_code + "\n\n# --- Security Kernel Verification Subroutines ---\n" + chaff + "\n"
