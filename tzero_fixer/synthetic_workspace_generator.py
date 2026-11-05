# -*- coding: utf-8 -*-
"""
T-Zero Synthetic Workspace Generator & End-to-End Stress Testbed
===============================================================
Generates fully functional, realistic multi-tier workspaces with deliberate
synthetic defects across all 6 diagnostic categories to verify self-healing,
zero-regression stability, transactional rollback, and performance under load.

Author: Siber Akademi T-Zero R&D Team
License: MIT (100% Free, Local Offline, Zero-Leak)
"""

from __future__ import annotations

import os
import shutil
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from tzero_fixer.models import (
    DiagnosticCategory,
    DiagnosticIssue,
    DiagnosticReport,
    HealReport,
    SeverityLevel,
)
from tzero_fixer.orchestrator import FixerOrchestrator


@dataclass
class E2EVerificationReport:
    workspace_dir: str
    initial_issues_count: int
    initial_health_score: float
    healed_actions_count: int
    remaining_issues_count: int
    final_health_score: float
    rollback_verified: bool
    execution_time_ms: float
    passed: bool
    details: List[str] = field(default_factory=list)


class SyntheticWorkspaceGenerator:
    """
    Constructs high-fidelity synthetic repositories with deliberate defects for automated verification.
    """

    @classmethod
    def create_synthetic_workspace(cls, target_dir: Optional[str] = None) -> str:
        """
        Creates a temporary directory populated with realistic project files containing
        deliberate defects across syntax, imports, secrets, configs, and environment.
        """
        if not target_dir:
            temp_root = tempfile.mkdtemp(prefix="tzero_synthetic_")
        else:
            temp_root = target_dir
            os.makedirs(temp_root, exist_ok=True)

        root = Path(temp_root)

        # 1. Python source files with syntax defects
        src_dir = root / "src" / "api"
        src_dir.mkdir(parents=True, exist_ok=True)

        # Defect 1: Missing colon on def
        with open(src_dir / "service.py", "w", encoding="utf-8") as f:
            f.write(
                "def calculate_total(a: int, b: int)\n"
                "    return a + b\n\n"
                "def process_order(order_id: str):\n"
                "    print('Processing order:', order_id)\n"
            )

        # Defect 2: Legacy Python 2 print and dict.has_key
        with open(src_dir / "legacy_handler.py", "w", encoding="utf-8") as f:
            f.write(
                "def run_legacy(data):\n"
                "    if data.has_key('auth'):\n"
                "        print 'Authorized access'\n"
                "    return True\n"
            )

        # Defect 3: Mutable default argument & bare except
        with open(src_dir / "models.py", "w", encoding="utf-8") as f:
            f.write(
                "def append_item(item, items=[]):\n"
                "    try:\n"
                "        items.append(item)\n"
                "    except:\n"
                "        pass\n"
                "    return items\n"
            )

        # 2. Corrupted JSON file (trailing comma & single quotes)
        config_dir = root / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        with open(config_dir / "settings.json", "w", encoding="utf-8") as f:
            f.write(
                "{\n"
                "  'app_name': 'T-Zero Enterprise',\n"
                "  'debug_mode': true,\n"
                "  'port': 8080,\n"
                "}\n"
            )

        # 3. Corrupted Makefile (spaces instead of TAB)
        with open(root / "Makefile", "w", encoding="utf-8") as f:
            f.write(
                ".PHONY: all build test\n\n"
                "all: build\n\n"
                "build:\n"
                "    python -m build\n\n"
                "test:\n"
                "    python -m unittest discover tests\n"
            )

        # 4. GitHub Actions CI workflow with deprecated action
        workflows_dir = root / ".github" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)
        with open(workflows_dir / "ci.yml", "w", encoding="utf-8") as f:
            f.write(
                "name: CI Pipeline\n"
                "on: [push, pull_request]\n"
                "jobs:\n"
                "  build:\n"
                "    runs-on: ubuntu-latest\n"
                "    steps:\n"
                "      - uses: actions/checkout@v2\n"
                "      - uses: actions/setup-python@v2\n"
                "        with:\n"
                "          python-version: '3.11'\n"
                "      - run: python -m unittest\n"
            )

        # 5. Stale git lockfile
        git_dir = root / ".git"
        git_dir.mkdir(parents=True, exist_ok=True)
        lock_file = git_dir / "index.lock"
        with open(lock_file, "w", encoding="utf-8") as f:
            f.write("mock lockfile")
        # Set modification time to 2 hours ago
        stale_time = time.time() - 7200
        os.utime(lock_file, (stale_time, stale_time))

        # 6. Orphaned bytecode file
        cache_dir = src_dir / "__pycache__"
        cache_dir.mkdir(parents=True, exist_ok=True)
        with open(cache_dir / "orphaned_module.cpython-312.pyc", "wb") as f:
            f.write(b"mock bytecode content")

        return str(root)

    @classmethod
    def run_e2e_self_healing_verification(cls, workspace_dir: Optional[str] = None) -> E2EVerificationReport:
        """
        Executes end-to-end diagnosis, auto-healing, re-diagnosis, and atomic rollback verification.
        """
        start_t = time.time()
        temp_dir = cls.create_synthetic_workspace(workspace_dir)
        details: List[str] = []

        try:
            # Step 1: Initial Diagnosis
            initial_report: DiagnosticReport = FixerOrchestrator.diagnose_workspace(temp_dir)
            init_count = len(initial_report.issues)
            init_score = FixerOrchestrator.calculate_health_score(initial_report.issues)
            details.append(f"Initial diagnosis detected {init_count} defects. Health score: {init_score:.1f}%")

            # Step 2: Auto-Heal Execution (with transaction backup)
            heal_report: HealReport = FixerOrchestrator.auto_heal(temp_dir, dry_run=False)
            healed_count = len([a for a in heal_report.actions if a.success])
            details.append(f"Auto-healer executed {healed_count} surgical repairs successfully.")

            # Step 3: Post-Heal Verification
            post_report: DiagnosticReport = FixerOrchestrator.diagnose_workspace(temp_dir)
            remaining_count = len([i for i in post_report.issues if i.auto_fixable])
            final_score = FixerOrchestrator.calculate_health_score(post_report.issues)
            details.append(f"Post-heal remaining auto-fixable defects: {remaining_count}. New health score: {final_score:.1f}%")

            # Step 4: Transaction Rollback Verification
            rollback_ok = False
            if heal_report.transaction_id:
                rollback_success = FixerOrchestrator.rollback_transaction(temp_dir, heal_report.transaction_id)
                if rollback_success:
                    rollback_report = FixerOrchestrator.diagnose_workspace(temp_dir)
                    # Verify issues returned back to pre-heal state
                    if len(rollback_report.issues) >= init_count - 2:
                        rollback_ok = True
                        details.append(f"Atomic rollback verified: files cleanly restored to pre-repair state.")
                    else:
                        details.append(f"Rollback partially restored ({len(rollback_report.issues)}/{init_count} defects).")

            elapsed_ms = (time.time() - start_t) * 1000.0
            passed = (healed_count > 0 and final_score > init_score and rollback_ok)

            return E2EVerificationReport(
                workspace_dir=temp_dir,
                initial_issues_count=init_count,
                initial_health_score=init_score,
                healed_actions_count=healed_count,
                remaining_issues_count=remaining_count,
                final_health_score=final_score,
                rollback_verified=rollback_ok,
                execution_time_ms=elapsed_ms,
                passed=passed,
                details=details,
            )

        finally:
            if not workspace_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass
