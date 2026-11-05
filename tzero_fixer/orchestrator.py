# -*- coding: utf-8 -*-
"""T-Zero Master Autonomous Orchestrator & Transactional Rollback Engine.

Coordinates all specialized doctor engines:
- OS & Hardware Doctor (OSDoctor)
- Virtualenv & Dependency Drift Doctor (VenvDoctor)
- AST Syntax Healer (ASTSyntaxHealer)
- Import Graph & Cycle Healer (ImportGraphHealer)
- Code Smells & Modernizer (CodeSmellsHealer)
- 100% Zero-Leak Security Guard (SecurityZeroLeakDoctor)

Features:
- Transactional file backups with atomic rollback (.tzero/fixer_backups/).
- Multi-pass convergence loop (diagnose -> heal -> verify AST -> converge).
- Unified ANSI terminal rendering and JSON / SARIF v2.1.0 report generation.

Author: Toprak Ahmet Aydogmus (Siber Akademi)
Version: 10.5.0
"""

import json
import os
import shutil
import sys
import time
import uuid
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .ast_syntax_healer import ASTSyntaxHealer
from .code_smells_healer import CodeSmellsHealer
from .git_advanced_surgeon import GitAdvancedSurgeon
from .hardware_and_disk_doctor import HardwareAndDiskSurgeon
from .import_graph_healer import ImportGraphHealer
from .models import (
    DiagnosticCategory,
    DiagnosticIssue,
    DiagnosticReport,
    EnvironmentSnapshot,
    HealAction,
    HealReport,
    RollbackManifest,
    SeverityLevel,
)
from .os_doctor import OSDoctor
from .packaging_abi_surgeon import PackagingAbiSurgeon
from .polyglot_build_healer import PolyglotBuildHealer
from .security_zero_leak import SecurityZeroLeakDoctor
from .venv_doctor import VenvDoctor

# Safe stdout on Windows
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


