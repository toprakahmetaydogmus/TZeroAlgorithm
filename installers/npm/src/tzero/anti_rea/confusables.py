# -*- coding: utf-8 -*-
"""Tier 9: Homoglyphs & BPE Tokenizer Desynchronization.

Substitutes ASCII characters in internal, locally-scoped identifier names
with visually identical Cyrillic or Unicode homoglyphs (e.g. Cyrillic 'а' U+0430
for Latin 'a' U+0061) while strictly preserving Python builtins, decorators,
keywords, and imported symbols so runtime execution remains 100% intact.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
"""

import ast
import builtins
import keyword
import random
from typing import Dict, Optional, Set


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

_BUILTIN_PROTECTED: Set[str] = (
    set(dir(builtins))
    | set(keyword.kwlist)
    | {
        "self", "cls", "classmethod", "staticmethod", "property", "super",
        "__init__", "__name__", "__main__", "__file__", "__doc__", "__package__",
        "True", "False", "None",
    }
)


def _collect_safe_targets(tree: ast.AST, protected: Set[str]) -> Set[str]:
    """Collect private/internal locally defined names safe to rename without breaking callers or imports."""
    imported: Set[str] = set()
    public_defs: Set[str] = set()
    local_candidates: Set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imported.add(alias.asname or alias.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("_") and not node.name.startswith("__"):
                local_candidates.add(node.name)
            else:
                public_defs.add(node.name)
            # Only rename internal-looking local assignments (not kwargs/public params)
            for arg in node.args.args + node.args.kwonlyargs:
                protected.add(arg.arg)
        elif isinstance(node, ast.ClassDef):
            public_defs.add(node.name)
        elif isinstance(node, ast.Global) or isinstance(node, ast.Nonlocal):
            protected.update(node.names)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            if node.id.startswith("_") and not node.id.startswith("__"):
                local_candidates.add(node.id)

    blocked = protected | imported | public_defs
    return {name for name in local_candidates if name not in blocked and len(name) >= 4}


class HomoglyphDesynchronizer(ast.NodeTransformer):
    """AST transformer that substitutes internal identifier characters with homoglyphs."""

    def __init__(self, protected_names: Optional[Set[str]] = None, seed: int = 42, target_names: Optional[Set[str]] = None):
        super().__init__()
        self.protected_names = set(_BUILTIN_PROTECTED)
        if protected_names:
            self.protected_names |= set(protected_names)
        self.target_names = target_names
        self.rng = random.Random(seed)
        self.renamed_map: Dict[str, str] = {}

    def _convert_name(self, name: str) -> str:
        """Converts an eligible internal name using homoglyph substitution."""
        if name in self.protected_names or name.startswith("__") or len(name) < 4:
            return name
        if self.target_names is not None and name not in self.target_names:
            return name
        if name in self.renamed_map:
            return self.renamed_map[name]

        chars = list(name)
        for i, ch in enumerate(chars):
            if ch in HOMOGLYPH_MAP:
                chars[i] = HOMOGLYPH_MAP[ch]
                break

        new_name = "".join(chars)
        self.renamed_map[name] = new_name
        return new_name

    def visit_Name(self, node: ast.Name) -> ast.Name:
        """Renames eligible internal variable references."""
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
        """Applies homoglyph desynchronization to internal identifiers safely."""
        try:
            tree = ast.parse(source_code)
            protected = set(_BUILTIN_PROTECTED)
            targets = _collect_safe_targets(tree, protected)
            transformer = cls(protected_names=protected, seed=seed, target_names=targets)
            transformed = transformer.visit(tree)
            ast.fix_missing_locations(transformed)
            return ast.unparse(transformed)
        except Exception:
            return source_code
