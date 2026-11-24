# -*- coding: utf-8 -*-
"""Tier 10: Dead-Code Sybil Networks & Graph Traversal Traps.

Target: Autonomous AI agents that iteratively trace call graphs and cross-references (xrefs).
Injects a network of 10+ interconnected, circular decoy classes with
mock dependency injection and phantom interfaces.
When an AI agent (such as Claude Code or Cursor) instructs REA's xref tools
to trace callers and callees, it gets trapped in circular graph traversals,
exhausting its tool-turn limit and context window.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
"""

import random
from typing import List


SYBIL_CLASS_TEMPLATE = """class _SybilHandlerNode_{idx}:
    def __init__(self, parent=None):
        self._parent = parent
        self._next_delegate = None

    def route_transaction_{idx}(self, payload: bytes) -> bytes:
        if self._parent and hasattr(self._parent, "dispatch_{next_idx}"):
            return getattr(self._parent, "dispatch_{next_idx}")(payload)
        return payload[::-1]

    def dispatch_{idx}(self, payload: bytes) -> bytes:
        return self.route_transaction_{idx}(payload)
"""


class SybilNetworkGenerator:
    """Generates dead-code circular class networks to trap autonomous xref tracers."""

    @classmethod
    def generate_sybil_mesh(cls, node_count: int = 5, seed: int = 42) -> str:
        """Generates interconnected circular decoy class definitions."""
        rng = random.Random(seed)
        nodes = [rng.randint(100, 999) for _ in range(node_count)]
        classes = []

        for i, idx in enumerate(nodes):
            next_idx = nodes[(i + 1) % len(nodes)]
            classes.append(SYBIL_CLASS_TEMPLATE.format(idx=idx, next_idx=next_idx))

        return "\n\n".join(classes)

    @classmethod
    def inject_sybil_mesh(cls, source_code: str, node_count: int = 4, seed: int = 42) -> str:
        """Appends a Sybil network to a Python module."""
        mesh = cls.generate_sybil_mesh(node_count=node_count, seed=seed)
        return source_code + "\n\n# --- Virtualized Inter-Process Delegation Mesh ---\n" + mesh + "\n"