class FixerOrchestrator:
    """Master orchestrator for all diagnosis and autonomous self-healing operations."""

    BACKUP_ROOT = ".tzero/fixer_backups"

    @classmethod
    def create_transaction_backup(cls, workspace_dir: str, files_to_backup: Set[str]) -> RollbackManifest:
        """Create timestamped transactional backup directory for atomic rollback."""
        tx_id = f"tx_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        backup_dir = os.path.join(workspace_dir, cls.BACKUP_ROOT, tx_id)
        os.makedirs(backup_dir, exist_ok=True)

        manifest = RollbackManifest(
            transaction_id=tx_id,
            timestamp=time.time(),
            target_dir=str(Path(workspace_dir).resolve()),
            backup_dir=backup_dir,
            backed_up_files={}
        )

        for src_f in files_to_backup:
            if os.path.isfile(src_f):
                rel_f = os.path.relpath(src_f, workspace_dir).replace(os.sep, "_")
                dest_f = os.path.join(backup_dir, rel_f)
                shutil.copy2(src_f, dest_f)
                manifest.backed_up_files[src_f] = dest_f

        manifest_file = os.path.join(backup_dir, "manifest.json")
        manifest.save(manifest_file)
        return manifest

    @classmethod
    def rollback_transaction(cls, workspace_dir: str, transaction_id: str) -> bool:
        """Restore all original files from a previous transactional backup."""
        backup_dir = os.path.join(workspace_dir, cls.BACKUP_ROOT, transaction_id)
        manifest_file = os.path.join(backup_dir, "manifest.json")
        if not os.path.isfile(manifest_file):
            print(f"\033[31m[ERROR] Manifest not found for transaction '{transaction_id}'\033[0m")
            return False

        manifest = RollbackManifest.load(manifest_file)
        restored = 0
        for orig_p, backup_p in manifest.backed_up_files.items():
            if os.path.isfile(backup_p):
                shutil.copy2(backup_p, orig_p)
                restored += 1

        print(f"\033[32m✔ Successfully rolled back transaction {transaction_id} ({restored} files restored)\033[0m")
        return True

    @classmethod
    def calculate_health_score(cls, issues: List[DiagnosticIssue]) -> float:
        """Compute 0.0-100.0 overall health score based on issue counts and severity weights."""
        if not issues:
            return 100.0
        crit = sum(1 for i in issues if i.severity == SeverityLevel.CRITICAL.value)
        err = sum(1 for i in issues if i.severity == SeverityLevel.ERROR.value)
        warn = sum(1 for i in issues if i.severity == SeverityLevel.WARNING.value)
        info = sum(1 for i in issues if i.severity == SeverityLevel.INFO.value)

        penalty = (crit * 5.0) + (err * 3.0) + (warn * 1.0) + (info * 0.2)
        score = 100.0 / (1.0 + penalty * 0.02)
        return round(score, 1)

    @classmethod
    def diagnose_workspace(cls, workspace_dir: str = ".") -> DiagnosticReport:
        """Run complete, multi-category diagnostic sweep across the entire workspace."""
        t0 = time.time()
        root = Path(workspace_dir).resolve()
        issues: List[DiagnosticIssue] = []

        # 1. Environment & Tools
        env_snapshot = OSDoctor.capture_snapshot(workspace_dir)
        issues.extend(OSDoctor.check_windows_registry_settings())
        issues.extend(OSDoctor.check_path_environment())
        issues.extend(OSDoctor.check_file_locks_and_permissions(workspace_dir))
        issues.extend(OSDoctor.check_bytecode_and_temp_bloat(workspace_dir))

        # 2. Virtualenv & Dependencies
        issues.extend(VenvDoctor.diagnose(workspace_dir))

        # 3. Import Graph & Cycles
        issues.extend(ImportGraphHealer.diagnose_workspace(workspace_dir))

        # 4. Packaging, PEP 517 & ABI
        issues.extend(PackagingAbiSurgeon.diagnose_workspace(workspace_dir))

        # 5. Git VCS Integrity & Locks
        issues.extend(GitAdvancedSurgeon.diagnose_workspace(workspace_dir))

        # 6. Polyglot Build & Infrastructure
        issues.extend(PolyglotBuildHealer.diagnose_workspace(workspace_dir))

        # 4. File-by-file AST, Smells, Security
        scanned_files = 0
        for root_dir, dirs, files in os.walk(str(root)):
            dirs[:] = [d for d in dirs if d not in OSDoctor.IGNORED_DIRS]
            for file in files:
                if file.endswith(".py"):
                    full_p = os.path.join(root_dir, file)
                    scanned_files += 1
                    # Syntax & Encoding
                    issues.extend(ASTSyntaxHealer.diagnose_file(full_p))
                    # Code Smells
                    issues.extend(CodeSmellsHealer.diagnose_file(full_p))
                    # Security & Zero-Leak
                    issues.extend(SecurityZeroLeakDoctor.diagnose_file(full_p))

        # Tallies
        crit_c = sum(1 for i in issues if i.severity == SeverityLevel.CRITICAL.value)
        err_c = sum(1 for i in issues if i.severity == SeverityLevel.ERROR.value)
        warn_c = sum(1 for i in issues if i.severity == SeverityLevel.WARNING.value)
        info_c = sum(1 for i in issues if i.severity == SeverityLevel.INFO.value)

        syntax_c = sum(1 for i in issues if i.category == DiagnosticCategory.SYNTAX.value)
        import_c = sum(1 for i in issues if i.category == DiagnosticCategory.IMPORTS.value)
        env_c = sum(1 for i in issues if i.category == DiagnosticCategory.ENVIRONMENT.value)
        sec_c = sum(1 for i in issues if i.category == DiagnosticCategory.SECURITY.value)
        smell_c = sum(1 for i in issues if i.category in (DiagnosticCategory.SMELLS.value, DiagnosticCategory.PERFORMANCE.value))
        cache_c = sum(1 for i in issues if i.category in (DiagnosticCategory.CACHE.value, DiagnosticCategory.ENCODING.value))

        score = cls.calculate_health_score(issues)
        duration_ms = round((time.time() - t0) * 1000, 2)

        return DiagnosticReport(
            timestamp=time.time(),
            target_dir=str(root),
            health_score_pct=score,
            total_issues=len(issues),
            critical_count=crit_c,
            error_count=err_c,
            warning_count=warn_c,
            info_count=info_c,
            syntax_errors=syntax_c,
            missing_imports=import_c,
            env_issues=env_c,
            security_leaks=sec_c,
            code_smells=smell_c,
            cache_issues=cache_c,
            issues=issues,
            environment=env_snapshot,
            scan_duration_ms=duration_ms,
            scanned_file_count=scanned_files
        )

    @classmethod
    def auto_heal(cls, workspace_dir: str = ".", dry_run: bool = False, max_iterations: int = 3) -> HealReport:
        """Execute autonomous self-healing convergence loop across all categories."""
        t0 = time.time()
        initial_diag = cls.diagnose_workspace(workspace_dir)
        all_actions: List[HealAction] = []
        manifest = None

        if initial_diag.total_issues > 0 and not dry_run:
            # Gather files to backup
            files_to_backup: Set[str] = set()
            for issue in initial_diag.issues:
                if issue.file_path and os.path.isfile(issue.file_path):
                    files_to_backup.add(issue.file_path)
            if files_to_backup:
                manifest = cls.create_transaction_backup(workspace_dir, files_to_backup)

        current_issues = initial_diag.issues

        # Convergence passes
        for iteration in range(1, max_iterations + 1):
            if not current_issues:
                break

            pass_actions: List[HealAction] = []
            # 1. OS & Cache Heals
            pass_actions.extend(OSDoctor.execute_os_heals(current_issues, dry_run=dry_run))

            # 2. Virtualenv Heals
            pass_actions.extend(VenvDoctor.execute_venv_heals(current_issues, dry_run=dry_run))

            # 3. Syntax & Encoding Heals
            pass_actions.extend(ASTSyntaxHealer.execute_syntax_heals(current_issues, dry_run=dry_run))

            # 4. Import Heals
            pass_actions.extend(ImportGraphHealer.execute_import_heals(current_issues, dry_run=dry_run))

            # 5. Code Smell Heals
            pass_actions.extend(CodeSmellsHealer.execute_smell_heals(current_issues, dry_run=dry_run))

            # 6. Security Heals
            pass_actions.extend(SecurityZeroLeakDoctor.execute_security_heals(current_issues, workspace_dir, dry_run=dry_run))

            # 7. Packaging Heals
            for issue in [i for i in current_issues if i.metadata.get("issue_type") in ("missing_build_system", "broken_pyvenv_home", "stale_egg_info", "legacy_setup_py")]:
                pass_actions.append(PackagingAbiSurgeon.heal_issue(issue, dry_run=dry_run))

            # 8. Git VCS Heals
            for issue in [i for i in current_issues if i.metadata.get("issue_type") in ("stale_git_lock", "missing_gitattributes")]:
                pass_actions.append(GitAdvancedSurgeon.heal_issue(issue, dry_run=dry_run))

            # 9. Polyglot Build Heals
            for issue in [i for i in current_issues if i.metadata.get("issue_type") in ("missing_dockerignore", "makefile_spaces_to_tabs", "makefile_missing_phony", "docker_add_to_copy")]:
                pass_actions.append(PolyglotBuildHealer.heal_issue(issue, dry_run=dry_run))

            all_actions.extend(pass_actions)

            if dry_run or not pass_actions:
                break

            # Re-diagnose to verify convergence
            post_pass_diag = cls.diagnose_workspace(workspace_dir)
            current_issues = [i for i in post_pass_diag.issues if i.auto_fixable]

        final_diag = cls.diagnose_workspace(workspace_dir) if not dry_run else initial_diag
        duration_ms = round((time.time() - t0) * 1000, 2)
        healed_count = sum(1 for a in all_actions if a.success)

        return HealReport(
            timestamp=time.time(),
            target_dir=str(Path(workspace_dir).resolve()),
            transaction_id=manifest.transaction_id if manifest else "dry_run",
            initial_health_score=initial_diag.health_score_pct,
            final_health_score=final_diag.health_score_pct,
            issues_detected=initial_diag.total_issues,
            issues_healed=healed_count,
            dry_run=dry_run,
            actions=all_actions,
            backup_manifest=manifest,
            execution_duration_ms=duration_ms
        )

    @classmethod
    def render_cli(cls, diag: DiagnosticReport, heal: Optional[HealReport] = None):
        """Render high-contrast, beautiful ANSI terminal cockpit report."""
        print("=" * 80)
        print("\033[1;36m🩺 T-ZERO MASTER PC-FIXER & ENVIRONMENT AUTONOMOUS DOCTOR v10.5.0\033[0m")
        print("=" * 80)
        print(f"Target Directory: \033[33m{diag.target_dir}\033[0m")
        print(f"Host OS:          \033[32m{diag.environment.os_release}\033[0m (Arch: {diag.environment.python_architecture})")
        print(f"Python Runtime:   \033[32mv{diag.environment.python_version}\033[0m ({diag.environment.python_executable})")
        print(f"Virtualenv:       \033[32m{diag.environment.virtualenv_root or 'Global / System Python'}\033[0m")
        print(f"Hardware Stats:   \033[36m{diag.environment.cpu_cores} Cores\033[0m | \033[36m{diag.environment.available_ram_gb:.1f}GB / {diag.environment.total_ram_gb:.1f}GB Free RAM\033[0m")

        # Tools status
        tools_str = " ".join([
            f"\033[32m[✔ {t}]\033[0m" if s.available else f"\033[31m[✘ {t}]\033[0m"
            for t, s in diag.environment.tools.items()
        ])
        print(f"CLI Toolchain:    {tools_str}")

        score_color = "\033[1;32m" if diag.health_score_pct >= 90 else ("\033[1;33m" if diag.health_score_pct >= 70 else "\033[1;31m")
        print(f"Health Score:     {score_color}{diag.health_score_pct} / 100\033[0m "
              f"(\033[35m{diag.scanned_file_count} files scanned in {diag.scan_duration_ms}ms\033[0m)")
        print("-" * 80)

        if diag.total_issues == 0:
            print("\033[1;32m✨ Codebase and host environment are in 100% pristine condition! Zero defects found.\033[0m")
        else:
            print(f"Detected Issues: \033[1;31m{diag.total_issues}\033[0m "
                  f"(\033[1;31mCrit: {diag.critical_count}\033[0m, \033[31mErr: {diag.error_count}\033[0m, "
                  f"\033[33mWarn: {diag.warning_count}\033[0m, \033[36mInfo: {diag.info_count}\033[0m)")
            print(f"Breakdown:       Syntax: \033[31m{diag.syntax_errors}\033[0m | "
                  f"Imports: \033[33m{diag.missing_imports}\033[0m | "
                  f"Security: \033[1;31m{diag.security_leaks}\033[0m | "
                  f"Env: \033[35m{diag.env_issues}\033[0m | "
                  f"Cache: \033[36m{diag.cache_issues}\033[0m")
            print()

            for idx, issue in enumerate(diag.issues[:20], start=1):
                sev_color = "\033[1;31m" if issue.severity == "critical" else ("\033[31m" if issue.severity == "error" else "\033[33m")
                loc = issue.formatted_location
                print(f"  {idx:2d}. {sev_color}[{issue.severity.upper():<4}]\033[0m \033[1m{loc:<26}\033[0m {issue.message}")
                print(f"      \033[36mFix:\033[0m {issue.suggested_fix}")

            if len(diag.issues) > 20:
                print(f"  ... and {len(diag.issues) - 20} more diagnostic issues.")

        if heal:
            print("-" * 80)
            print("\033[1;32m💉 AUTONOMOUS SELF-HEALING EXECUTION RESULTS:\033[0m")
            print(f"  Transaction ID:   \033[35m{heal.transaction_id}\033[0m")
            print(f"  Issues Healed:    \033[32m{heal.issues_healed} / {heal.issues_detected}\033[0m")
            print(f"  Health Boost:     \033[33m{heal.initial_health_score}%\033[0m -> \033[1;32m{heal.final_health_score}%\033[0m")
            print(f"  Execution Time:   \033[36m{heal.execution_duration_ms:.2f} ms\033[0m")

            for a in heal.actions[:12]:
                status_icon = "\033[32m✔\033[0m" if a.success else "\033[31m✘\033[0m"
                print(f"  {status_icon} [{a.category.upper()}] {a.description}")
                if a.diff:
                    for dline in a.diff.splitlines()[:3]:
                        print(f"      \033[35m{dline}\033[0m")

            if len(heal.actions) > 12:
                print(f"  ... and {len(heal.actions) - 12} additional repairs.")

        print("=" * 80)
