# -*- coding: utf-8 -*-
"""Tier 9: Homoglyphs & BPE Tokenizer Desynchronization.

Substitutes ASCII characters in internal, non-exported identifier names
with visually identical Cyrillic or Unicode homoglyphs (e.g. Cyrillic 'а' U+0430
for Latin 'a' U+0061).
While Python 3 natively permits arbitrary UTF-8 identifiers, LLM Byte-Pair
Encoding (BPE) and SentencePiece tokenizers tokenize these homoglyphs as
separate, high-entropy token fragments, destroying semantic vector alignments
in the attention heads of AI coding agents.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
"""

import ast
import random
from typing import Dict, Set, Optional


# Mapping from Latin ASCII letters to visually indistinguishable Cyrillic / Greek homoglyphs
HOMOGLYPH_MAP: Dict[str, str] = {
    "a": "а",  # Cyrillic small letter a (U+0430)
    "e": "е",  # Cyrillic small letter ie (U+0435)
    "o": "о",  # Cyrillic small letter o (U+043E)
    "p": "р",  # Cyrillic small letter er (U+0440)
    "c": "с",  # Cyrillic small letter es (U+0441)
    "y": "у",  # Cyrillic small letter u (U+0443)
    "x": "х",  # Cyrillic small letter ha (U+0445)
    "i": "і",  # Cyrillic small letter byelorussian-ukrainian i (U+0456)
    "j": "ј",  # Cyrillic small letter je (U+0458)
}


class HomoglyphDesynchronizer(ast.NodeTransformer):
    """AST transformer that substitutes internal identifier characters with homoglyphs."""

    def __init__(self, protected_names: Optional[Set[str]] = None, seed: int = 42):
        super().__init__()
        self.protected_names = protected_names or {
            "self", "cls", "__init__", "__name__", "__main__", "__file__",
            "True", "False", "None", "print", "range", "len", "open"
        }
        self.rng = random.Random(seed)
        self.renamed_map: Dict[str, str] = {}

    def _convert_name(self, name: str) -> str:
        """Converts an internal name using homoglyph substitution."""
        if name in self.protected_names or name.startswith("__") or len(name) < 4:
            return name
        if name in self.renamed_map:
            return self.renamed_map[name]

        chars = list(name)
        # Substitute at least one character if possible
        for i, ch in enumerate(chars):
            if ch in HOMOGLYPH_MAP:
                chars[i] = HOMOGLYPH_MAP[ch]
                break

        new_name = "".join(chars)
        self.renamed_map[name] = new_name
        return new_name

    def visit_Name(self, node: ast.Name) -> ast.Name:
        """Renames local variable references."""
        node.id = self._convert_name(node.id)
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Renames private/internal functions starting with '_'."""
        if node.name.startswith("_") and not node.name.startswith("__"):
            node.name = self._convert_name(node.name)
        self.generic_visit(node)
        return node

    @classmethod
    def desynchronize_source(cls, source_code: str, seed: int = 42) -> str:
        """Applies homoglyph desynchronization to internal identifiers."""
        try:
            tree = ast.parse(source_code)
            transformer = cls(seed=seed)
            transformed = transformer.visit(tree)
            ast.fix_missing_locations(transformed)
            return ast.unparse(transformed)
        except Exception:
            return source_code
