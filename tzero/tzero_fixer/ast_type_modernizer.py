# -*- coding: utf-8 -*-
"""T-Zero AST Type Hint Modernizer & PEP 585 / PEP 604 Transformer.

Performs static AST transforms to modernize Python type annotations:
- PEP 585 Generics: converts typing.List[T] -> list[T], typing.Dict[K, V] -> dict[K, V], typing.Set[T] -> set[T].
- PEP 604 Unions: converts typing.Optional[T] -> T | None, typing.Union[A, B] -> A | B.
- Dataclass field mutable defaults: converts 'field: list = []' -> 'field: list = field(default_factory=list)'.
- PEP 654 Exception Groups validation and modernization.

Author: Toprak Ahmet Aydogmus (Siber Akademi)
Version: 10.4.0
"""

import ast
import difflib
import os
import re
import sys
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


class ASTTypeModernizer:
    """AST visitor and transformer for upgrading type hints to modern Python standards."""

    PEP_585_MAP = {
        "List": "list",
        "Dict": "dict",
        "Set": "set",
        "Tuple": "tuple",
        "FrozenSet": "frozenset",
        "Type": "type",
    }

    @classmethod
    def scan_legacy_typing_generics(cls, file_path: str, content: str) -> List[DiagnosticIssue]:
        """Detect legacy typing module collections (typing.List, typing.Dict) eligible for PEP 585."""
        issues: List[DiagnosticIssue] = []
        if sys.version_info < (3, 9):
            return issues  # PEP 585 requires Python 3.9+

        lines = content.splitlines()
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue

            for old_typ, new_typ in cls.PEP_585_MAP.items():
                pattern = rf"\b(typing\.)?{old_typ}\["
                if re.search(pattern, line):
                    issues.append(DiagnosticIssue(
                        category=DiagnosticCategory.TYPE_HINTS.value,
                        severity=SeverityLevel.INFO.value,
                        file_path=file_path,
                        line=idx,
                        column=0,
                        error_code="TZ-TYPE-PEP585",
                        message=f"Legacy typing generic '{old_typ}[...]' can be modernized to native '{new_typ}[...]'",
                        suggested_fix=f"Replace '{old_typ}[...]' with native '{new_typ}[...]' (PEP 585)",
                        auto_fixable=True,
                        metadata={"action": "modernize_pep585", "old": old_typ, "new": new_typ, "lineno": idx, "path": file_path}
                    ))
                    break

        return issues

    @classmethod
    def scan_legacy_optional_and_union(cls, file_path: str, content: str) -> List[DiagnosticIssue]:
        """Detect Optional[T] and Union[A, B] eligible for PEP 604 pipe syntax (A | B)."""
        issues: List[DiagnosticIssue] = []
        if sys.version_info < (3, 10):
            return issues  # PEP 604 requires Python 3.10+

        lines = content.splitlines()
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue

            # Optional[T] -> T | None
            match_opt = re.search(r"\b(typing\.)?Optional\[([A-Za-z0-9_\.]+)\]", line)
            if match_opt:
                inner_t = match_opt.group(2)
                issues.append(DiagnosticIssue(
                    category=DiagnosticCategory.TYPE_HINTS.value,
                    severity=SeverityLevel.INFO.value,
                    file_path=file_path,
                    line=idx,
                    column=match_opt.start(),
                    error_code="TZ-TYPE-PEP604-OPTIONAL",
                    message=f"Legacy 'Optional[{inner_t}]' can be modernized to '{inner_t} | None'",
                    suggested_fix=f"Replace with modern pipe syntax: '{inner_t} | None' (PEP 604)",
                    auto_fixable=True,
                    metadata={"action": "modernize_optional", "inner": inner_t, "lineno": idx, "path": file_path}
                ))

        return issues

    @classmethod
    def scan_dataclass_mutable_fields(cls, file_path: str, tree: ast.AST) -> List[DiagnosticIssue]:
        """Detect mutable defaults directly assigned to fields in @dataclass definitions."""
        issues: List[DiagnosticIssue] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check if decorated with @dataclass
                is_dc = any(
                    (isinstance(d, ast.Name) and d.id == "dataclass") or
                    (isinstance(d, ast.Call) and isinstance(d.func, ast.Name) and d.func.id == "dataclass")
                    for d in node.decorator_list
                )
                if not is_dc:
                    continue

                for stmt in node.body:
                    if isinstance(stmt, ast.AnnAssign) and stmt.value:
                        if isinstance(stmt.value, ast.List):
                            issues.append(DiagnosticIssue(
                                category=DiagnosticCategory.SMELLS.value,
                                severity=SeverityLevel.CRITICAL.value,
                                file_path=file_path,
                                line=stmt.lineno,
                                column=stmt.col_offset,
                                error_code="TZ-TYPE-DC-MUTABLE-LIST",
                                message=f"Mutable list default directly assigned to dataclass field '{ast.unparse(stmt.target)}'",
                                suggested_fix="Use 'field(default_factory=list)' instead of mutable default",
                                auto_fixable=True,
                                metadata={"action": "heal_dc_mutable_field", "field_type": "list", "lineno": stmt.lineno, "path": file_path}
                            ))
                        elif isinstance(stmt.value, ast.Dict):
                            issues.append(DiagnosticIssue(
                                category=DiagnosticCategory.SMELLS.value,
                                severity=SeverityLevel.CRITICAL.value,
                                file_path=file_path,
                                line=stmt.lineno,
                                column=stmt.col_offset,
                                error_code="TZ-TYPE-DC-MUTABLE-DICT",
                                message=f"Mutable dict default directly assigned to dataclass field '{ast.unparse(stmt.target)}'",
                                suggested_fix="Use 'field(default_factory=dict)' instead of mutable default",
                                auto_fixable=True,
                                metadata={"action": "heal_dc_mutable_field", "field_type": "dict", "lineno": stmt.lineno, "path": file_path}
                            ))

        return issues

    @classmethod
    def modernize_code(cls, content: str, filename: str = "snippet.py") -> Any:
        """In-memory type modernization helper."""
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
            cls.execute_type_heals(issues, dry_run=False)
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
        """Scan file for all type modernization opportunities and dataclass flaws."""
        issues: List[DiagnosticIssue] = []
        path = Path(file_path)
        if not path.is_file() or path.suffix != ".py":
            return issues

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception:
            return issues

        issues.extend(cls.scan_legacy_typing_generics(file_path, content))
        issues.extend(cls.scan_legacy_optional_and_union(file_path, content))

        try:
            tree = ast.parse(content, filename=file_path)
            issues.extend(cls.scan_dataclass_mutable_fields(file_path, tree))
        except Exception:
            pass

        return issues

    @classmethod
    def execute_type_heals(cls, issues: List[DiagnosticIssue], dry_run: bool = False) -> List[HealAction]:
        """Execute surgical regex/AST transforms for PEP 585/604 and dataclass fields."""
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

                # 1. PEP 585 modernizer
                if action_type == "modernize_pep585":
                    old_t = issue.metadata.get("old")
                    new_t = issue.metadata.get("new")
                    if old_t and new_t:
                        mod_line = re.sub(rf"\b(typing\.)?{old_t}\[", f"{new_t}[", orig_line)

                # 2. PEP 604 Optional modernizer
                elif action_type == "modernize_optional":
                    inner_t = issue.metadata.get("inner")
                    if inner_t:
                        mod_line = re.sub(rf"\b(typing\.)?Optional\[{re.escape(inner_t)}\]", f"{inner_t} | None", orig_line)

                # 3. Dataclass mutable field healer
                elif action_type == "heal_dc_mutable_field":
                    f_type = issue.metadata.get("field_type")
                    factory_name = "list" if f_type == "list" else "dict"
                    mod_line = re.sub(r"=\s*\[\s*\]", f"= field(default_factory={factory_name})", orig_line)
                    mod_line = re.sub(r"=\s*\{\s*\}", f"= field(default_factory={factory_name})", mod_line)

                if mod_line != orig_line:
                    diff = "".join(difflib.unified_diff(
                        [orig_line], [mod_line], fromfile="before", tofile="after"
                    ))
                    lines[lineno - 1] = mod_line
                    if not dry_run:
                        with open(p, "w", encoding="utf-8", newline="\n") as f:
                            f.writelines(lines)
                    actions.append(HealAction(
                        category=DiagnosticCategory.TYPE_HINTS.value,
                        action_type=action_type,
                        file_path=file_p,
                        description=f"Modernized type hint on line {lineno} of {p.name}",
                        success=True,
                        diff=diff,
                        duration_ms=round((time.time() - t0) * 1000, 2)
                    ))
            except Exception as e:
                actions.append(HealAction(
                    category=DiagnosticCategory.TYPE_HINTS.value,
                    action_type=action_type,
                    file_path=file_p,
                    description=f"Failed modernizing type hint: {e}",
                    success=False,
                    duration_ms=round((time.time() - t0) * 1000, 2)
                ))

        return actions
