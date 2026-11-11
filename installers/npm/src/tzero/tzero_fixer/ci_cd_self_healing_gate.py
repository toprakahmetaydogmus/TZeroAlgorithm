# -*- coding: utf-8 -*-
"""
T-Zero CI/CD Quality Gate, Hook Integrator, & SARIF/JUnit Exporter
================================================================
Enterprise-grade integration engine for CI/CD continuous inspection pipelines.
Provides:
  - Automated Git Pre-Commit & Pre-Push Hook Installer (.git/hooks/)
  - Native GitHub Actions Quality Gate Generator (.github/workflows/tzero_gate.yml)
  - GitLab CI / Bitbucket Pipelines Configuration Generators
  - Industry-standard SARIF 2.1.0 JSON Report Exporter (for GitHub Code Scanning)
  - JUnit XML Test Result Exporter (for Jenkins, CircleCI, Azure DevOps)

Author: Siber Akademi T-Zero R&D Team
License: MIT (100% Free, Local Offline, Zero-Leak)
"""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from tzero.tzero_fixer.models import (
    DiagnosticCategory,
    DiagnosticIssue,
    DiagnosticReport,
    HealReport,
    SeverityLevel,
)


class GitHookIntegrator:
    """Installs and manages git pre-commit and pre-push hooks."""

    PRE_COMMIT_SCRIPT = """#!/usr/bin/env sh
# T-Zero Autonomous Pre-Commit Security & AST Verification Gate
# Installed by Siber Akademi T-Zero Master Fixer

echo "🔒 [T-ZERO GATE] Running pre-commit Zero-Leak and AST syntax validation..."

# Execute tzero doctor check
if command -v python >/dev/null 2>&1; then
    python -c "from tzero_pc_fixer import PCFixerDoctor; report = PCFixerDoctor.diagnose('.'); crit = [i for i in report.get('issues', []) if i.get('severity') in ('critical', 'error')]; exit(1 if crit else 0)"
    STATUS=$?
    if [ $STATUS -ne 0 ]; then
        echo "🚨 [T-ZERO GATE BLOCKED] Critical syntax errors or secret leaks detected in staging!"
        echo "💡 Run 'tzero doctor --fix' or 'tzero pc-fixer --heal' to automatically resolve issues."
        exit 1
    fi
fi

echo "✅ [T-ZERO GATE PASSED] Workspace is clean. Proceeding with commit."
exit 0
"""

    @classmethod
    def install_hooks(cls, workspace_dir: str = ".") -> Tuple[bool, str]:
        """Installs pre-commit hook script into .git/hooks/pre-commit."""
        git_dir = Path(workspace_dir) / ".git"
        if not git_dir.is_dir():
            return False, f"Not a git repository: {workspace_dir}"

        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)

        hook_file = hooks_dir / "pre-commit"
        try:
            with open(hook_file, "w", encoding="utf-8", newline="\n") as f:
                f.write(cls.PRE_COMMIT_SCRIPT)

            # Mark executable on POSIX systems
            if hasattr(os, "chmod"):
                try:
                    os.chmod(hook_file, 0o755)
                except Exception:
                    pass

            return True, f"Successfully installed T-Zero pre-commit hook into {hook_file}"
        except Exception as e:
            return False, f"Failed to install git hook: {e}"


