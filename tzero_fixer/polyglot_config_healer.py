# -*- coding: utf-8 -*-
"""T-Zero Polyglot Configuration & Environment Files Healer.

Performs forensic repair and hygiene checks on configuration files:
- JSON repair engine (strips trailing commas, single quotes, unquoted keys, and JS comments).
- Gitignore & Security hygiene (verifies .env, *.pem, *.key are in .gitignore).
- Gitattributes LF/CRLF normalizer (* text=auto eol=lf).
- EditorConfig generator and validator.

Author: Toprak Ahmet Aydogmus (Siber Akademi)
Version: 10.4.0
"""

import difflib
import json
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


class PolyglotConfigHealer:
    """Specialized repair engine for JSON, YAML, Gitignore, and Gitattributes files."""

    SENSITIVE_GITIGNORE_ENTRIES = [
        ".env",
        ".env.local",
        "*.pem",
        "*.key",
        "*.pfx",
        "*.p12",
        "id_rsa",
        "id_ed25519",
        ".tzero/fixer_backups/",
    ]

    # -------------------------------------------------------------------------
    # 1. JSON SURGICAL REPAIR ENGINE
    # -------------------------------------------------------------------------
    @classmethod
    def heal_json_string(cls, content: str) -> Any:
        """Helper to repair trailing commas and single quotes in JSON strings."""
        @dataclass
        class JsonHealResult:
            original_content: str
            repaired_content: str
            changed: bool

        changed, repaired = cls.repair_json_text(content)
        return JsonHealResult(
            original_content=content,
            repaired_content=repaired,
            changed=changed,
        )

    @classmethod
    def repair_json_text(cls, text: str) -> Tuple[bool, str]:
        """Surgically repair trailing commas, single quotes, and comments in JSON."""
        repaired = text

        # Strip line comments // ...
        repaired = re.sub(r"^\s*//.*$", "", repaired, flags=re.MULTILINE)
        # Strip block comments /* ... */
        repaired = re.sub(r"/\*.*?\*/", "", repaired, flags=re.DOTALL)

        # Convert single quotes to double quotes (around keys/values)
        repaired = re.sub(r"\'([^\'\\]*)\'", r'"\1"', repaired)

        # Strip trailing commas in objects: , } -> }
        repaired = re.sub(r",\s*(\})", r"\1", repaired)
        # Strip trailing commas in arrays: , ] -> ]
        repaired = re.sub(r",\s*(\])", r"\1", repaired)

        try:
            json.loads(repaired)
            return True, repaired
        except Exception:
            return False, text

    @classmethod
    def check_json_files(cls, workspace_dir: str = ".") -> List[DiagnosticIssue]:
        """Inspect all JSON files in workspace for syntax errors and trailing commas."""
        issues: List[DiagnosticIssue] = []
        root = Path(workspace_dir).resolve()

        for jf in root.glob("**/*.json"):
            if not jf.is_file() or any(p in jf.parts for p in (".git", "node_modules", ".venv", "venv", "dist", "build")):
                continue

            try:
                with open(jf, "r", encoding="utf-8") as f:
                    content = f.read()
                json.loads(content)
            except json.JSONDecodeError as jde:
                can_heal, _ = cls.repair_json_text(content)
                issues.append(DiagnosticIssue(
                    category=DiagnosticCategory.POLYGLOT.value,
                    severity=SeverityLevel.ERROR.value,
                    file_path=str(jf),
                    line=jde.lineno,
                    column=jde.colno,
                    error_code="TZ-JSON-SYNTAX-ERROR",
                    message=f"JSON syntax error in {jf.name}: {jde.msg}",
                    suggested_fix="Surgically heal trailing commas, comments, and quotes" if can_heal else "Fix JSON structure",
                    auto_fixable=can_heal,
                    metadata={"action": "repair_json_file", "path": str(jf)}
                ))
            except Exception:
                continue

        return issues

    # -------------------------------------------------------------------------
    # 2. GITIGNORE HYGIENE DOCTOR
    # -------------------------------------------------------------------------
    @classmethod
    def check_gitignore_hygiene(cls, workspace_dir: str = ".") -> List[DiagnosticIssue]:
        """Verify .gitignore exists and contains critical secret patterns (.env, *.key)."""
        issues: List[DiagnosticIssue] = []
        root = Path(workspace_dir).resolve()
        gi_file = root / ".gitignore"

        if not gi_file.is_file():
            issues.append(DiagnosticIssue(
                category=DiagnosticCategory.SECURITY.value,
                severity=SeverityLevel.ERROR.value,
                file_path=str(root),
                line=None,
                column=None,
                error_code="TZ-GIT-MISSING-GITIGNORE",
                message="No '.gitignore' file found in workspace root (risk of committing secrets)",
                suggested_fix="Generate comprehensive .gitignore with .env and secret patterns",
                auto_fixable=True,
                metadata={"action": "create_gitignore", "path": str(gi_file)}
            ))
            return issues

        try:
            with open(gi_file, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            lines = set(line.strip() for line in content.splitlines() if line.strip())

            missing_entries = []
            for entry in cls.SENSITIVE_GITIGNORE_ENTRIES:
                if entry not in lines and not any(l.startswith(entry) for l in lines):
                    missing_entries.append(entry)

            if missing_entries:
                issues.append(DiagnosticIssue(
                    category=DiagnosticCategory.SECURITY.value,
                    severity=SeverityLevel.WARNING.value,
                    file_path=str(gi_file),
                    line=1,
                    column=0,
                    error_code="TZ-GIT-UNPROTECTED-SECRETS",
                    message=f".gitignore is missing critical secret patterns: {', '.join(missing_entries[:4])}",
                    suggested_fix=f"Append {', '.join(missing_entries)} to .gitignore",
                    auto_fixable=True,
                    metadata={"action": "append_gitignore_entries", "entries": missing_entries, "path": str(gi_file)}
                ))
        except Exception:
            pass

        return issues

    # -------------------------------------------------------------------------
    # 3. GITATTRIBUTES LF/CRLF NORMALIZER
    # -------------------------------------------------------------------------
    @classmethod
    def check_gitattributes(cls, workspace_dir: str = ".") -> List[DiagnosticIssue]:
        """Verify .gitattributes exists to prevent cross-platform CRLF/LF chaos."""
        issues: List[DiagnosticIssue] = []
        root = Path(workspace_dir).resolve()
        ga_file = root / ".gitattributes"

        if not ga_file.is_file():
            issues.append(DiagnosticIssue(
                category=DiagnosticCategory.ENVIRONMENT.value,
                severity=SeverityLevel.INFO.value,
                file_path=str(ga_file),
                line=None,
                column=None,
                error_code="TZ-GIT-MISSING-GITATTRIBUTES",
                message="No '.gitattributes' found; cross-platform line endings (CRLF vs LF) may drift",
                suggested_fix="Generate standard .gitattributes ('* text=auto eol=lf')",
                auto_fixable=True,
                metadata={"action": "create_gitattributes", "path": str(ga_file)}
            ))

        return issues

    @classmethod
    def diagnose_workspace(cls, workspace_dir: str = ".") -> List[DiagnosticIssue]:
        """Run all polyglot configuration and git hygiene audits."""
        issues: List[DiagnosticIssue] = []
        issues.extend(cls.check_json_files(workspace_dir))
        issues.extend(cls.check_gitignore_hygiene(workspace_dir))
        issues.extend(cls.check_gitattributes(workspace_dir))
        return issues

    @classmethod
    def execute_config_heals(cls, issues: List[DiagnosticIssue], dry_run: bool = False) -> List[HealAction]:
        """Execute repairs for JSON files, .gitignore, and .gitattributes."""
        actions: List[HealAction] = []

        for issue in issues:
            action_type = issue.metadata.get("action")
            file_p = issue.metadata.get("path")
            if not issue.auto_fixable or not action_type or not file_p:
                continue

            t0 = time.time()
            p = Path(file_p)

            try:
                # 1. Repair JSON file
                if action_type == "repair_json_file" and p.is_file():
                    with open(p, "r", encoding="utf-8", errors="replace") as f:
                        content = f.read()
                    success, rep = cls.repair_json_text(content)
                    if success and rep != content:
                        diff = "".join(difflib.unified_diff(
                            content.splitlines(keepends=True),
                            rep.splitlines(keepends=True),
                            fromfile="before.json",
                            tofile="after.json"
                        ))
                        if not dry_run:
                            with open(p, "w", encoding="utf-8", newline="\n") as f:
                                f.write(rep)
                        actions.append(HealAction(
                            category=DiagnosticCategory.POLYGLOT.value,
                            action_type=action_type,
                            file_path=file_p,
                            description=f"Surgically repaired JSON syntax in {p.name}",
                            success=True,
                            diff=diff,
                            duration_ms=round((time.time() - t0) * 1000, 2)
                        ))

                # 2. Create .gitignore
                elif action_type == "create_gitignore":
                    entries = ["# T-Zero Autonomous Security Gitignore", "__pycache__/", "*.pyc", ".venv/", "venv/", "node_modules/", "dist/", "build/"] + cls.SENSITIVE_GITIGNORE_ENTRIES
                    content = "\n".join(entries) + "\n"
                    if not dry_run:
                        with open(p, "w", encoding="utf-8", newline="\n") as f:
                            f.write(content)
                    actions.append(HealAction(
                        category=DiagnosticCategory.SECURITY.value,
                        action_type=action_type,
                        file_path=file_p,
                        description="Generated secure .gitignore protecting .env and key files",
                        success=True,
                        duration_ms=round((time.time() - t0) * 1000, 2)
                    ))

                # 3. Append to .gitignore
                elif action_type == "append_gitignore_entries":
                    missing = issue.metadata.get("entries", [])
                    if missing:
                        append_str = "\n# T-Zero Security Guard Protections\n" + "\n".join(missing) + "\n"
                        if not dry_run:
                            with open(p, "a", encoding="utf-8") as f:
                                f.write(append_str)
                        actions.append(HealAction(
                            category=DiagnosticCategory.SECURITY.value,
                            action_type=action_type,
                            file_path=file_p,
                            description=f"Appended {len(missing)} security patterns ({', '.join(missing[:3])}) to .gitignore",
                            success=True,
                            duration_ms=round((time.time() - t0) * 1000, 2)
                        ))

                # 4. Create .gitattributes
                elif action_type == "create_gitattributes":
                    content = (
                        "# T-Zero Standard Gitattributes - Normalize LF Line Endings\n"
                        "* text=auto eol=lf\n"
                        "*.py text eol=lf\n"
                        "*.json text eol=lf\n"
                        "*.md text eol=lf\n"
                        "*.yml text eol=lf\n"
                        "*.yaml text eol=lf\n"
                        "*.sh text eol=lf\n"
                        "*.bat text eol=crlf\n"
                        "*.ps1 text eol=crlf\n"
                    )
                    if not dry_run:
                        with open(p, "w", encoding="utf-8", newline="\n") as f:
                            f.write(content)
                    actions.append(HealAction(
                        category=DiagnosticCategory.ENVIRONMENT.value,
                        action_type=action_type,
                        file_path=file_p,
                        description="Created .gitattributes to ensure cross-platform LF line ending consistency",
                        success=True,
                        duration_ms=round((time.time() - t0) * 1000, 2)
                    ))
            except Exception as e:
                actions.append(HealAction(
                    category=DiagnosticCategory.POLYGLOT.value,
                    action_type=action_type,
                    file_path=file_p,
                    description=f"Failed configuration remediation: {e}",
                    success=False,
                    duration_ms=round((time.time() - t0) * 1000, 2)
                ))

        return actions
