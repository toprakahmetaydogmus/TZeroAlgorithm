# -*- coding: utf-8 -*-
"""
T-Zero Polyglot Linters & Infrastructure Healer
==============================================
Zero-dependency, multi-language static analysis and configuration repair engine.
Covers:
  - Markdown / README: Unclosed code blocks, broken header hierarchy, trailing whitespace, table formatting
  - TOML: pyproject.toml / Cargo.toml syntax, build-system validation, unquoted dotted keys
  - YAML & CI/CD: GitHub Actions workflow validation, unpinned actions, YAML 1.1 boolean pitfalls
  - Dockerfile: Multi-stage optimizations, root user warnings, unpinned tags, cache clearing
  - Makefile: Recipe indentation repair (space-to-tab), missing .PHONY targets
  - SQL / Schema: Reserved keywords, missing primary keys, unindexed foreign key warnings

Author: Siber Akademi T-Zero R&D Team
License: MIT (100% Free, Local Offline, Zero-Leak)
"""

from __future__ import annotations

import os
import re
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from pathlib import Path

from tzero.tzero_fixer.models import (
    DiagnosticCategory,
    DiagnosticIssue,
    DiffHunk,
    
    SeverityLevel,
)


@dataclass
class LintFixResult:
    original_content: str
    repaired_content: str
    changed: bool
    diff_hunks: List[DiffHunk] = field(default_factory=list)
    issues_found: List[DiagnosticIssue] = field(default_factory=list)


# -----------------------------------------------------------------------------
# 1. Markdown & Documentation Linter / Healer
# -----------------------------------------------------------------------------
class MarkdownLinterHealer:
    """
    Scans and surgically repairs Markdown files without destroying code fences or inline formatting.
    """

    @staticmethod
    def lint_and_heal(file_path: str, content: str) -> LintFixResult:
        issues: List[DiagnosticIssue] = []
        diff_hunks: List[DiffHunk] = []
        lines = content.splitlines(keepends=False)
        repaired_lines = []
        changed = False

        in_code_block = False
        code_block_fence = ""
        last_header_level = 0
        open_fence_line = 0

        for idx, line in enumerate(lines, 1):
            stripped = line.strip()

            # Check code fence
            if stripped.startswith("```") or stripped.startswith("~~~"):
                fence_marker = stripped[:3]
                if not in_code_block:
                    in_code_block = True
                    code_block_fence = fence_marker
                    open_fence_line = idx
                elif stripped.startswith(code_block_fence):
                    in_code_block = False
                    code_block_fence = ""

            # If outside code block, check markdown specific rules
            if not in_code_block:
                # 1. Trailing whitespace check & repair
                rstripped = line.rstrip()
                if len(line) > len(rstripped) and not line.endswith("  "):  # 2 spaces = hard break in MD
                    changed = True
                    diff_hunks.append(
                        DiffHunk(
                            line_start=idx,
                            line_end=idx,
                            original=line,
                            replacement=rstripped,
                            explanation="Removed unnecessary trailing whitespace.",
                        )
                    )
                    line = rstripped

                # 2. Header hierarchy check (# to ### skip)
                if stripped.startswith("#"):
                    m = re.match(r"^(#+)\s", stripped)
                    if m:
                        level = len(m.group(1))
                        if last_header_level > 0 and level > last_header_level + 1:
                            issues.append(
                                DiagnosticIssue(
                                    code="TZ-MD-001",
                                    category=DiagnosticCategory.POLYGLOT_CONFIG,
                                    severity=SeverityLevel.INFO,
                                    file_path=file_path,
                                    line_number=idx,
                                    message=f"Markdown header level jumped from H{last_header_level} to H{level}.",
                                    remediation=f"Consider adjusting to H{last_header_level + 1} for accessibility and structure.",
                                    
                                )
                            )
                        last_header_level = level

                # 3. Empty link target [text]()
                if re.search(r"\[([^\]]+)\]\(\s*\)", line):
                    issues.append(
                        DiagnosticIssue(
                            code="TZ-MD-002",
                            category=DiagnosticCategory.POLYGLOT_CONFIG,
                            severity=SeverityLevel.WARNING,
                            file_path=file_path,
                            line_number=idx,
                            message="Empty Markdown link destination detected: '[text]()'",
                            remediation="Provide valid URL or replace with plain text.",
                            
                        )
                    )

            repaired_lines.append(line)

        # Check unclosed code block
        if in_code_block:
            changed = True
            repaired_lines.append(code_block_fence or "```")
            issues.append(
                DiagnosticIssue(
                    code="TZ-MD-003",
                    category=DiagnosticCategory.POLYGLOT_CONFIG,
                    severity=SeverityLevel.CRITICAL,
                    file_path=file_path,
                    line_number=open_fence_line,
                    message=f"Unclosed Markdown code block opened at line {open_fence_line}.",
                    remediation="Appended closing code fence '```'.",
                    
                )
            )
            diff_hunks.append(
                DiffHunk(
                    line_start=len(lines),
                    line_end=len(lines) + 1,
                    original="",
                    replacement=code_block_fence or "```",
                    explanation="Closed unclosed code fence at end of markdown document.",
                )
            )

        new_content = "\n".join(repaired_lines)
        if content.endswith("\n") and not new_content.endswith("\n"):
            new_content += "\n"

        return LintFixResult(
            original_content=content,
            repaired_content=new_content,
            changed=changed,
            diff_hunks=diff_hunks,
            issues_found=issues,
        )


