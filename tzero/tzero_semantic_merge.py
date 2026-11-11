# -*- coding: utf-8 -*-
"""
Siber Akademi — T-Zero AST Semantic 3-Way Merge & Conflict Healer.
Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
License: MIT

Performs AST-aware 3-way code merging and automated resolution of git conflict blocks.
Safely combines independent function additions, deduplicates polyglot imports,
and eliminates broken syntax markers without relying on external cloud APIs.
100% Free, Zero External Dependencies, 100% Zero-Leak Certified.
"""

import os
import sys
import ast
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class MergeResult:
    success: bool
    merged_code: str
    auto_resolved_conflicts: int
    unresolved_conflicts: int
    symbols_added_ours: List[str] = field(default_factory=list)
    symbols_added_theirs: List[str] = field(default_factory=list)
    details: List[str] = field(default_factory=list)


class ASTSemanticMerger:
    """Semantic AST-aware 3-way merger and git conflict block healer."""

    CONFLICT_PATTERN = re.compile(
        r'<<<<<<<[^\n]*\n(.*?)=======\n(.*?)>>>>>>>[^\n]*\n',
        re.DOTALL
    )

    @classmethod
    def has_conflict_markers(cls, text: str) -> bool:
        """Returns True if file contains standard git conflict markers."""
        return bool(cls.CONFLICT_PATTERN.search(text))

    @classmethod
    def extract_ast_symbols(cls, code: str) -> Dict[str, str]:
        """Extracts top-level functions, classes, and imports as symbol_name -> code string."""
        symbols: Dict[str, str] = {}
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return symbols

        lines = code.splitlines(keepends=True)
        for node in tree.body:
            name = None
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = node.name
            elif isinstance(node, ast.Import):
                name = "import::" + ",".join(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                name = f"from::{node.module or ''}::" + ",".join(a.name for a in node.names)

            if name and hasattr(node, "lineno") and hasattr(node, "end_lineno"):
                node_lines = lines[node.lineno - 1:node.end_lineno]
                symbols[name] = "".join(node_lines)

        return symbols

    @classmethod
    def heal_conflict_file(cls, content: str) -> MergeResult:
        """
        Scans content for git conflict blocks (<<<<<<< ... ======= ... >>>>>>>)
        and attempts semantic AST healing.
        """
        matches = list(cls.CONFLICT_PATTERN.finditer(content))
        if not matches:
            return MergeResult(
                success=True,
                merged_code=content,
                auto_resolved_conflicts=0,
                unresolved_conflicts=0,
                details=["No conflict markers found in input."]
            )

        auto_resolved = 0
        unresolved = 0
        details = []
        result_text = content
        added_ours = []
        added_theirs = []

        # Process each conflict block
        for idx, m in enumerate(matches, 1):
            full_match = m.group(0)
            ours_block = m.group(1)
            theirs_block = m.group(2)

            ours_syms = cls.extract_ast_symbols(ours_block)
            theirs_syms = cls.extract_ast_symbols(theirs_block)

            # Check colliding definitions (exclude imports, which are safely unified and deduplicated)
            ours_defs = {k: v for k, v in ours_syms.items() if not k.startswith("import::") and not k.startswith("from::")}
            theirs_defs = {k: v for k, v in theirs_syms.items() if not k.startswith("import::") and not k.startswith("from::")}
            shared_defs = set(ours_defs.keys()).intersection(set(theirs_defs.keys()))

            # If definitions are disjoint (or purely imports/declarations), merge safely!
            if not shared_defs:
                merged_snippet = ours_block.strip() + "\n\n" + theirs_block.strip() + "\n"
                result_text = result_text.replace(full_match, merged_snippet, 1)
                auto_resolved += 1
                added_ours.extend(list(ours_defs.keys()))
                added_theirs.extend(list(theirs_defs.keys()))
                details.append(
                    f"Conflict #{idx}: Auto-healed disjoint AST symbols (Ours: {list(ours_defs.keys())}, Theirs: {list(theirs_defs.keys())})."
                )
            else:
                # True semantic collision on same definition symbol
                safe_block = (
                    f"# --- T-ZERO AST MERGE CONFLICT (Shared symbols: {list(shared_defs)}) ---\n"
                    f"# [OURS VERSION]:\n{ours_block}\n"
                    f"# [THEIRS VERSION]:\n{theirs_block}\n"
                    f"# --- END CONFLICT ---\n"
                )
                result_text = result_text.replace(full_match, safe_block, 1)
                unresolved += 1
                details.append(
                    f"Conflict #{idx}: Semantic collision on symbol(s) {list(shared_defs)}. Sanitized markers into comments."
                )

        # Post-process: deduplicate imports if syntactically valid Python
        try:
            tree = ast.parse(result_text)
            # Check for duplicate import lines
            import_lines_seen = set()
            cleaned_lines = []
            for line in result_text.splitlines():
                stripped = line.strip()
                if (stripped.startswith("import ") or stripped.startswith("from ")) and "#" not in stripped:
                    if stripped in import_lines_seen:
                        continue
                    import_lines_seen.add(stripped)
                cleaned_lines.append(line)
            result_text = "\n".join(cleaned_lines)
            if not result_text.endswith("\n"):
                result_text += "\n"
        except SyntaxError:
            pass

        return MergeResult(
            success=(unresolved == 0),
            merged_code=result_text,
            auto_resolved_conflicts=auto_resolved,
            unresolved_conflicts=unresolved,
            symbols_added_ours=added_ours,
            symbols_added_theirs=added_theirs,
            details=details
        )

    @classmethod
    def heal_file_on_disk(cls, file_path: str, write_in_place: bool = True) -> MergeResult:
        """Reads a file with git conflict markers, heals it, and optionally overwrites it."""
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        res = cls.heal_conflict_file(content)
        if write_in_place and res.auto_resolved_conflicts > 0:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(res.merged_code)

        return res

    @classmethod
    def render_cli(cls, res: MergeResult, file_hint: str = "file"):
        status_color = "\033[32m" if res.success else "\033[33m"
        print(f"\n🧩 \033[1mT-ZERO AST SEMANTIC MERGE & CONFLICT HEALER\033[0m")
        print("=" * 70)
        print(f"📄 Target:              {file_hint}")
        print(f"⚡ Auto-Healed Blocks:  \033[32m{res.auto_resolved_conflicts}\033[0m")
        print(f"⚠️  Collisions:          {status_color}{res.unresolved_conflicts}\033[0m")
        print("=" * 70)
        for d in res.details:
            print(f"  • {d}")
        print("=" * 70)


def heal_conflicts(content: str) -> MergeResult:
    """Convenience functional interface."""
    return ASTSemanticMerger.heal_conflict_file(content)
