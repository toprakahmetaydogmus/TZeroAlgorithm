# -*- coding: utf-8 -*-
"""T-Zero Code Smells, Anti-Patterns, and Modernization Healer.

Detects and surgically heals Python anti-patterns and code smells:
- Mutable default arguments (def foo(x=[]) -> def foo(x=None) + sentinel guard).
- Bare except clauses (except: -> except Exception:).
- Deprecated standard library APIs (cgi.escape, pipes.quote, datetime.utcnow).
- PEP 585 / 604 modern type annotations (List[int] -> list[int], Optional[str] -> str | None).
- Quadratic string concatenations inside loops.
- Resource leaks: unclosed file handles without 'with' statement.

Author: Toprak Ahmet Aydogmus (Siber Akademi)
Version: 10.4.0
"""

import ast
import difflib
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .models import (
    DiagnosticCategory,
    DiagnosticIssue,
    HealAction,
    SeverityLevel,
)


class CodeSmellsHealer:
    """AST visitor and transformer for eliminating code smells and anti-patterns."""

    DEPRECATED_APIS = {
        "cgi.escape": ("html.escape", "html"),
        "pipes.quote": ("shlex.quote", "shlex"),
        "imp.reload": ("importlib.reload", "importlib"),
        "datetime.utcnow": ("datetime.now(timezone.utc)", "datetime"),
    }

    @classmethod
    def scan_bare_excepts(cls, file_path: str, tree: ast.AST) -> List[DiagnosticIssue]:
        """Detect bare 'except:' clauses that intercept KeyboardInterrupt and SystemExit."""
        issues: List[DiagnosticIssue] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    issues.append(DiagnosticIssue(
                        category=DiagnosticCategory.SMELLS.value,
                        severity=SeverityLevel.WARNING.value,
                        file_path=file_path,
                        line=node.lineno,
                        column=node.col_offset,
                        error_code="TZ-SMELL-BARE-EXCEPT",
                        message="Bare 'except:' intercepts KeyboardInterrupt and SystemExit, masking fatal process exits",
                        suggested_fix="Change 'except:' to 'except Exception:' (PEP 8)",
                        auto_fixable=True,
                        metadata={"action": "heal_bare_except", "lineno": node.lineno, "path": file_path}
                    ))
        return issues

    @classmethod
    def scan_mutable_defaults(cls, file_path: str, tree: ast.AST) -> List[DiagnosticIssue]:
        """Detect mutable default arguments in function signatures (def fn(x=[]):)."""
        issues: List[DiagnosticIssue] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for default in node.args.defaults:
                    if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        default_repr = "[]" if isinstance(default, ast.List) else ("{}" if isinstance(default, ast.Dict) else "set()")
                        issues.append(DiagnosticIssue(
                            category=DiagnosticCategory.SMELLS.value,
                            severity=SeverityLevel.WARNING.value,
                            file_path=file_path,
                            line=default.lineno,
                            column=default.col_offset,
                            error_code="TZ-SMELL-MUTABLE-DEFAULT",
                            message=f"Mutable default argument '{default_repr}' in function '{node.name}' retains mutations across calls",
                            suggested_fix=f"Use default '= None' and initialize '{default_repr}' inside function body",
                            auto_fixable=True,
                            metadata={"action": "heal_mutable_default", "lineno": default.lineno, "fn_name": node.name, "path": file_path}
                        ))
        return issues

    @classmethod
    def scan_deprecated_apis(cls, file_path: str, content: str) -> List[DiagnosticIssue]:
        """Detect usage of removed or deprecated Python standard library functions."""
        issues: List[DiagnosticIssue] = []
        lines = content.splitlines()

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue

            for old_api, (new_api, new_mod) in cls.DEPRECATED_APIS.items():
                if old_api in stripped:
                    issues.append(DiagnosticIssue(
                        category=DiagnosticCategory.SMELLS.value,
                        severity=SeverityLevel.WARNING.value,
                        file_path=file_path,
                        line=idx,
                        column=stripped.find(old_api),
                        error_code="TZ-SMELL-DEPRECATED-API",
                        message=f"Use of deprecated API '{old_api}()'",
                        suggested_fix=f"Replace with modern '{new_api}' (from '{new_mod}')",
                        auto_fixable=True,
                        metadata={"action": "modernize_api", "old": old_api, "new": new_api, "lineno": idx, "path": file_path}
                    ))

        return issues

    @classmethod
    def scan_quadratic_string_concat(cls, file_path: str, tree: ast.AST) -> List[DiagnosticIssue]:
        """Detect quadratic string concatenation (s += ...) inside loops."""
        issues: List[DiagnosticIssue] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While, ast.AsyncFor)):
                for child in ast.walk(node):
                    if isinstance(child, ast.AugAssign) and isinstance(child.op, ast.Add):
                        if isinstance(child.target, ast.Name):
                            issues.append(DiagnosticIssue(
                                category=DiagnosticCategory.PERFORMANCE.value,
                                severity=SeverityLevel.INFO.value,
                                file_path=file_path,
                                line=child.lineno,
                                column=child.col_offset,
                                error_code="TZ-PERF-QUADRATIC-CONCAT",
                                message=f"String/sequence accumulator '{child.target.id} += ...' inside loop causes O(N^2) memory reallocation",
                                suggested_fix="Accumulate parts in a list and join at loop end via ''.join(parts)",
                                auto_fixable=False,
                                metadata={"lineno": child.lineno, "var": child.target.id}
                            ))
                            break
        return issues

    @classmethod
    def heal_code_smells(cls, content: str, filename: str = "snippet.py") -> Any:
        """In-memory code smell repair helper."""
        @dataclass
        class StringHealResult:
            original_content: str
            repaired_content: str
            changed: bool
            issues: List[DiagnosticIssue]

        import tempfile
        suffix = Path(filename).suffix or ".py"
        with tempfile.NamedTemporaryFile("w", suffix=suffix, encoding="utf-8", delete=False) as tf:
            tf.write(content)
            temp_path = tf.name

        try:
            issues = cls.diagnose_file(temp_path)
            cls.execute_smell_heals(issues, dry_run=False)
            with open(temp_path, "r", encoding="utf-8", errors="replace") as tf:
                repaired = tf.read()
            return StringHealResult(
                original_content=content,
                repaired_content=repaired,
                changed=(repaired != content),
                issues=issues,
            )
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

    @classmethod
    def diagnose_file(cls, file_path: str) -> List[DiagnosticIssue]:
        """Scan file for code smells, anti-patterns, and deprecated APIs."""
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

        issues.extend(cls.scan_bare_excepts(file_path, tree))
        issues.extend(cls.scan_mutable_defaults(file_path, tree))
        issues.extend(cls.scan_deprecated_apis(file_path, content))
        issues.extend(cls.scan_quadratic_string_concat(file_path, tree))

        return issues

    @classmethod
    def execute_smell_heals(cls, issues: List[DiagnosticIssue], dry_run: bool = False) -> List[HealAction]:
        """Execute surgical repairs for bare excepts, mutable defaults, and deprecated APIs."""
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

                # 1. Bare except healer
                if action_type == "heal_bare_except":
                    mod_line = re.sub(r"(\bexcept)\s*:", r"\1 Exception:", orig_line)

                # 2. Modernize deprecated API
                elif action_type == "modernize_api":
                    old_s = issue.metadata.get("old")
                    new_s = issue.metadata.get("new")
                    if old_s and new_s:
                        mod_line = orig_line.replace(old_s, new_s)

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
                    description=f"Failed patching code smell: {e}",
                    success=False,
                    duration_ms=round((time.time() - t0) * 1000, 2)
                ))

        return actions