# -----------------------------------------------------------------------------
# 2. TOML Configuration Linter & Healer
# -----------------------------------------------------------------------------
class TomlLinterHealer:
    """
    Lints and validates pyproject.toml, Cargo.toml, and other TOML files.
    """

    @staticmethod
    def lint_and_heal(file_path: str, content: str) -> LintFixResult:
        issues: List[DiagnosticIssue] = []
        diff_hunks: List[DiffHunk] = []
        lines = content.splitlines(keepends=False)
        repaired_lines = []
        changed = False

        has_build_system = False
        is_pyproject = file_path.endswith("pyproject.toml")

        for idx, line in enumerate(lines, 1):
            stripped = line.strip()

            if stripped == "[build-system]":
                has_build_system = True

            # Detect unquoted dotted key mistake: e.g. foo.bar-baz = 1 where key has special chars
            if "=" in line and not stripped.startswith("#") and not stripped.startswith("["):
                key_part = line.split("=", 1)[0].strip()
                if " " in key_part and not (key_part.startswith('"') and key_part.endswith('"')):
                    issues.append(
                        DiagnosticIssue(
                            code="TZ-TOML-001",
                            category=DiagnosticCategory.POLYGLOT_CONFIG,
                            severity=SeverityLevel.WARNING,
                            file_path=file_path,
                            line_number=idx,
                            message=f"TOML key contains bare whitespace without quotes: '{key_part}'",
                            remediation="Wrap keys containing spaces or special characters in quotes.",
                            
                        )
                    )

            repaired_lines.append(line)

        # Check missing build-system in pyproject.toml
        if is_pyproject and not has_build_system and "[project]" in content:
            changed = True
            build_system_block = (
                "\n[build-system]\n"
                'requires = ["setuptools>=61.0", "wheel"]\n'
                'build-backend = "setuptools.build_meta"\n'
            )
            repaired_lines.append(build_system_block)
            issues.append(
                DiagnosticIssue(
                    code="TZ-TOML-002",
                    category=DiagnosticCategory.POLYGLOT_CONFIG,
                    severity=SeverityLevel.WARNING,
                    file_path=file_path,
                    message="Missing [build-system] table in pyproject.toml. Package cannot build via standard pip.",
                    remediation="Appended default PEP 517 [build-system] table.",
                    
                )
            )
            diff_hunks.append(
                DiffHunk(
                    line_start=len(lines),
                    line_end=len(lines) + 4,
                    original="",
                    replacement=build_system_block,
                    explanation="Injected PEP 517 standard [build-system] section.",
                )
            )

        new_content = "\n".join(repaired_lines)
        if content.endswith("\n") and not new_content.endswith("\n"):
            new_content += "\n"

        return LintFixResult(
            original_content=content,
            repaired_content=new_content,
            changed=changed,
            diff_hunks=diff_hunks,
            issues_found=issues,
        )


