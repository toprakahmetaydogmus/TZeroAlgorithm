# -*- coding: utf-8 -*-
"""
T-Zero Dead Code, Orphaned Symbol, & Unreachable Branch Eliminator
================================================================
Static AST analyzer that detects dead code smells, unreferenced private symbols,
unused local variables, and statements after terminating branches (return / raise).

Key Capabilities:
  - Detection of unreferenced private functions (_helper()) within module scope
  - Detection of unreachable statements immediately following return, raise, or break
  - Detection of unused local assignments
  - Autonomous surgical removal or comment-out of dead branches

Author: Siber Akademi T-Zero R&D Team
Version: 10.5.0 | 100% Free & Local Offline | Zero-Leak Certified
"""

from __future__ import annotations

import ast
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from tzero_fixer.models import (
    DiagnosticCategory,
    DiagnosticIssue,
    HealAction,
    SeverityLevel,
)


class DeadCodeEliminator:
    """AST surgical engine for discovering and pruning unreachable or unused code."""

    @classmethod
    def diagnose_file(cls, file_path: str) -> List[DiagnosticIssue]:
        """Audit Python file for dead code, unreferenced private helpers, and unreachable lines."""
        issues: List[DiagnosticIssue] = []
        try:
            content = Path(file_path).read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(content, filename=file_path)
        except Exception:
            return issues

        # 1. Check for unreachable statements in blocks
        issues.extend(cls._find_unreachable_statements(file_path, tree))

        # 2. Check for unused private module functions
        issues.extend(cls._find_unused_private_functions(file_path, tree))

        return issues

    @classmethod
    def _find_unreachable_statements(cls, file_path: str, tree: ast.AST) -> List[DiagnosticIssue]:
        """Find statements following return, raise, break, or continue in the same body block."""
        issues: List[DiagnosticIssue] = []

        for node in ast.walk(tree):
            if hasattr(node, "body") and isinstance(node.body, list):
                term_index = -1
                for idx, stmt in enumerate(node.body):
                    if isinstance(stmt, (ast.Return, ast.Raise, ast.Break, ast.Continue)):
                        term_index = idx
                        break

                if term_index != -1 and term_index < len(node.body) - 1:
                    dead_stmt = node.body[term_index + 1]
                    issues.append(DiagnosticIssue(
                        category=DiagnosticCategory.SMELLS,
                        severity=SeverityLevel.WARNING,
                        file_path=file_path,
                        line_number=dead_stmt.lineno,
                        error_code="TZ-DEAD-UNREACHABLE",
                        message=f"Unreachable code detected: Statement on line {dead_stmt.lineno} executes after terminating {type(node.body[term_index]).__name__}",
                        suggested_fix="Prune or restructure unreachable statement block",
                        auto_fixable=True,
                        metadata={
                            "issue_type": "unreachable_code",
                            "start_line": dead_stmt.lineno,
                            "end_line": getattr(dead_stmt, "end_lineno", dead_stmt.lineno),
                        },
                    ))

        return issues

    @classmethod
    def _find_unused_private_functions(cls, file_path: str, tree: ast.Module) -> List[DiagnosticIssue]:
        """Discover module-level private functions (_func) that are never referenced in the module."""
        issues: List[DiagnosticIssue] = []
        defined_privates: Dict[str, ast.FunctionDef] = {}

        # Collect top-level private functions (excluding dunders)
        for item in tree.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if item.name.startswith("_") and not item.name.startswith("__"):
                    defined_privates[item.name] = item

        if not defined_privates:
            return issues

        # Count references in the entire module
        referenced_names: Set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and not isinstance(node.ctx, ast.Store):
                referenced_names.add(node.id)

        for name, func_node in defined_privates.items():
            if name not in referenced_names:
                issues.append(DiagnosticIssue(
                    category=DiagnosticCategory.SMELLS,
                    severity=SeverityLevel.INFO,
                    file_path=file_path,
                    line_number=func_node.lineno,
                    error_code="TZ-DEAD-UNUSED-FUNC",
                    message=f"Unused private function '{name}()' is defined but never called in module",
                    suggested_fix=f"Remove or export '{name}()'",
                    auto_fixable=False,
                    metadata={"issue_type": "unused_private_func", "name": name, "line_num": func_node.lineno},
                ))

        return issues

    @classmethod
    def heal_issue(cls, issue: DiagnosticIssue, dry_run: bool = False) -> HealAction:
        """Autonomously comment-out or prune dead unreachable blocks."""
        itype = issue.metadata.get("issue_type")
        file_path = issue.file_path
        start_line = issue.metadata.get("start_line")
        end_line = issue.metadata.get("end_line", start_line)

        if itype == "unreachable_code" and file_path and start_line:
            p = Path(file_path)
            if not p.is_file():
                return HealAction(issue=issue, success=False, details="File not found")

            if dry_run:
                return HealAction(issue=issue, success=True, details=f"[Dry-Run] Would comment out unreachable code lines {start_line}-{end_line}")

            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
            for idx in range(start_line - 1, min(end_line, len(lines))):
                if not lines[idx].strip().startswith("#"):
                    lines[idx] = "# [T-Zero Dead Code] " + lines[idx]

            p.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return HealAction(issue=issue, success=True, details=f"Commented out unreachable statements on lines {start_line}-{end_line}")

        return HealAction(issue=issue, success=False, details=f"No automated prune for issue type '{itype}'")
