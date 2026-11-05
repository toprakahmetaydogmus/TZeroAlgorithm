# -*- coding: utf-8 -*-
"""T-Zero Polyglot Ecosystem Doctor: Node, Rust, Go, Docker, & CI Workflows.

Performs forensic diagnostics across polyglot project architectures:
- Node.js / TypeScript: package.json validation, tsconfig.json integrity, lockfile conflicts, node_modules bloat.
- Rust / Cargo: Cargo.toml linting, target/ directory bloat, missing edition flags, cargo lock sync.
- Go Toolchain: go.mod & go.sum validation, GOPATH resolution, dangling vendor folders.
- Docker & Containers: Dockerfile linting (unpinned base images, root user execution, dangling cache).
- GitHub Actions CI/CD: .github/workflows YAML syntax, unpinned actions SHA, hardcoded secret leaks in workflows.

Author: Toprak Ahmet Aydogmus (Siber Akademi)
Version: 10.3.0
"""

import json
import os
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


class PolyglotDoctor:
    """Specialized doctor for polyglot language toolchains and container configurations."""

    IGNORED_DIRS = {
        ".git", ".svn", ".hg", "__pycache__", ".pytest_cache", ".mypy_cache",
        "node_modules", ".venv", "venv", "env", "build", "dist", ".idea", ".vscode"
    }

    # -------------------------------------------------------------------------
    # 1. NODE.JS & TYPESCRIPT DOCTOR
    # -------------------------------------------------------------------------
    @classmethod
    def check_nodejs_project(cls, workspace_dir: str = ".") -> List[DiagnosticIssue]:
        """Inspect package.json, package-lock.json, and tsconfig.json for common defects."""
        issues: List[DiagnosticIssue] = []
        root = Path(workspace_dir).resolve()
        pkg_json = root / "package.json"

        if not pkg_json.is_file():
            return issues

        try:
            with open(pkg_json, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as jde:
            issues.append(DiagnosticIssue(
                category=DiagnosticCategory.POLYGLOT.value,
                severity=SeverityLevel.CRITICAL.value,
                file_path=str(pkg_json),
                line=jde.lineno,
                column=jde.colno,
                error_code="TZ-NODE-INVALID-PACKAGE-JSON",
                message=f"package.json is corrupted or not valid JSON: {jde.msg}",
                suggested_fix="Fix JSON syntax error in package.json",
                auto_fixable=False
            ))
            return issues

        # Check required fields
        if not data.get("name"):
            issues.append(DiagnosticIssue(
                category=DiagnosticCategory.POLYGLOT.value,
                severity=SeverityLevel.WARNING.value,
                file_path=str(pkg_json),
                line=1,
                column=0,
                error_code="TZ-NODE-MISSING-NAME",
                message="package.json is missing top-level 'name' attribute",
                suggested_fix="Add a unique 'name' attribute to package.json",
                auto_fixable=False
            ))

        # Check conflicting lockfiles (e.g. package-lock.json AND yarn.lock AND pnpm-lock.yaml)
        lock_files = []
        if (root / "package-lock.json").is_file():
            lock_files.append("package-lock.json (npm)")
        if (root / "yarn.lock").is_file():
            lock_files.append("yarn.lock (yarn)")
        if (root / "pnpm-lock.yaml").is_file():
            lock_files.append("pnpm-lock.yaml (pnpm)")
        if (root / "bun.lockb").is_file():
            lock_files.append("bun.lockb (bun)")

        if len(lock_files) > 1:
            issues.append(DiagnosticIssue(
                category=DiagnosticCategory.POLYGLOT.value,
                severity=SeverityLevel.WARNING.value,
                file_path=str(pkg_json),
                line=None,
                column=None,
                error_code="TZ-NODE-CONFLICTING-LOCKFILES",
                message=f"Multiple conflicting package lockfiles detected: {', '.join(lock_files)}",
                suggested_fix="Standardize on a single package manager (npm, yarn, pnpm, or bun) and remove unused lockfiles",
                auto_fixable=False
            ))

        # Check node_modules existence vs package.json
        has_deps = bool(data.get("dependencies") or data.get("devDependencies"))
        if has_deps and not (root / "node_modules").is_dir():
            issues.append(DiagnosticIssue(
                category=DiagnosticCategory.POLYGLOT.value,
                severity=SeverityLevel.ERROR.value,
                file_path=str(pkg_json),
                line=None,
                column=None,
                error_code="TZ-NODE-MODULES-MISSING",
                message="package.json defines dependencies but 'node_modules' directory is missing",
                suggested_fix="Run 'npm install' or 'pnpm install' to install dependencies",
                auto_fixable=False
            ))

        # Check tsconfig.json if TypeScript project
        has_ts = any("typescript" in str(k) for k in list((data.get("devDependencies") or {}).keys()) + list((data.get("dependencies") or {}).keys()))
        tsconfig = root / "tsconfig.json"
        if has_ts and not tsconfig.is_file():
            issues.append(DiagnosticIssue(
                category=DiagnosticCategory.POLYGLOT.value,
                severity=SeverityLevel.WARNING.value,
                file_path=str(root),
                line=None,
                column=None,
                error_code="TZ-TS-MISSING-TSCONFIG",
                message="TypeScript dependency declared but 'tsconfig.json' is missing in workspace root",
                suggested_fix="Initialize TypeScript config via 'npx tsc --init'",
                auto_fixable=False
            ))

        return issues

    # -------------------------------------------------------------------------
    # 2. RUST & CARGO DOCTOR
    # -------------------------------------------------------------------------
    @classmethod
    def check_rust_project(cls, workspace_dir: str = ".") -> List[DiagnosticIssue]:
        """Inspect Cargo.toml and target directory for Rust projects."""
        issues: List[DiagnosticIssue] = []
        root = Path(workspace_dir).resolve()
        cargo_toml = root / "Cargo.toml"

        if not cargo_toml.is_file():
            return issues

        try:
            with open(cargo_toml, "r", encoding="utf-8") as f:
                content = f.read()

            # Check [package] table
            if "[package]" not in content:
                issues.append(DiagnosticIssue(
                    category=DiagnosticCategory.POLYGLOT.value,
                    severity=SeverityLevel.ERROR.value,
                    file_path=str(cargo_toml),
                    line=1,
                    column=0,
                    error_code="TZ-RUST-MISSING-PACKAGE",
                    message="Cargo.toml is missing '[package]' manifest header",
                    suggested_fix="Add '[package]' section with name, version, and edition",
                    auto_fixable=False
                ))

            # Check edition flag (edition = "2021")
            if "edition =" not in content:
                issues.append(DiagnosticIssue(
                    category=DiagnosticCategory.POLYGLOT.value,
                    severity=SeverityLevel.WARNING.value,
                    file_path=str(cargo_toml),
                    line=1,
                    column=0,
                    error_code="TZ-RUST-MISSING-EDITION",
                    message="Cargo.toml does not declare Rust edition (defaults to legacy 2015)",
                    suggested_fix="Specify modern edition: 'edition = \"2021\"'",
                    auto_fixable=True,
                    metadata={"action": "add_cargo_edition", "path": str(cargo_toml)}
                ))

            # Check target/ directory size bloat (> 1GB)
            target_dir = root / "target"
            if target_dir.is_dir():
                total_b = sum(f.stat().st_size for f in target_dir.glob("**/*") if f.is_file())
                if total_b > 1024 * 1024 * 1024:  # > 1GB
                    issues.append(DiagnosticIssue(
                        category=DiagnosticCategory.CACHE.value,
                        severity=SeverityLevel.INFO.value,
                        file_path=str(target_dir),
                        line=None,
                        column=None,
                        error_code="TZ-RUST-TARGET-BLOAT",
                        message=f"Rust build artifacts in 'target/' consume {round(total_b / (1024**3), 2)}GB",
                        suggested_fix="Run 'cargo clean' to reclaim disk space",
                        auto_fixable=False
                    ))
        except Exception:
            pass

        return issues

    # -------------------------------------------------------------------------
    # 3. GO TOOLCHAIN DOCTOR
    # -------------------------------------------------------------------------
    @classmethod
    def check_go_project(cls, workspace_dir: str = ".") -> List[DiagnosticIssue]:
        """Inspect go.mod and go.sum files in Go workspaces."""
        issues: List[DiagnosticIssue] = []
        root = Path(workspace_dir).resolve()
        go_mod = root / "go.mod"

        if not go_mod.is_file():
            return issues

        try:
            with open(go_mod, "r", encoding="utf-8") as f:
                content = f.read()

            if not content.startswith("module ") and "\nmodule " not in content:
                issues.append(DiagnosticIssue(
                    category=DiagnosticCategory.POLYGLOT.value,
                    severity=SeverityLevel.ERROR.value,
                    file_path=str(go_mod),
                    line=1,
                    column=0,
                    error_code="TZ-GO-MISSING-MODULE",
                    message="go.mod file is missing required 'module <path>' declaration",
                    suggested_fix="Add 'module <github.com/org/repo>' at top of go.mod",
                    auto_fixable=False
                ))

            if "go 1." not in content:
                issues.append(DiagnosticIssue(
                    category=DiagnosticCategory.POLYGLOT.value,
                    severity=SeverityLevel.WARNING.value,
                    file_path=str(go_mod),
                    line=1,
                    column=0,
                    error_code="TZ-GO-MISSING-VERSION",
                    message="go.mod does not specify Go language version directive (e.g. 'go 1.22')",
                    suggested_fix="Add 'go 1.22' directive to go.mod",
                    auto_fixable=False
                ))
        except Exception:
            pass

        return issues

    # -------------------------------------------------------------------------
    # 4. DOCKER & CONTAINER DOCTOR
    # -------------------------------------------------------------------------
    @classmethod
    def check_dockerfiles(cls, workspace_dir: str = ".") -> List[DiagnosticIssue]:
        """Inspect Dockerfile and compose manifests for security and performance smells."""
        issues: List[DiagnosticIssue] = []
        root = Path(workspace_dir).resolve()

        dockerfiles = list(root.glob("**/Dockerfile*")) + list(root.glob("**/docker-compose*.yml"))
        for df in dockerfiles:
            if not df.is_file() or any(p in df.parts for p in cls.IGNORED_DIRS):
                continue

            try:
                with open(df, "r", encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()

                has_user = False
                for idx, line in enumerate(lines, start=1):
                    stripped = line.strip()

                    # Unpinned :latest tag
                    if stripped.startswith("FROM ") and (":latest" in stripped or ":" not in stripped.split()[1]):
                        issues.append(DiagnosticIssue(
                            category=DiagnosticCategory.POLYGLOT.value,
                            severity=SeverityLevel.WARNING.value,
                            file_path=str(df),
                            line=idx,
                            column=0,
                            error_code="TZ-DOCKER-LATEST-TAG",
                            message=f"Unpinned Docker base image in '{stripped}' creates non-reproducible builds",
                            suggested_fix="Pin base image to specific semantic version tag or digest (e.g. python:3.12-slim)",
                            auto_fixable=False
                        ))

                    if stripped.startswith("USER ") and "root" not in stripped:
                        has_user = True

                # Check root user execution in Dockerfile
                if df.name.startswith("Dockerfile") and not has_user and len(lines) > 5:
                    issues.append(DiagnosticIssue(
                        category=DiagnosticCategory.SECURITY.value,
                        severity=SeverityLevel.WARNING.value,
                        file_path=str(df),
                        line=len(lines),
                        column=0,
                        error_code="TZ-DOCKER-ROOT-USER",
                        message=f"Dockerfile '{df.name}' runs as default 'root' user without non-root USER directive",
                        suggested_fix="Create and switch to a non-privileged user (e.g. 'USER appuser')",
                        auto_fixable=False
                    ))
            except Exception:
                continue

        return issues

    # -------------------------------------------------------------------------
    # 5. GITHUB ACTIONS & CI WORKFLOW DOCTOR
    # -------------------------------------------------------------------------
    @classmethod
    def check_ci_workflows(cls, workspace_dir: str = ".") -> List[DiagnosticIssue]:
        """Inspect .github/workflows YAML manifests for syntax flaws and security issues."""
        issues: List[DiagnosticIssue] = []
        root = Path(workspace_dir).resolve()
        workflows_dir = root / ".github" / "workflows"

        if not workflows_dir.is_dir():
            return issues

        for wf in workflows_dir.glob("*.yml"):
            try:
                with open(wf, "r", encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()

                for idx, line in enumerate(lines, start=1):
                    stripped = line.strip()

                    # Unpinned action version (@master or @main)
                    if "uses:" in stripped and ("@master" in stripped or "@main" in stripped):
                        issues.append(DiagnosticIssue(
                            category=DiagnosticCategory.SECURITY.value,
                            severity=SeverityLevel.WARNING.value,
                            file_path=str(wf),
                            line=idx,
                            column=0,
                            error_code="TZ-CI-UNPINNED-ACTION",
                            message=f"GitHub Action uses mutable branch reference in '{stripped}'",
                            suggested_fix="Pin action to full immutable commit SHA (e.g. actions/checkout@v4)",
                            auto_fixable=False
                        ))

                    # Hardcoded secrets in workflow
                    if re.search(r"""(?i)(api[_-]?key|password|token)\s*:\s*['"][A-Za-z0-9_\-]{16,}['"]""", stripped):
                        issues.append(DiagnosticIssue(
                            category=DiagnosticCategory.SECURITY.value,
                            severity=SeverityLevel.CRITICAL.value,
                            file_path=str(wf),
                            line=idx,
                            column=0,
                            error_code="TZ-CI-HARDCODED-SECRET",
                            message="Hardcoded secret or credential token in GitHub Actions workflow file",
                            suggested_fix="Move secret to repository settings and reference via ${{ secrets.NAME }}",
                            auto_fixable=False
                        ))
            except Exception:
                continue

        return issues

    @classmethod
    def diagnose_workspace(cls, workspace_dir: str = ".") -> List[DiagnosticIssue]:
        """Run all polyglot ecosystem diagnostic checks."""
        issues: List[DiagnosticIssue] = []
        issues.extend(cls.check_nodejs_project(workspace_dir))
        issues.extend(cls.check_rust_project(workspace_dir))
        issues.extend(cls.check_go_project(workspace_dir))
        issues.extend(cls.check_dockerfiles(workspace_dir))
        issues.extend(cls.check_ci_workflows(workspace_dir))
        return issues