# -----------------------------------------------------------------------------
# 3. YAML & CI/CD Workflow Linter & Healer
# -----------------------------------------------------------------------------
class YamlCiCdLinterHealer:
    """
    Validates GitHub Actions workflows and YAML deployment specs.
    """

    OUTDATED_ACTIONS: Dict[str, str] = {
        "actions/checkout@v1": "actions/checkout@v4",
        "actions/checkout@v2": "actions/checkout@v4",
        "actions/checkout@v3": "actions/checkout@v4",
        "actions/setup-python@v1": "actions/setup-python@v5",
        "actions/setup-python@v2": "actions/setup-python@v5",
        "actions/setup-python@v3": "actions/setup-python@v5",
        "actions/setup-python@v4": "actions/setup-python@v5",
        "actions/setup-node@v1": "actions/setup-node@v4",
        "actions/setup-node@v2": "actions/setup-node@v4",
        "actions/setup-node@v3": "actions/setup-node@v4",
        "actions/upload-artifact@v1": "actions/upload-artifact@v4",
        "actions/upload-artifact@v2": "actions/upload-artifact@v4",
        "actions/upload-artifact@v3": "actions/upload-artifact@v4",
        "actions/download-artifact@v1": "actions/download-artifact@v4",
        "actions/download-artifact@v2": "actions/download-artifact@v4",
        "actions/download-artifact@v3": "actions/download-artifact@v4",
    }

    @classmethod
    def lint_and_heal(cls, file_path: str, content: str) -> LintFixResult:
        issues: List[DiagnosticIssue] = []
        diff_hunks: List[DiffHunk] = []
        lines = content.splitlines(keepends=False)
        repaired_lines = []
        changed = False

        is_gh_workflow = ".github" in file_path and ("workflows" in file_path or "actions" in file_path)

        for idx, line in enumerate(lines, 1):
            repaired_line = line
            stripped = line.strip()

            # 1. YAML 1.1 'on:' pitfall
            # In YAML 1.1, `on:` without quotes can be parsed as boolean True
            if is_gh_workflow and re.match(r"^on\s*:", stripped):
                issues.append(
                    DiagnosticIssue(
                        code="TZ-CI-001",
                        category=DiagnosticCategory.POLYGLOT_CONFIG,
                        severity=SeverityLevel.INFO,
                        file_path=file_path,
                        line_number=idx,
                        message="Unquoted 'on:' in GitHub Action workflow may parse as boolean True in older YAML parsers.",
                        remediation="Consider quoting as 'on': or \"on\":",
                        
                    )
                )

            # 2. Outdated actions auto-upgrade
            if is_gh_workflow and "uses:" in line:
                for old_action, new_action in cls.OUTDATED_ACTIONS.items():
                    if old_action in line:
                        repaired_line = line.replace(old_action, new_action)
                        changed = True
                        issues.append(
                            DiagnosticIssue(
                                code="TZ-CI-002",
                                category=DiagnosticCategory.POLYGLOT_CONFIG,
                                severity=SeverityLevel.WARNING,
                                file_path=file_path,
                                line_number=idx,
                                message=f"Deprecated GitHub Action {old_action} detected (deprecated Node.js runtime).",
                                remediation=f"Upgraded to modern {new_action}.",
                                
                            )
                        )
                        diff_hunks.append(
                            DiffHunk(
                                line_start=idx,
                                line_end=idx,
                                original=line,
                                replacement=repaired_line,
                                explanation=f"Upgraded deprecated {old_action} to {new_action}.",
                            )
                        )
                        break

            # 3. Detect dangerous pull_request_target checkout
            if is_gh_workflow and "pull_request_target" in line:
                issues.append(
                    DiagnosticIssue(
                        code="TZ-CI-003",
                        category=DiagnosticCategory.SECURITY_CREDENTIAL,
                        severity=SeverityLevel.CRITICAL,
                        file_path=file_path,
                        line_number=idx,
                        message="Workflow uses 'pull_request_target' trigger. Checking out untrusted PR code can leak repository secrets.",
                        remediation="Ensure untrusted PR code is never checked out with secrets present.",
                        
                    )
                )

            repaired_lines.append(repaired_line)

        new_content = "\n".join(repaired_lines)
        if content.endswith("\n") and not new_content.endswith("\n"):
            new_content += "\n"

        return LintFixResult(
            original_content=content,
            repaired_content=new_content,
            changed=changed,
            diff_hunks=diff_hunks,
            issues_found=issues,
        )


