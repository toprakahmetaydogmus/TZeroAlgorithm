# -*- coding: utf-8 -*-
"""
T-Zero Polyglot Build, Container, & Infrastructure Healer
========================================================
Specialized AST & syntax healer for cross-language build tools, Dockerfiles,
Makefiles, container configurations, web server rules, and multi-ecosystem manifests.

Key Capabilities:
  - Dockerfile best-practice auditor & .dockerignore generator
  - Makefile tab-vs-space indentation healer (eliminates 'missing separator' errors)
  - Makefile .PHONY target generator
  - Nginx / Caddy reverse proxy syntax and semicolon validator
  - Rust Cargo.toml & Go go.mod basic syntax integrity checkers

Author: Siber Akademi T-Zero R&D Team
Version: 10.5.0 | 100% Free & Local Offline | Zero-Leak Certified
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from tzero_fixer.models import (
    DiagnosticCategory,
    DiagnosticIssue,
    HealAction,
    SeverityLevel,
)


class PolyglotBuildHealer:
    """Surgeon for polyglot build scripts, container files, and infrastructure recipes."""

    @classmethod
    def diagnose_workspace(cls, workspace_path: str) -> List[DiagnosticIssue]:
        """Audit build and container files across the workspace."""
        issues: List[DiagnosticIssue] = []
        root = Path(workspace_path).resolve()

        # 1. Dockerfile check
        for dockerfile in root.glob("**/Dockerfile*"):
            if dockerfile.is_file() and not cls._is_ignored(dockerfile):
                issues.extend(cls._audit_dockerfile(dockerfile, root))

        # 2. Makefile check
        for makefile in root.glob("**/Makefile*"):
            if makefile.is_file() and not cls._is_ignored(makefile):
                issues.extend(cls._audit_makefile(makefile))

        # 3. Nginx / Caddy conf check
        for conf in root.glob("**/*.conf"):
            if conf.is_file() and not cls._is_ignored(conf):
                issues.extend(cls._audit_webserver_conf(conf))

        # 4. Cargo.toml check
        for cargo in root.glob("**/Cargo.toml"):
            if cargo.is_file() and not cls._is_ignored(cargo):
                issues.extend(cls._audit_cargo_toml(cargo))

        # 5. go.mod check
        for gopkg in root.glob("**/go.mod"):
            if gopkg.is_file() and not cls._is_ignored(gopkg):
                issues.extend(cls._audit_go_mod(gopkg))

        return issues

    @classmethod
    def _is_ignored(cls, p: Path) -> bool:
        """Check if path is inside ignored VCS, venv, or build folders."""
        parts = p.parts
        ignored_names = {".git", ".venv", "venv", "node_modules", "dist", "build", ".tox", "__pycache__"}
        return any(part in ignored_names for part in parts)

    @classmethod
    def _audit_dockerfile(cls, dockerfile: Path, root: Path) -> List[DiagnosticIssue]:
        """Audit Dockerfile for best practices and check for .dockerignore."""
        issues: List[DiagnosticIssue] = []
        try:
            content = dockerfile.read_text(encoding="utf-8", errors="replace")
            lines = content.splitlines()
        except Exception:
            return issues

        # Check for missing .dockerignore in directory
        dockerignore = dockerfile.parent / ".dockerignore"
        if not dockerignore.is_file():
            issues.append(DiagnosticIssue(
                category=DiagnosticCategory.WORKSPACE,
                severity=SeverityLevel.WARNING,
                description=f"Dockerfile in '{dockerfile.parent.name}' lacks a '.dockerignore' file (unnecessary files like .git or .venv will bloat context)",
                file_path=str(dockerfile),
                suggested_fix="Generate optimized .dockerignore to exclude git, venv, cache, and build artifacts",
                metadata={"issue_type": "missing_dockerignore", "target_dir": str(dockerfile.parent)},
            ))

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()

            # FROM :latest warning
            if stripped.startswith("FROM ") and ":latest" in stripped:
                issues.append(DiagnosticIssue(
                    category=DiagnosticCategory.WORKSPACE,
                    severity=SeverityLevel.INFO,
                    description=f"Dockerfile uses unpinned ':latest' base image: '{stripped}'",
                    file_path=str(dockerfile),
                    line_number=idx,
                    suggested_fix="Pin base image to specific digest or version tag for deterministic builds",
                    metadata={"issue_type": "unpinned_docker_image"},
                ))

            # ADD instead of COPY
            if stripped.startswith("ADD ") and not ("://" in stripped or stripped.endswith(".tar.gz") or stripped.endswith(".tgz")):
                issues.append(DiagnosticIssue(
                    category=DiagnosticCategory.WORKSPACE,
                    severity=SeverityLevel.INFO,
                    description=f"Using 'ADD' instead of 'COPY' for simple local file copy: '{stripped}'",
                    file_path=str(dockerfile),
                    line_number=idx,
                    suggested_fix="Replace 'ADD' with 'COPY' for local files as per Dockerfile best practices",
                    metadata={"issue_type": "docker_add_to_copy", "line_num": idx},
                ))

            # apt-get install without cleanup
            if "apt-get install" in stripped and "rm -rf /var/lib/apt/lists" not in stripped and not stripped.endswith("\\"):
                issues.append(DiagnosticIssue(
                    category=DiagnosticCategory.WORKSPACE,
                    severity=SeverityLevel.WARNING,
                    description=f"apt-get install without cache cleanup in same RUN layer: '{stripped}'",
                    file_path=str(dockerfile),
                    line_number=idx,
                    suggested_fix="Append '&& rm -rf /var/lib/apt/lists/*' to reduce container image footprint",
                    metadata={"issue_type": "docker_apt_cleanup"},
                ))

        return issues

    @classmethod
    def _audit_makefile(cls, makefile: Path) -> List[DiagnosticIssue]:
        """Audit Makefile for space vs tab indentation and missing .PHONY declarations."""
        issues: List[DiagnosticIssue] = []
        try:
            content = makefile.read_text(encoding="utf-8", errors="replace")
            lines = content.splitlines()
        except Exception:
            return issues

        in_rule = False
        space_indented_lines: List[int] = []
        targets: List[str] = []

        for idx, line in enumerate(lines, start=1):
            if not line.strip() or line.strip().startswith("#"):
                continue

            # Detect target rule
            target_match = re.match(r"^([a-zA-Z0-9_\-\.]+)\s*:\s*(.*)$", line)
            if target_match:
                in_rule = True
                tgt = target_match.group(1)
                if not tgt.startswith("."):
                    targets.append(tgt)
                continue

            # Recipe lines must start with TAB, not spaces
            if in_rule:
                if line.startswith("    ") or (line.startswith(" ") and not line.startswith("\t")):
                    space_indented_lines.append(idx)

        if space_indented_lines:
            issues.append(DiagnosticIssue(
                category=DiagnosticCategory.SYNTAX,
                severity=SeverityLevel.ERROR,
                description=f"Makefile contains {len(space_indented_lines)} recipe line(s) indented with spaces instead of tabs (causes '*** missing separator' error)",
                file_path=str(makefile),
                line_number=space_indented_lines[0],
                suggested_fix="Convert leading spaces on recipe lines to real tab (\\t) characters",
                metadata={"issue_type": "makefile_spaces_to_tabs", "lines": space_indented_lines},
            ))

        if targets and ".PHONY:" not in content:
            issues.append(DiagnosticIssue(
                category=DiagnosticCategory.WORKSPACE,
                severity=SeverityLevel.INFO,
                description="Makefile declares targets without '.PHONY' directive (can conflict with files named after targets)",
                file_path=str(makefile),
                suggested_fix=f"Declare targets as .PHONY: {', '.join(targets[:5])}",
                metadata={"issue_type": "makefile_missing_phony", "targets": targets},
            ))

        return issues

    @classmethod
    def _audit_webserver_conf(cls, conf_file: Path) -> List[DiagnosticIssue]:
        """Audit Nginx / reverse proxy config files for missing semicolons."""
        issues: List[DiagnosticIssue] = []
        try:
            content = conf_file.read_text(encoding="utf-8", errors="replace")
            lines = content.splitlines()
        except Exception:
            return issues

        # Only audit if it looks like an nginx/caddy configuration
        if "server {" not in content and "http {" not in content and "location " not in content:
            return issues

        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped.endswith("{") or stripped.endswith("}"):
                continue
            if not stripped.endswith(";"):
                issues.append(DiagnosticIssue(
                    category=DiagnosticCategory.SYNTAX,
                    severity=SeverityLevel.ERROR,
                    description=f"Missing terminating semicolon in Nginx directive: '{stripped}'",
                    file_path=str(conf_file),
                    line_number=idx,
                    suggested_fix="Append ';' to directive line",
                    metadata={"issue_type": "nginx_missing_semicolon", "line_num": idx},
                ))

        return issues

    @classmethod
    def _audit_cargo_toml(cls, cargo_file: Path) -> List[DiagnosticIssue]:
        """Audit Rust Cargo.toml for basic sections."""
        issues: List[DiagnosticIssue] = []
        try:
            content = cargo_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return issues

        if "[package]" not in content and "[workspace]" not in content:
            issues.append(DiagnosticIssue(
                category=DiagnosticCategory.DEPENDENCY,
                severity=SeverityLevel.ERROR,
                description="Cargo.toml is missing mandatory '[package]' or '[workspace]' header",
                file_path=str(cargo_file),
                suggested_fix="Add '[package]' table with name, version, and edition = '2021'",
                metadata={"issue_type": "cargo_missing_package"},
            ))

        return issues

    @classmethod
    def _audit_go_mod(cls, go_mod_file: Path) -> List[DiagnosticIssue]:
        """Audit Go go.mod for module declaration."""
        issues: List[DiagnosticIssue] = []
        try:
            content = go_mod_file.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return issues

        if not re.search(r"^module\s+\S+", content, re.MULTILINE):
            issues.append(DiagnosticIssue(
                category=DiagnosticCategory.DEPENDENCY,
                severity=SeverityLevel.ERROR,
                description="go.mod is missing mandatory 'module <path>' declaration",
                file_path=str(go_mod_file),
                suggested_fix="Declare module path on first line of go.mod",
                metadata={"issue_type": "go_missing_module"},
            ))

        return issues

    @classmethod
    def heal_issue(cls, issue: DiagnosticIssue, dry_run: bool = False) -> HealAction:
        """Autonomously heal polyglot build and container issues."""
        itype = issue.metadata.get("issue_type")
        file_path = issue.file_path

        if itype == "missing_dockerignore":
            target_dir = Path(issue.metadata.get("target_dir", "."))
            dignore = target_dir / ".dockerignore"
            if dry_run:
                return HealAction(issue=issue, success=True, details=f"[Dry-Run] Would create .dockerignore in {target_dir}")

            ignore_content = (
                "# T-Zero Autonomous Dockerignore\n"
                ".git\n"
                ".gitignore\n"
                ".venv\n"
                "venv/\n"
                "env/\n"
                "node_modules/\n"
                "__pycache__/\n"
                "*.pyc\n"
                "*.pyo\n"
                "dist/\n"
                "build/\n"
                "*.egg-info/\n"
                ".DS_Store\n"
                "Thumbs.db\n"
                ".env\n"
                ".env.local\n"
                "coverage/\n"
                ".pytest_cache/\n"
            )
            dignore.write_text(ignore_content, encoding="utf-8")
            return HealAction(issue=issue, success=True, details=f"Generated high-performance .dockerignore in '{target_dir.name}'")

        if itype == "makefile_spaces_to_tabs" and file_path:
            p = Path(file_path)
            if dry_run:
                return HealAction(issue=issue, success=True, details="[Dry-Run] Would convert recipe spaces to tabs in Makefile")

            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
            new_lines = []
            converted = 0
            in_rule = False

            for line in lines:
                if not line.strip() or line.strip().startswith("#"):
                    new_lines.append(line)
                    continue

                if re.match(r"^[a-zA-Z0-9_\-\.]+\s*:\s*.*$", line):
                    in_rule = True
                    new_lines.append(line)
                    continue

                if in_rule:
                    if line.startswith("    "):
                        new_lines.append("\t" + line[4:])
                        converted += 1
                        continue
                    elif line.startswith("  "):
                        new_lines.append("\t" + line.lstrip(" "))
                        converted += 1
                        continue

                new_lines.append(line)

            p.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
            return HealAction(issue=issue, success=True, details=f"Converted {converted} recipe lines from spaces to real tabs in Makefile")

        if itype == "makefile_missing_phony" and file_path:
            p = Path(file_path)
            targets = issue.metadata.get("targets", [])
            if dry_run:
                return HealAction(issue=issue, success=True, details=f"[Dry-Run] Would prepend .PHONY: {' '.join(targets)} to Makefile")

            content = p.read_text(encoding="utf-8", errors="replace")
            phony_line = f".PHONY: {' '.join(targets)}\n\n"
            p.write_text(phony_line + content, encoding="utf-8")
            return HealAction(issue=issue, success=True, details=f"Injected .PHONY target declarations into Makefile")

        if itype == "docker_add_to_copy" and file_path:
            p = Path(file_path)
            line_num = issue.metadata.get("line_num")
            if dry_run:
                return HealAction(issue=issue, success=True, details=f"[Dry-Run] Would replace ADD with COPY on line {line_num}")

            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
            if line_num and 1 <= line_num <= len(lines):
                lines[line_num - 1] = re.sub(r"^ADD\s+", "COPY ", lines[line_num - 1])
                p.write_text("\n".join(lines) + "\n", encoding="utf-8")
                return HealAction(issue=issue, success=True, details=f"Replaced 'ADD' with 'COPY' on line {line_num} of Dockerfile")

        return HealAction(issue=issue, success=False, details=f"No automated repair for issue type '{itype}'")

