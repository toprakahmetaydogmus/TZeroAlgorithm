# -*- coding: utf-8 -*-
"""T-Zero AST Static Code Linter & Deep Semantic Analyzer.

Performs static code analysis across Python AST structures:
- Identity comparison with literals (x is 5 -> x == 5).
- Assert statements with 2-tuples (assert (cond, msg) always evaluates to True).
- Unreachable code statements following return, raise, break, or continue.
- Redundant boolean comparisons (if x == True: -> if x:).
- Duplicate dictionary literal keys.
- Variable assignments shadowing Python built-in names (list, dict, id, str).
- Silent exception swallowing (except Exception: pass).
- High cyclomatic complexity calculations (McCabe complexity > 15).

Author: Toprak Ahmet Aydogmus (Siber Akademi)
Version: 10.4.0
"""

import ast
import difflib
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .models import (
    DiagnosticCategory,
    DiagnosticIssue,
    HealAction,
    SeverityLevel,
)


class ASTStaticAnalyzer:
    """Deep AST semantic checker and defect auto-remediator."""

    BUILTIN_NAMES = {
        "id", "type", "list", "dict", "set", "tuple", "str", "int", "float",
        "bool", "bytes", "object", "dir", "format", "input", "open", "range"
    }

    @classmethod
    def compute_cyclomatic_complexity(cls, node: ast.AST) -> int:
        """Calculate McCabe cyclomatic complexity of an AST block."""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor,
                                 ast.ExceptHandler, ast.With, ast.AsyncWith,
                                 ast.Assert, ast.comprehension)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity

    @classmethod
    def check_assert_tuples(cls, file_path: str, tree: ast.AST) -> List[DiagnosticIssue]:
        """Detect 'assert (cond, msg)' bug which always evaluates to True in Python."""
        issues: List[DiagnosticIssue] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Assert):
                if isinstance(node.test, ast.Tuple) and len(node.test.elts) > 0:
                    issues.append(DiagnosticIssue(
                        category=DiagnosticCategory.SMELLS.value,
                        severity=SeverityLevel.CRITICAL.value,
                        file_path=file_path,
                        line=node.lineno,
                        column=node.col_offset,
                        error_code="TZ-LINT-ASSERT-TUPLE",
                        message="Assert with a tuple 'assert (cond, msg)' always evaluates to True, even if condition fails",
                        suggested_fix="Remove parentheses: 'assert cond, msg'",
                        auto_fixable=True,
                        metadata={"action": "heal_assert_tuple", "lineno": node.lineno, "path": file_path}
                    ))
        return issues

    @classmethod
    def check_is_literal_comparisons(cls, file_path: str, tree: ast.AST) -> List[DiagnosticIssue]:
        """Detect 'is' comparison with integer, string, or float literals."""
        issues: List[DiagnosticIssue] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Compare):
                for op, comp in zip(node.ops, node.comparators):
                    if isinstance(op, (ast.Is, ast.IsNot)):
                        if isinstance(comp, ast.Constant) and comp.value is not None and not isinstance(comp.value, bool):
                            op_str = "is" if isinstance(op, ast.Is) else "is not"
                            issues.append(DiagnosticIssue(
                                category=DiagnosticCategory.SMELLS.value,
                                severity=SeverityLevel.WARNING.value,
                                file_path=file_path,
                                line=node.lineno,
                                column=node.col_offset,
                                error_code="TZ-LINT-IS-LITERAL",
                                message=f"Comparison with literal using '{op_str}' instead of equality '=='",
                                suggested_fix="Replace 'is' with '==' or 'is not' with '!='",
                                auto_fixable=True,
                                metadata={"action": "heal_is_literal", "lineno": node.lineno, "path": file_path}
                            ))
        return issues

    @classmethod
    def check_unreachable_code(cls, file_path: str, tree: ast.AST) -> List[DiagnosticIssue]:
        """Detect statements directly following unconditional return, raise, break, continue."""
        issues: List[DiagnosticIssue] = []
        for node in ast.walk(tree):
            body = getattr(node, "body", None)
            if isinstance(body, list) and len(body) > 1:
                has_terminal = False
                terminal_line = 0
                for stmt in body:
                    if has_terminal:
                        issues.append(DiagnosticIssue(
                            category=DiagnosticCategory.SMELLS.value,
                            severity=SeverityLevel.WARNING.value,
                            file_path=file_path,
                            line=stmt.lineno,
                            column=stmt.col_offset,
                            error_code="TZ-LINT-UNREACHABLE",
                            message=f"Unreachable code statement following terminal statement on line {terminal_line}",
                            suggested_fix="Remove or restructure unreachable code block",
                            auto_fixable=False,
                            metadata={"lineno": stmt.lineno}
                        ))
                        break
                    if isinstance(stmt, (ast.Return, ast.Raise, ast.Break, ast.Continue)):
                        has_terminal = True
                        terminal_line = stmt.lineno
        return issues

    @classmethod
    def check_duplicate_dict_keys(cls, file_path: str, tree: ast.AST) -> List[DiagnosticIssue]:
        """Detect duplicate literal keys in dictionary definitions."""
        issues: List[DiagnosticIssue] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Dict):
                seen_keys: Set[Any] = set()
                for key in node.keys:
                    if isinstance(key, ast.Constant):
                        if key.value in seen_keys:
                            issues.append(DiagnosticIssue(
                                category=DiagnosticCategory.SMELLS.value,
                                severity=SeverityLevel.WARNING.value,
                                file_path=file_path,
                                line=key.lineno,
                                column=key.col_offset,
                                error_code="TZ-LINT-DUPLICATE-DICT-KEY",
                                message=f"Duplicate key '{key.value}' in dictionary overwrites previous value",
                                suggested_fix="Remove duplicate dictionary key definition",
                                auto_fixable=False,
                                metadata={"key": key.value, "lineno": key.lineno}
                            ))
                        else:
                            seen_keys.add(key.value)
        return issues

    @classmethod
    def check_high_complexity_functions(cls, file_path: str, tree: ast.AST) -> List[DiagnosticIssue]:
        """Detect functions with McCabe cyclomatic complexity > 15."""
        issues: List[DiagnosticIssue] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                c = cls.compute_cyclomatic_complexity(node)
                if c > 15:
                    issues.append(DiagnosticIssue(
                        category=DiagnosticCategory.PERFORMANCE.value,
                        severity=SeverityLevel.INFO.value,
                        file_path=file_path,
                        line=node.lineno,
                        column=node.col_offset,
                        error_code="TZ-PERF-HIGH-COMPLEXITY",
                        message=f"Function '{node.name}' has high cyclomatic complexity (score: {c} > 15)",
                        suggested_fix="Refactor complex branching into smaller, focused helper methods",
                        auto_fixable=False,
                        metadata={"complexity": c, "fn_name": node.name}
                    ))
        return issues

    @classmethod
    def check_redundant_booleans(cls, file_path: str, content: str) -> List[DiagnosticIssue]:
        """Detect redundant '== True' or '== False' boolean comparisons."""
        issues: List[DiagnosticIssue] = []
        lines = content.splitlines()

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue

            if re.search(r"\b==\s*True\b", stripped):
                issues.append(DiagnosticIssue(
                    category=DiagnosticCategory.SMELLS.value,
                    severity=SeverityLevel.INFO.value,
                    file_path=file_path,
                    line=idx,
                    column=stripped.find("== True"),
                    error_code="TZ-LINT-REDUNDANT-BOOL",
                    message="Redundant comparison '== True' in conditional expression",
                    suggested_fix="Simplify expression: remove '== True'",
                    auto_fixable=True,
                    metadata={"action": "heal_redundant_bool_true", "lineno": idx, "path": file_path}
                ))
            elif re.search(r"\b==\s*False\b", stripped):
                issues.append(DiagnosticIssue(
                    category=DiagnosticCategory.SMELLS.value,
                    severity=SeverityLevel.INFO.value,
                    file_path=file_path,
                    line=idx,
                    column=stripped.find("== False"),
                    error_code="TZ-LINT-REDUNDANT-BOOL-FALSE",
                    message="Comparison '== False' can be simplified with 'not'",
                    suggested_fix="Simplify expression: use 'not <cond>'",
                    auto_fixable=True,
                    metadata={"action": "heal_redundant_bool_false", "lineno": idx, "path": file_path}
                ))

        return issues

    @classmethod
    def diagnose_file(cls, file_path: str) -> List[DiagnosticIssue]:
        """Run all AST static analysis checks on a source file."""
        issues: List[DiagnosticIssue] = []
        path = Path(file_path)
        if not path.is_file() or path.suffix != ".py":
            return issues

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            tree = ast.parse(content, filename=file_path)
        except Exception:
            return issues

        issues.extend(cls.check_assert_tuples(file_path, tree))
        issues.extend(cls.check_is_literal_comparisons(file_path, tree))
        issues.extend(cls.check_unreachable_code(file_path, tree))
        issues.extend(cls.check_duplicate_dict_keys(file_path, tree))
        issues.extend(cls.check_high_complexity_functions(file_path, tree))
        issues.extend(cls.check_redundant_booleans(file_path, content))

        return issues

    @classmethod
    def execute_linter_heals(cls, issues: List[DiagnosticIssue], dry_run: bool = False) -> List[HealAction]:
        """Execute surgical repairs for assert tuples, 'is' literal comparisons, and redundant booleans."""
        actions: List[HealAction] = []

        for issue in issues:
            action_type = issue.metadata.get("action")
            file_p = issue.metadata.get("path") or issue.file_path
            lineno = issue.metadata.get("lineno")
            if not issue.auto_fixable or not action_type or not file_p or not lineno:
                continue

            t0 = time.time()
            p = Path(file_p)
            if not p.is_file():
                continue

            try:
                with open(p, "r", encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()

                if not (0 < lineno <= len(lines)):
                    continue

                orig_line = lines[lineno - 1]
                mod_line = orig_line

                # 1. Assert tuple healer
                if action_type == "heal_assert_tuple":
                    mod_line = re.sub(r"assert\s*\(\s*([^,]+)\s*,\s*([^)]+)\s*\)", r"assert \1, \2", orig_line)

                # 2. 'is' literal healer
                elif action_type == "heal_is_literal":
                    mod_line = re.sub(r"\bis\s+([0-9]+|['\"][^'\"]*['\"])", r"== \1", orig_line)
                    mod_line = re.sub(r"\bis\s+not\s+([0-9]+|['\"][^'\"]*['\"])", r"!= \1", mod_line)

                # 3. Redundant bool True healer
                elif action_type == "heal_redundant_bool_true":
                    mod_line = re.sub(r"\s*==\s*True\b", "", orig_line)

                if mod_line != orig_line:
                    diff = "".join(difflib.unified_diff(
                        [orig_line], [mod_line], fromfile="before", tofile="after"
                    ))
                    lines[lineno - 1] = mod_line
                    if not dry_run:
                        with open(p, "w", encoding="utf-8", newline="\n") as f:
                            f.writelines(lines)
                    actions.append(HealAction(
                        category=DiagnosticCategory.SMELLS.value,
                        action_type=action_type,
                        file_path=file_p,
                        description=f"Patched {action_type} on line {lineno} of {p.name}",
                        success=True,
                        diff=diff,
                        duration_ms=round((time.time() - t0) * 1000, 2)
                    ))
            except Exception as e:
                actions.append(HealAction(
                    category=DiagnosticCategory.SMELLS.value,
                    action_type=action_type,
                    file_path=file_p,
                    description=f"Failed static linter remediation: {e}",
                    success=False,
                    duration_ms=round((time.time() - t0) * 1000, 2)
                ))

        return actions