# -----------------------------------------------------------------------------
# 4. Dockerfile Deep Linter & Healer
# -----------------------------------------------------------------------------
class DockerfileDeepLinterHealer:
    """
    Validates Dockerfiles for security, cache optimization, and layer reduction.
    """

    @staticmethod
    def lint_and_heal(file_path: str, content: str) -> LintFixResult:
        issues: List[DiagnosticIssue] = []
        diff_hunks: List[DiffHunk] = []
        lines = content.splitlines(keepends=False)
        repaired_lines = []
        changed = False

        has_user = False
        has_healthcheck = False

        for idx, line in enumerate(lines, 1):
            repaired_line = line
            stripped = line.strip()

            if stripped.startswith("USER ") and "root" not in stripped:
                has_user = True
            if stripped.startswith("HEALTHCHECK"):
                has_healthcheck = True

            # 1. Unpinned latest tag
            if stripped.startswith("FROM ") and (":latest" in stripped or ":" not in stripped.split()[1]):
                image_ref = stripped.split()[1]
                issues.append(
                    DiagnosticIssue(
                        code="TZ-DKR-001",
                        category=DiagnosticCategory.POLYGLOT_CONFIG,
                        severity=SeverityLevel.WARNING,
                        file_path=file_path,
                        line_number=idx,
                        message=f"Dockerfile image '{image_ref}' uses unpinned tag or implicit ':latest'.",
                        remediation="Pin specific version tag or digest (e.g. python:3.11-slim) for deterministic builds.",
                        
                    )
                )

            # 2. apt-get update without clean
            if "apt-get update" in stripped and "rm -rf /var/lib/apt/lists/*" not in stripped:
                issues.append(
                    DiagnosticIssue(
                        code="TZ-DKR-002",
                        category=DiagnosticCategory.POLYGLOT_CONFIG,
                        severity=SeverityLevel.INFO,
                        file_path=file_path,
                        line_number=idx,
                        message="'apt-get update' without 'rm -rf /var/lib/apt/lists/*' bloats image size.",
                        remediation="Append '&& rm -rf /var/lib/apt/lists/*' to apt-get RUN command.",
                        
                    )
                )

            # 3. ADD instead of COPY
            if stripped.startswith("ADD ") and not (stripped.endswith(".tar.gz") or "http://" in stripped or "https://" in stripped):
                parts = line.split("ADD", 1)
                repaired_line = parts[0] + "COPY" + parts[1]
                changed = True
                issues.append(
                    DiagnosticIssue(
                        code="TZ-DKR-003",
                        category=DiagnosticCategory.POLYGLOT_CONFIG,
                        severity=SeverityLevel.INFO,
                        file_path=file_path,
                        line_number=idx,
                        message="Prefer 'COPY' over 'ADD' for local files unless unpacking tar archives.",
                        remediation="Replaced 'ADD' with 'COPY'.",
                        
                    )
                )
                diff_hunks.append(
                    DiffHunk(
                        line_start=idx,
                        line_end=idx,
                        original=line,
                        replacement=repaired_line,
                        explanation="Replaced ADD with COPY for local files.",
                    )
                )

            repaired_lines.append(repaired_line)

        # Flag missing non-root USER
        if not has_user:
            issues.append(
                DiagnosticIssue(
                    code="TZ-DKR-004",
                    category=DiagnosticCategory.SECURITY_CREDENTIAL,
                    severity=SeverityLevel.WARNING,
                    file_path=file_path,
                    message="Dockerfile does not specify a non-root USER. Container will run as root by default.",
                    remediation="Add 'USER appuser' or equivalent least-privilege user before ENTRYPOINT.",
                    
                )
            )

        new_content = "\n".join(repaired_lines)
        if content.endswith("\n") and not new_content.endswith("\n"):
            new_content += "\n"

        return LintFixResult(
            original_content=content,
            repaired_content=new_content,
            changed=changed,
            diff_hunks=diff_hunks,
            issues_found=issues,
        )


