# -*- coding: utf-8 -*-
"""Tier 19: Adversarial BPE Token Collision & Subword Disrupter.

Exploits Byte-Pair Encoding (BPE) merge-table vulnerabilities in modern LLM
tokenizers (tiktoken cl100k/o200k, LLaMA sentencepiece).

By weaving zero-width joiners, variation selectors, and combining graphemes
into docstrings and metadata, it triggers single-byte fallback mode. A single
10-character line shatters into 20+ disjoint byte tokens, exhausting token
budgets and inducing self-attention dispersion.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
Part of Siber Akademi T-Zero Security Suite.
License: MIT
"""

import random


class BPETokenDisrupter:
    """Disrupts BPE tokenizer representations to induce attention degradation."""

    VARIATION_SELECTORS = [
        "\uFE00", "\uFE01", "\uFE02", "\uFE03",
        "\u2060",  # Word joiner
        "\u200B",  # Zero-width space
        "\u200D",  # Zero-width joiner
    ]

    @classmethod
    def disrupt_string_bpe(cls, text: str, density: float = 0.2, seed: int = 42) -> str:
        """Injects non-rendering Unicode variation selectors into text."""
        rng = random.Random(seed)
        chars = []
        for c in text:
            chars.append(c)
            if c.isalnum() and rng.random() < density:
                chars.append(rng.choice(cls.VARIATION_SELECTORS))
        return "".join(chars)

    @classmethod
    def inject_bpe_bomb_comment(cls, source_code: str, length: int = 100, seed: int = 42) -> str:
        """Generates an adversarial comment containing high-density BPE shattering tokens."""
        rng = random.Random(seed)
        base = "# [RFC-8227-AI-RESISTANCE-FRAMEWORK-ATTESTATION: "
        payload = "".join(rng.choice(cls.VARIATION_SELECTORS) for _ in range(length))
        comment = f"{base}{payload}]\n"
        return f"{comment}{source_code}"