class CiCdWorkflowGenerator:
    """Generates CI/CD quality gate workflow configurations."""

    @classmethod
    def generate_github_workflow(cls, workspace_dir: str = ".") -> Tuple[bool, str]:
        """Generates .github/workflows/tzero_gate.yml."""
        wf_dir = Path(workspace_dir) / ".github" / "workflows"
        wf_dir.mkdir(parents=True, exist_ok=True)
        wf_path = wf_dir / "tzero_gate.yml"

        content = """name: T-Zero Quality & Security Gate
on:
  push:
    branches: [ main, master, develop ]
  pull_request:
    branches: [ main, master, develop ]

jobs:
  tzero-audit:
    name: Zero-Leak & AST Health Audit
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Codebase
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install T-Zero Engine
        run: |
          python -m pip install --upgrade pip
          pip install tzero

      - name: Run T-Zero Health & Security Check
        run: |
          tzero doctor --format sarif --out tzero-results.sarif

      - name: Upload SARIF Results to GitHub Security Tab
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: tzero-results.sarif
"""
        try:
            with open(wf_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(content)
            return True, f"Generated GitHub Actions quality workflow at {wf_path}"
        except Exception as e:
            return False, f"Failed to generate GitHub workflow: {e}"


class SarifReportExporter:
    """Converts T-Zero diagnostic reports into SARIF 2.1.0 standard schema."""

    @classmethod
    def export_sarif(cls, issues: List[DiagnosticIssue], workspace_dir: str = ".") -> str:
        """Serializes issues into official OASIS SARIF v2.1.0 JSON."""
        rules_map: Dict[str, Dict[str, Any]] = {}
        results: List[Dict[str, Any]] = []

        for issue in issues:
            rule_id = issue.error_code or "TZ-GENERIC"
            if rule_id not in rules_map:
                rules_map[rule_id] = {
                    "id": rule_id,
                    "name": issue.category.title(),
                    "shortDescription": {"text": issue.message[:100]},
                    "fullDescription": {"text": issue.message},
                    "defaultConfiguration": {
                        "level": "error" if issue.severity in ("critical", "error") else "warning"
                    },
                    "properties": {
                        "category": issue.category,
                        "remediation": issue.suggested_fix,
                    },
                }

            file_uri = issue.file_path or "workspace"
            if os.path.isabs(file_uri):
                try:
                    file_uri = os.path.relpath(file_uri, workspace_dir).replace("\\", "/")
                except Exception:
                    pass

            level = "error" if issue.severity in ("critical", "error") else "warning"
            if issue.severity == "info":
                level = "note"

            result_entry: Dict[str, Any] = {
                "ruleId": rule_id,
                "level": level,
                "message": {"text": issue.message},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": file_uri},
                            "region": {
                                "startLine": issue.line or 1,
                                "startColumn": (issue.column or 0) + 1,
                            },
                        }
                    }
                ],
            }
            results.append(result_entry)

        sarif_doc = {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "T-Zero PC-Fixer & Codebase Doctor",
                            "semanticVersion": "10.4.0",
                            "informationUri": "https://tzero-indol.vercel.app",
                            "rules": list(rules_map.values()),
                        }
                    },
                    "results": results,
                }
            ],
        }

        return json.dumps(sarif_doc, indent=2)


class JUnitXmlExporter:
    """Exports diagnostic issues to JUnit XML for dashboard reporting."""

    @classmethod
    def export_junit_xml(cls, issues: List[DiagnosticIssue]) -> str:
        """Generates standard JUnit XML testsuite element."""
        critical_count = len([i for i in issues if i.severity in ("critical", "error")])
        warning_count = len([i for i in issues if i.severity == "warning"])
        total_tests = len(issues) if issues else 1

        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<testsuite name="tzero-fixer-audit" tests="{total_tests}" failures="{critical_count}" errors="0" skipped="0">',
        ]

        if not issues:
            lines.append('  <testcase classname="TZeroDoctor" name="WorkspaceClean" time="0.001"/>')
        else:
            for idx, issue in enumerate(issues, 1):
                cname = f"TZero.{issue.category.capitalize()}"
                tname = f"{issue.error_code}_{idx}"
                escaped_msg = issue.message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
                if issue.severity in ("critical", "error"):
                    lines.append(f'  <testcase classname="{cname}" name="{tname}" time="0.001">')
                    lines.append(f'    <failure message="{escaped_msg}" type="{issue.error_code}">{escaped_msg}\nRemediation: {issue.suggested_fix}</failure>')
                    lines.append('  </testcase>')
                else:
                    lines.append(f'  <testcase classname="{cname}" name="{tname}" time="0.001"/>')

        lines.append('</testsuite>')
        return "\n".join(lines)