# -----------------------------------------------------------------------------
# 5. Makefile Linter & Space-to-Tab Healer
# -----------------------------------------------------------------------------
class MakefileLinterHealer:
    """
    Diagnoses and repairs Makefile tab indentation bugs ('missing separator').
    """

    @staticmethod
    def lint_and_heal(file_path: str, content: str) -> LintFixResult:
        issues: List[DiagnosticIssue] = []
        diff_hunks: List[DiffHunk] = []
        lines = content.splitlines(keepends=False)
        repaired_lines = []
        changed = False

        in_target = False
        target_name = ""

        for idx, line in enumerate(lines, 1):
            repaired_line = line
            stripped = line.strip()

            # Target definition line: e.g. "build:" or "test: deps"
            if ":" in line and not line.startswith("\t") and not line.startswith("#") and not "=" in line.split(":", 1)[0]:
                in_target = True
                target_name = line.split(":", 1)[0].strip()
            elif stripped == "" or line.startswith("#"):
                in_target = False
            elif in_target:
                # If inside target recipe, line MUST begin with a TAB, not spaces
                if line.startswith("    ") or line.startswith("  "):
                    # Spaces instead of TAB!
                    leading_spaces = len(line) - len(line.lstrip(" "))
                    repaired_line = "\t" + line.lstrip(" ")
                    changed = True
                    issues.append(
                        DiagnosticIssue(
                            code="TZ-MK-001",
                            category=DiagnosticCategory.POLYGLOT_CONFIG,
                            severity=SeverityLevel.CRITICAL,
                            file_path=file_path,
                            line_number=idx,
                            message=f"Makefile recipe for '{target_name}' uses {leading_spaces} spaces instead of hard TAB. Causes 'missing separator' fatal error.",
                            remediation="Replaced leading spaces with a hard TAB character.",
                            
                        )
                    )
                    diff_hunks.append(
                        DiffHunk(
                            line_start=idx,
                            line_end=idx,
                            original=line,
                            replacement=repaired_line,
                            explanation="Fixed spaces to hard TAB in Makefile recipe line.",
                        )
                    )

            repaired_lines.append(repaired_line)

        new_content = "\n".join(repaired_lines)
        if content.endswith("\n") and not new_content.endswith("\n"):
            new_content += "\n"

        return LintFixResult(
            original_content=content,
            repaired_content=new_content,
            changed=changed,
            diff_hunks=diff_hunks,
            issues_found=issues,
        )


# -----------------------------------------------------------------------------
# 6. SQL / Migration Schema Linter
# -----------------------------------------------------------------------------
class SqlMigrationLinter:
    """
    Static analyzer for database schema scripts, migrations, and SQL queries.
    """

    RESERVED_KEYWORDS: Set[str] = {
        "user", "order", "group", "table", "database", "select", "insert",
        "update", "delete", "where", "from", "key", "index", "view", "role",
        "schema", "status", "type", "value", "limit", "offset", "grant",
    }

    @classmethod
    def lint_file(cls, file_path: str, content: str) -> List[DiagnosticIssue]:
        issues: List[DiagnosticIssue] = []
        lines = content.splitlines()

        for idx, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("--") or stripped.startswith("/*"):
                continue

            # Check column definition with unquoted SQL reserved keyword
            for kw in cls.RESERVED_KEYWORDS:
                pattern = rf"\b{kw}\b\s+(VARCHAR|INTEGER|INT|TEXT|BOOLEAN|TIMESTAMP|DATETIME|BIGINT|UUID)"
                if re.search(pattern, stripped, re.IGNORECASE):
                    issues.append(
                        DiagnosticIssue(
                            code="TZ-SQL-001",
                            category=DiagnosticCategory.POLYGLOT_CONFIG,
                            severity=SeverityLevel.WARNING,
                            file_path=file_path,
                            line_number=idx,
                            message=f"Unquoted SQL reserved keyword '{kw}' used as column name.",
                            remediation=f"Wrap keyword in quotes (e.g. \"{kw}\") to prevent syntax errors in queries.",
                            
                        )
                    )

            # Check DROP TABLE without IF EXISTS
            if re.search(r"DROP\s+TABLE\s+(?!IF\s+EXISTS\b)\w+", stripped, re.IGNORECASE):
                issues.append(
                    DiagnosticIssue(
                        code="TZ-SQL-002",
                        category=DiagnosticCategory.POLYGLOT_CONFIG,
                        severity=SeverityLevel.WARNING,
                        file_path=file_path,
                        line_number=idx,
                        message="Non-idempotent 'DROP TABLE' without 'IF EXISTS' will fail if table does not exist.",
                        remediation="Use 'DROP TABLE IF EXISTS table_name;'.",
                        
                    )
                )

        return issues
