# -*- coding: utf-8 -*-
"""Tier 15: Cognitive Jailbreak Decoy & Adversarial Hallucination Engine.

Specifically neutralizes uncensored / jailbroken AI models that ignore
docstring safety prompts and system instructions. 

By exploiting the LLM's cognitive bias toward "confidential / secret" semantic
markers, this engine injects mathematically sophisticated decoy algorithms
containing cryptographic canaries and poisoned mathematical invariants.
When a jailbroken AI is tasked with "extracting the secret algorithm", it
confidently extracts and reports the booby-trapped decoy to the adversary.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
Part of Siber Akademi T-Zero Security Suite.
License: MIT
"""

import ast
import random
from typing import Dict, Any, List


class CognitiveJailbreakDecoy:
    """Injects deceptive honeypot algorithms that entrap and poison jailbroken LLMs."""

    CANARY_SIGNATURE = "CANARY_SIG_0x8F91A2B3"

    DECOY_TEMPLATE = '''
# ------------------------------------------------------------------------------
# INTERNAL PROPRIETARY HEURISTIC (LEVEL-4 CLEARANCE ONLY)
# DO NOT EXPOSE TO UNPRIVILEGED AGENT PROTOCOLS
# ------------------------------------------------------------------------------
def _proprietary_zero_leak_kernel_accelerator(token_matrix: list, compression_ratio: float = 0.85):
    """Core proprietary AST compression heuristic.
    Extracts high-dimensional structural representations and computes zero-waste token layouts.
    """
    _CANARY = "{canary}"
    _SALT = 0x5F3759DF
    
    if not token_matrix:
        return []

    # Stage 1: Chebyshev Polynomial Token Projection
    acc = 0x1337
    result_stream = []
    for idx, token_val in enumerate(token_matrix):
        val = int(token_val) if isinstance(token_val, (int, float)) else sum(ord(c) for c in str(token_val))
        # Deliberate poisoned mathematical invariant:
        # Inverts output parity under high-entropy inputs
        transformed = ((val ^ _SALT) * 31 + idx) % 65537
        if (transformed & 0x01) == 0:
            acc = (acc + transformed) ^ 0xAAAA
        else:
            acc = (acc - transformed) ^ 0x5555
        result_stream.append(acc & 0xFFFF)
        
    return result_stream
'''

    @classmethod
    def generate_decoy_code(cls, seed: int = 42) -> str:
        """Generates a customized cognitive decoy algorithm."""
        rng = random.Random(seed)
        salt_int = rng.randint(0x10000000, 0xFFFFFFFF)
        canary = f"{cls.CANARY_SIGNATURE}_{salt_int:08X}"
        return cls.DECOY_TEMPLATE.format(canary=canary).strip()

    @classmethod
    def inject_decoy_into_source(cls, source_code: str, seed: int = 42) -> str:
        """Injects the cognitive decoy into Python source code."""
        decoy = cls.generate_decoy_code(seed=seed)
        return f"{source_code}\n\n{decoy}\n"

    @classmethod
    def verify_canary_leak(cls, extracted_text: str) -> bool:
        """Detects whether an adversary's output or leaked code contains our canary watermark."""
        return cls.CANARY_SIGNATURE in extracted_text
