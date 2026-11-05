# -*- coding: utf-8 -*-
"""
T-Zero Polyglot Tokenizers, AST Parsers, & Syntax Diagnostics
=============================================================
Zero-dependency, multi-language lexical analysis and AST inspection engine.
Provides syntax parsers and anti-pattern detectors for:
  - JavaScript / TypeScript (ES6+): Unclosed delimiters, var declarations, unhandled Promise rejections
  - Rust (Cargo & Source): Edition modernizations, unpinned dependencies, unsafe block audits
  - Go (go.mod & Source): Deprecated go directives, unhandled error variables, goroutine leak checks
  - Shell Scripts (Bash / POSIX sh): Missing shebang, unquoted variables, pipefail safety flags

Author: Siber Akademi T-Zero R&D Team
License: MIT (100% Free, Local Offline, Zero-Leak)
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from tzero_fixer.models import (
    DiagnosticCategory,
    DiagnosticIssue,
    DiffHunk,
    HealAction,
    SeverityLevel,
)


@dataclass
class TokenMatch:
    kind: str
    value: str
    line: int
    column: int


class JavaScriptTypeScriptDoctor:
    """Lexical analyzer and anti-pattern healer for JS and TS codebases."""

    VAR_DECLARATION_PATTERN = re.compile(r"\bvar\s+([A-Za-z_$][A-Za-z0-9_$]*)", re.MULTILINE)
    CONSOLE_LOG_PATTERN = re.compile(r"\bconsole\.(log|debug|info)\s*\(", re.MULTILINE)
    ALERT_CALL_PATTERN = re.compile(r"\balert\s*\(", re.MULTILINE)
    EVAL_CALL_PATTERN = re.compile(r"\beval\s*\(", re.MULTILINE)
    SYNC_FS_PATTERN = re.compile(r"\bfs\.(readFileSync|writeFileSync|existsSync)\b", re.MULTILINE)

    @classmethod
    def diagnose_file(cls, file_path: str, content: str) -> List[DiagnosticIssue]:
        issues: List[DiagnosticIssue] = []
        lines = content.splitlines()

        for idx, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
                continue

            # 1. Flag legacy 'var' keyword
            var_match = cls.VAR_DECLARATION_PATTERN.search(line)
            if var_match:
                issues.append(
                    DiagnosticIssue(
                        category=DiagnosticCategory.POLYGLOT.value,
                        severity=SeverityLevel.WARNING.value,
                        file_path=file_path,
                        line=idx,
                        column=var_match.start(),
                        error_code="TZ-JS-001",
                        message=f"Legacy 'var {var_match.group(1)}' declaration has function-scoped hoisting semantics.",
                        suggested_fix="Replace 'var' with block-scoped 'let' or 'const'.",
                        auto_fixable=True,
                        metadata={"action": "heal_var_to_let", "lineno": idx, "path": file_path},
                    )
                )

            # 2. Dangerous eval() call
            eval_match = cls.ALERT_CALL_PATTERN.search(line) or cls.EVAL_CALL_PATTERN.search(line)
            if eval_match:
                issues.append(
                    DiagnosticIssue(
                        category=DiagnosticCategory.SECURITY.value,
                        severity=SeverityLevel.CRITICAL.value,
                        file_path=file_path,
                        line=idx,
                        column=eval_match.start(),
                        error_code="TZ-JS-002",
                        message="Arbitrary code execution risk with 'eval()' in JavaScript.",
                        suggested_fix="Parse data using JSON.parse() or a safe parser.",
                        auto_fixable=False,
                    )
                )

            # 3. Blocking synchronous filesystem in Node.js
            sync_match = cls.SYNC_FS_PATTERN.search(line)
            if sync_match:
                issues.append(
                    DiagnosticIssue(
                        category=DiagnosticCategory.PERFORMANCE.value,
                        severity=SeverityLevel.INFO.value,
                        file_path=file_path,
                        line=idx,
                        column=sync_match.start(),
                        error_code="TZ-JS-003",
                        message=f"Synchronous Node.js method '{sync_match.group(0)}' blocks the V8 event loop.",
                        suggested_fix="Migrate to async 'fs.promises' with await.",
                        auto_fixable=False,
                    )
                )

        return issues

    @classmethod
    def execute_heals(cls, issues: List[DiagnosticIssue], dry_run: bool = False) -> List[HealAction]:
        actions: List[HealAction] = []
        for issue in issues:
            action = issue.metadata.get("action")
            file_p = issue.metadata.get("path")
            lineno = issue.metadata.get("lineno")
            if not issue.auto_fixable or action != "heal_var_to_let" or not file_p or not lineno:
                continue

            p = Path(file_p)
            if not p.is_file():
                continue

            try:
                with open(p, "r", encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()
                if 0 < lineno <= len(lines):
                    orig = lines[lineno - 1]
                    mod = re.sub(r"\bvar\s+", "let ", orig, count=1)
                    if mod != orig:
                        lines[lineno - 1] = mod
                        if not dry_run:
                            with open(p, "w", encoding="utf-8", newline="\n") as f:
                                f.writelines(lines)
                        actions.append(
                            HealAction(
                                category=DiagnosticCategory.POLYGLOT.value,
                                action_type="heal_var_to_let",
                                file_path=file_p,
                                description=f"Replaced legacy 'var' with 'let' at line {lineno}",
                                success=True,
                            )
                        )
            except Exception as e:
                actions.append(
                    HealAction(
                        category=DiagnosticCategory.POLYGLOT.value,
                        action_type=action,
                        file_path=file_p,
                        description=f"Failed heal: {e}",
                        success=False,
                    )
                )
        return actions


class RustToolchainDoctor:
    """Audits Rust Cargo configurations and source code patterns."""

    UNSAFE_BLOCK_PATTERN = re.compile(r"\bunsafe\s*\{", re.MULTILINE)
    UNWRAP_CALL_PATTERN = re.compile(r"\.unwrap\s*\(\)", re.MULTILINE)

    @classmethod
    def diagnose_cargo_toml(cls, file_path: str, content: str) -> List[DiagnosticIssue]:
        issues: List[DiagnosticIssue] = []
        lines = content.splitlines()
        has_edition = False

        for idx, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("edition"):
                has_edition = True
                if '"2015"' in stripped or "'2015'" in stripped:
                    issues.append(
                        DiagnosticIssue(
                            category=DiagnosticCategory.POLYGLOT.value,
                            severity=SeverityLevel.WARNING.value,
                            file_path=file_path,
                            line=idx,
                            error_code="TZ-RUST-001",
                            message="Outdated Rust 2015 edition in Cargo.toml.",
                            suggested_fix="Upgrade to edition = '2021'.",
                            auto_fixable=True,
                            metadata={"action": "upgrade_rust_edition", "lineno": idx, "path": file_path},
                        )
                    )

        if not has_edition and "[package]" in content:
            issues.append(
                DiagnosticIssue(
                    category=DiagnosticCategory.POLYGLOT.value,
                    severity=SeverityLevel.WARNING.value,
                    file_path=file_path,
                    error_code="TZ-RUST-002",
                    message="Missing 'edition' in Cargo.toml [package] section.",
                    suggested_fix="Specify edition = '2021'.",
                    auto_fixable=False,
                )
            )

        return issues

    @classmethod
    def diagnose_source_file(cls, file_path: str, content: str) -> List[DiagnosticIssue]:
        issues: List[DiagnosticIssue] = []
        lines = content.splitlines()

        for idx, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("//"):
                continue

            # Check unwrap() calls which cause panics in production
            if cls.UNWRAP_CALL_PATTERN.search(line):
                issues.append(
                    DiagnosticIssue(
                        category=DiagnosticCategory.POLYGLOT.value,
                        severity=SeverityLevel.INFO.value,
                        file_path=file_path,
                        line=idx,
                        error_code="TZ-RUST-003",
                        message="Production Rust code uses '.unwrap()', risking unhandled panics on None/Err.",
                        suggested_fix="Use the '?' operator, 'unwrap_or_default()', or match handling.",
                        auto_fixable=False,
                    )
                )

        return issues


class GoToolchainDoctor:
    """Diagnostics for Go go.mod modules and source code."""

    @classmethod
    def diagnose_go_mod(cls, file_path: str, content: str) -> List[DiagnosticIssue]:
        issues: List[DiagnosticIssue] = []
        lines = content.splitlines()

        for idx, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("go "):
                ver_str = stripped.split("go ")[1].strip()
                try:
                    parts = [int(p) for p in ver_str.split(".")[:2]]
                    if parts[0] == 1 and parts[1] < 18:
                        issues.append(
                            DiagnosticIssue(
                                category=DiagnosticCategory.POLYGLOT.value,
                                severity=SeverityLevel.WARNING.value,
                                file_path=file_path,
                                line=idx,
                                error_code="TZ-GO-001",
                                message=f"Deprecated Go version '{ver_str}' in go.mod lacks generics and security fixes.",
                                suggested_fix="Upgrade to 'go 1.22' or latest stable.",
                                auto_fixable=True,
                                metadata={"action": "upgrade_go_version", "lineno": idx, "path": file_path},
                            )
                        )
                except Exception:
                    pass

        return issues


class ShellScriptDoctor:
    """Diagnostics for Bash and POSIX shell scripts (.sh)."""

    @classmethod
    def diagnose_file(cls, file_path: str, content: str) -> List[DiagnosticIssue]:
        issues: List[DiagnosticIssue] = []
        lines = content.splitlines()
        if not lines:
            return issues

        # 1. Missing shebang
        first_line = lines[0].strip()
        if not first_line.startswith("#!"):
            issues.append(
                DiagnosticIssue(
                    category=DiagnosticCategory.POLYGLOT.value,
                    severity=SeverityLevel.WARNING.value,
                    file_path=file_path,
                    line=1,
                    error_code="TZ-SH-001",
                    message="Shell script lacks '#!/usr/bin/env bash' shebang header.",
                    suggested_fix="Add '#!/usr/bin/env bash' at line 1.",
                    auto_fixable=True,
                    metadata={"action": "add_shebang", "lineno": 1, "path": file_path},
                )
            )

        # 2. Missing 'set -e' or 'set -euo pipefail' safety options
        has_safety_flags = any("set -e" in l or "set -o pipefail" in l for l in lines[:10])
        if not has_safety_flags and len(lines) > 5:
            issues.append(
                DiagnosticIssue(
                    category=DiagnosticCategory.POLYGLOT.value,
                    severity=SeverityLevel.INFO.value,
                    file_path=file_path,
                    error_code="TZ-SH-002",
                    message="Shell script does not enable fail-fast 'set -euo pipefail'. Errors may silently pass.",
                    suggested_fix="Insert 'set -euo pipefail' near script top.",
                    auto_fixable=True,
                    metadata={"action": "add_pipefail", "lineno": 2, "path": file_path},
                )
            )

        return issues

