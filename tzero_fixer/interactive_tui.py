# -*- coding: utf-8 -*-
"""T-Zero Autonomous Doctor Interactive Terminal Cockpit & TUI.

Provides high-impact ANSI terminal visualization:
- Visual health score gauges and dial meters.
- Multi-column toolchain status matrices.
- Colored syntax-highlighted diff hunk renderers.
- Interactive category filtering and self-healing menus.

Author: Toprak Ahmet Aydogmus (Siber Akademi)
Version: 10.3.0
"""

import os
import sys
from typing import Any, Dict, List, Optional

from .models import (
    DiagnosticIssue,
    DiagnosticReport,
    HealAction,
    HealReport,
    SeverityLevel,
)


class InteractiveFixerTUI:
    """Terminal UI renderer for T-Zero Autonomous Doctor."""

    @staticmethod
    def render_gauge(percentage: int, width: int = 30) -> str:
        """Render a colored ASCII health progress bar gauge."""
        fill = int(width * (percentage / 100))
        empty = width - fill
        if percentage >= 90:
            color = "\033[1;32m"  # Bold green
        elif percentage >= 70:
            color = "\033[1;33m"  # Bold yellow
        else:
            color = "\033[1;31m"  # Bold red

        bar = "█" * fill + "░" * empty
        return f"{color}[{bar}] {percentage}%\033[0m"

    @classmethod
    def render_cockpit(cls, diag: DiagnosticReport, heal: Optional[HealReport] = None):
        """Render full interactive cockpit view."""
        term_width = 80

        print("\033[36m" + "╔" + "═" * (term_width - 2) + "╗\033[0m")
        print("\033[36m║\033[0m\033[1;37m   ⚡ T-ZERO AUTONOMOUS PC-FIXER & CODEBASE DOCTOR COCKPIT   \033[0m" + " " * 18 + "\033[36m║\033[0m")
        print("\033[36m╠" + "═" * (term_width - 2) + "╣\033[0m")

        # Top summary row
        gauge = cls.render_gauge(diag.health_score_pct)
        print(f"\033[36m║\033[0m  Overall Health: {gauge:<38} \033[36m║\033[0m")
        print(f"\033[36m║\033[0m  Directory:      \033[33m{diag.target_dir[:58]:<58}\033[0m \033[36m║\033[0m")
        print(f"\033[36m║\033[0m  Platform:       \033[32m{diag.environment.os_release[:40]:<40}\033[0m (\033[35mv{diag.environment.python_version}\033[0m) \033[36m║\033[0m")
        print(f"\033[36m║\033[0m  Hardware:       \033[36m{diag.environment.cpu_cores} Cores\033[0m | \033[36m{diag.environment.available_ram_gb:.1f}GB / {diag.environment.total_ram_gb:.1f}GB Free RAM\033[0m" + " " * 15 + "\033[36m║\033[0m")
        print("\033[36m╠" + "═" * (term_width - 2) + "╣\033[0m")

        # Diagnostics matrix
        print("\033[36m║\033[0m  \033[1mDIAGNOSTIC METRICS BREAKDOWN\033[0m" + " " * 48 + "\033[36m║\033[0m")
        print(f"\033[36m║\033[0m    • Critical Faults:   \033[1;31m{diag.critical_count:<4}\033[0m │ Syntax Defects:   \033[31m{diag.syntax_errors:<4}\033[0m \033[36m║\033[0m")
        print(f"\033[36m║\033[0m    • Error Level:       \033[31m{diag.error_count:<4}\033[0m │ Missing Imports:  \033[33m{diag.missing_imports:<4}\033[0m \033[36m║\033[0m")
        print(f"\033[36m║\033[0m    • Warnings:          \033[33m{diag.warning_count:<4}\033[0m │ Security Leaks:   \033[1;31m{diag.security_leaks:<4}\033[0m \033[36m║\033[0m")
        print(f"\033[36m║\033[0m    • Code Smells:       \033[36m{diag.code_smells:<4}\033[0m │ Cache & Bytecode: \033[32m{diag.cache_issues:<4}\033[0m \033[36m║\033[0m")
        print(f"\033[36m║\033[0m    • Scanned Files:     \033[35m{diag.scanned_file_count:<4}\033[0m │ Scan Latency:     \033[35m{diag.scan_duration_ms}ms\033[0m" + " " * 9 + "\033[36m║\033[0m")

        # Healing section if present
        if heal:
            print("\033[36m╠" + "═" * (term_width - 2) + "╣\033[0m")
            print("\033[36m║\033[0m  \033[1;32m💉 AUTONOMOUS SELF-HEALING OUTCOME\033[0m" + " " * 42 + "\033[36m║\033[0m")
            print(f"\033[36m║\033[0m    • Transaction:     \033[35m{heal.transaction_id:<32}\033[0m \033[36m║\033[0m")
            print(f"\033[36m║\033[0m    • Issues Healed:   \033[1;32m{heal.issues_healed} / {heal.issues_detected}\033[0m ({'DRY-RUN PREVIEW' if heal.dry_run else 'COMMITTED TO DISK'}) \033[36m║\033[0m")
            print(f"\033[36m║\033[0m    • Score Boost:     \033[33m{heal.initial_health_score}%\033[0m -> \033[1;32m{heal.final_health_score}%\033[0m in \033[36m{heal.execution_duration_ms:.1f}ms\033[0m \033[36m║\033[0m")

        print("\033[36m╚" + "═" * (term_width - 2) + "╝\033[0m")

    @classmethod
    def render_diff(cls, diff_text: str):
        """Render a unified diff with ANSI syntax colors."""
        for line in diff_text.splitlines():
            if line.startswith("+"):
                print(f"\033[32m{line}\033[0m")
            elif line.startswith("-"):
                print(f"\033[31m{line}\033[0m")
            elif line.startswith("@@"):
                print(f"\033[35m{line}\033[0m")
            else:
                print(line)
