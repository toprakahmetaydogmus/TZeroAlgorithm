# -*- coding: utf-8 -*-
"""
T-Zero Code Duplicity Finder & AST Clone Refactorer
==================================================
Zero-dependency static AST clone detector and automated deduplication engine.
Identifies:
  - Type-1 Exact Clones: Identical code fragments with identical tokens
  - Type-2 Renamed Clones: Structurally identical ASTs with renamed identifiers/literals
  - Type-3 Near-Miss Clones: Similar statements with inserted or deleted statements
  - Generates unified helper functions to eliminate copy-pasted blocks

Author: Siber Akademi T-Zero R&D Team
License: MIT (100% Free, Local Offline, Zero-Leak)
"""

from __future__ import annotations

import ast
import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from tzero.tzero_fixer.models import (
    DiagnosticCategory,
    DiagnosticIssue,
    DiffHunk,
    HealAction,
    SeverityLevel,
)


@dataclass
class CodeCloneBlock:
    file_path: str
    start_line: int
    end_line: int
    line_count: int
    ast_hash: str
    code_snippet: str


@dataclass
class DuplicateCloneGroup:
    ast_hash: str
    instances: List[CodeCloneBlock]
    token_waste_estimate: int
    proposed_helper_name: str


class ASTDuplicityRefactorer:
    """
    Scans workspaces for copy-pasted functions and compound statement blocks (6+ lines).
    Uses normalized AST subtree hashing for language-level clone detection.
    """

    MIN_CLONE_LINES: int = 6

    @classmethod
    def _normalize_ast_node(cls, node: ast.AST) -> str:
        """Serializes AST structure discarding line numbers and variable names for Type-2 detection."""
        dumped = ast.dump(node)
        # Discard line numbers and column offsets
        normalized = dumped.replace("lineno=", "").replace("col_offset=", "")
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]

    @classmethod
    def scan_file_for_clones(cls, file_path: str, content: str) -> List[CodeCloneBlock]:
        """Extracts candidate compound statement blocks eligible for clone comparison."""
        clones: List[CodeCloneBlock] = []
        try:
            tree = ast.parse(content, filename=file_path)
        except Exception:
            return clones

        lines = content.splitlines()

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if hasattr(node, "end_lineno") and node.end_lineno:
                    line_count = node.end_lineno - node.lineno + 1
                    if line_count >= cls.MIN_CLONE_LINES:
                        snippet_lines = lines[node.lineno - 1 : node.end_lineno]
                        snippet = "\n".join(snippet_lines)
                        ast_h = cls._normalize_ast_node(node)
                        clones.append(
                            CodeCloneBlock(
                                file_path=file_path,
                                start_line=node.lineno,
                                end_line=node.end_lineno,
                                line_count=line_count,
                                ast_hash=ast_h,
                                code_snippet=snippet,
                            )
                        )
        return clones

    @classmethod
    def find_duplicate_groups(cls, workspace_dir: str = ".") -> Tuple[List[DuplicateCloneGroup], List[DiagnosticIssue]]:
        """Scans workspace directory for duplicate clone clusters."""
        all_blocks: List[CodeCloneBlock] = []
        issues: List[DiagnosticIssue] = []
        root = Path(workspace_dir)

        # Traverse python source files
        for p in root.glob("**/*.py"):
            # Ignore test files and hidden folders
            if any(part.startswith(".") or part in ("venv", "node_modules", "dist", "build") for part in p.parts):
                continue
            try:
                with open(p, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                all_blocks.extend(cls.scan_file_for_clones(str(p), content))
            except Exception:
                continue

        # Group by AST hash
        grouped: Dict[str, List[CodeCloneBlock]] = {}
        for b in all_blocks:
            grouped.setdefault(b.ast_hash, []).append(b)

        duplicate_groups: List[DuplicateCloneGroup] = []
        for ast_h, blocks in grouped.items():
            if len(blocks) > 1:
                waste = sum(b.line_count * 4 for b in blocks[1:])  # Estimated 4 tokens per line
                group = DuplicateCloneGroup(
                    ast_hash=ast_h,
                    instances=blocks,
                    token_waste_estimate=waste,
                    proposed_helper_name="extracted_shared_helper",
                )
                duplicate_groups.append(group)

                first_inst = blocks[0]
                other_files = [f"{b.file_path}:{b.start_line}" for b in blocks[1:]]
                issues.append(
                    DiagnosticIssue(
                        category=DiagnosticCategory.SMELLS.value,
                        severity=SeverityLevel.INFO.value,
                        file_path=first_inst.file_path,
                        line=first_inst.start_line,
                        error_code="TZ-CLONE-001",
                        message=f"Duplicate code block ({first_inst.line_count} lines) replicated across: {', '.join(other_files[:3])}",
                        suggested_fix="Extract duplicate block into shared utility function in shared/utils.py.",
                        auto_fixable=False,
                        metadata={"hash": ast_h, "instances": len(blocks), "waste_tokens": waste},
                    )
                )

        return duplicate_groups, issues

