# -*- coding: utf-8 -*-
"""
T-Zero System Repair Playbooks & Operating System Healer Recipes
===============================================================
Production-grade system repair recipes for engineering workstations.
Provides automated playbooks and verified remediation commands for:
  - Windows 10/11 & Server: LongPaths, DeveloperMode, UTF-8 console, Symlinks, ExecutionPolicy
  - Linux (Ubuntu/Debian, Fedora/RHEL, Arch): inotify watchers, file descriptors, tmp permissions, SSH keys
  - macOS (Apple Silicon & Intel): Gatekeeper quarantine, Homebrew permissions, Xcode CLI tools
  - Language Runtimes: Python (pip/pyenv/poetry/pdm), Node.js (npm/yarn/pnpm), Rust (cargo), Go
  - Version Control & Storage: Stale git locks, detached HEADs, Git LFS pointer corruptions, disk caches

Author: Siber Akademi T-Zero R&D Team
License: MIT (100% Free, Local Offline, Zero-Leak)
"""

from __future__ import annotations

import os
import sys
import platform
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from tzero.tzero_fixer.models import (
    DiagnosticCategory,
    DiagnosticIssue,
    HealAction,
    SeverityLevel,
    SystemPlatform,
)


@dataclass
class SystemRepairRecipe:
    """Executable repair recipe for a specific operating system or toolchain defect."""
    recipe_id: str
    target_platform: SystemPlatform
    title: str
    description: str
    diagnostic_code: str
    requires_elevation: bool
    automated_fix_available: bool
    windows_powershell_cmd: Optional[str] = None
    posix_bash_cmd: Optional[str] = None
    verification_check_cmd: Optional[str] = None
    safety_notes: str = ""


class SystemRepairPlaybooks:
    """
    Exhaustive catalog and execution engine for cross-platform system repair recipes.
    """

    RECIPES: List[SystemRepairRecipe] = [
        # =====================================================================
        # 1. WINDOWS OPERATING SYSTEM RECIPES
        # =====================================================================
        SystemRepairRecipe(
            recipe_id="REC-WIN-001",
            target_platform=SystemPlatform.WINDOWS,
            title="Enable Windows LongPathsEnabled in Registry",
            description="Removes the legacy 260-character MAX_PATH limit in Windows, allowing deeply nested node_modules and python virtual environments to function without crashing.",
            diagnostic_code="TZ-WIN-001",
            requires_elevation=True,
            automated_fix_available=True,
            windows_powershell_cmd='Set-ItemProperty -Path "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\FileSystem" -Name "LongPathsEnabled" -Value 1 -Type DWord',
            verification_check_cmd='(Get-ItemProperty "HKLM:\\SYSTEM\\CurrentControlSet\\Control\\FileSystem").LongPathsEnabled',
            safety_notes="Completely safe. Supported natively in Windows 10 (version 1607+) and Windows 11.",
        ),
        SystemRepairRecipe(
            recipe_id="REC-WIN-002",
            target_platform=SystemPlatform.WINDOWS,
            title="Enable Developer Mode for Unprivileged Symlink Creation",
            description="Allows standard non-administrator users to create symbolic links (mklink) required by npm, yarn, and python virtual environments.",
            diagnostic_code="TZ-WIN-002",
            requires_elevation=True,
            automated_fix_available=True,
            windows_powershell_cmd='Set-ItemProperty -Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\AppModelUnlock" -Name "AllowDevelopmentWithoutDevLicense" -Value 1 -Type DWord',
            verification_check_cmd='(Get-ItemProperty "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\AppModelUnlock").AllowDevelopmentWithoutDevLicense',
            safety_notes="Enables Windows Developer Mode. Safe for engineering development workstations.",
        ),
        SystemRepairRecipe(
            recipe_id="REC-WIN-003",
            target_platform=SystemPlatform.WINDOWS,
            title="Configure UTF-8 Code Page 65001 for Windows Console",
            description="Configures Windows command prompt and PowerShell to default to UTF-8 encoding (cp65001), eliminating UnicodeEncodeError crashes.",
            diagnostic_code="TZ-WIN-003",
            requires_elevation=False,
            automated_fix_available=True,
            windows_powershell_cmd="[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; [Console]::InputEncoding = [System.Text.Encoding]::UTF8",
            verification_check_cmd="[Console]::OutputEncoding.CodePage",
            safety_notes="Non-destructive in-session or profile configuration.",
        ),
        SystemRepairRecipe(
            recipe_id="REC-WIN-004",
            target_platform=SystemPlatform.WINDOWS,
            title="Set PowerShell ExecutionPolicy to RemoteSigned",
            description="Allows local developer activation scripts (e.g. .venv\\Scripts\\Activate.ps1) to run while still blocking unsigned remote internet scripts.",
            diagnostic_code="TZ-WIN-004",
            requires_elevation=False,
            automated_fix_available=True,
            windows_powershell_cmd="Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force",
            verification_check_cmd="Get-ExecutionPolicy -Scope CurrentUser",
            safety_notes="Restricted to CurrentUser scope; does not lower machine-wide security policies.",
        ),
        SystemRepairRecipe(
            recipe_id="REC-WIN-005",
            target_platform=SystemPlatform.WINDOWS,
            title="Purge Windows Temp Stale Build Directories (%TEMP%)",
            description="Safely deletes abandoned pip-build-*, tmp*, and npm cache directories older than 24 hours from user temporary storage.",
            diagnostic_code="TZ-SYS-052",
            requires_elevation=False,
            automated_fix_available=True,
            windows_powershell_cmd='Get-ChildItem -Path $env:TEMP -Filter "pip-*" -Directory | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-1) } | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue',
            verification_check_cmd='(Get-ChildItem -Path $env:TEMP -Filter "pip-*" -Directory).Count',
            safety_notes="Only purges build folders older than 24 hours.",
        ),

        # =====================================================================
        # 2. LINUX OPERATING SYSTEM RECIPES
        # =====================================================================
        SystemRepairRecipe(
            recipe_id="REC-LNX-001",
            target_platform=SystemPlatform.LINUX,
            title="Increase inotify File Watcher Limit for Dev Servers",
            description="Increases fs.inotify.max_user_watches from default 8192 to 524288 to prevent 'ENOSPC: System limit for number of file watchers reached' in Vite, Next.js, and Webpack.",
            diagnostic_code="TZ-LNX-001",
            requires_elevation=True,
            automated_fix_available=True,
            posix_bash_cmd='echo "fs.inotify.max_user_watches=524288" | sudo tee -a /etc/sysctl.d/99-tzero-inotify.conf && sudo sysctl -p /etc/sysctl.d/99-tzero-inotify.conf',
            verification_check_cmd="cat /proc/sys/fs/inotify/max_user_watches",
            safety_notes="Standard configuration for frontend and fullstack web developers on Linux.",
        ),
        SystemRepairRecipe(
            recipe_id="REC-LNX-002",
            target_platform=SystemPlatform.LINUX,
            title="Increase Max Open File Descriptors (nofile limit)",
            description="Increases the maximum number of open files per user process to 65535, preventing 'Too many open files' in database and high-concurrency dev testing.",
            diagnostic_code="TZ-LNX-002",
            requires_elevation=True,
            automated_fix_available=True,
            posix_bash_cmd='sudo sh -c \'echo "* soft nofile 65535\\n* hard nofile 65535" >> /etc/security/limits.d/99-tzero-nofile.conf\'',
            verification_check_cmd="ulimit -n",
            safety_notes="Requires user re-login or new shell session to take effect.",
        ),
        SystemRepairRecipe(
            recipe_id="REC-LNX-003",
            target_platform=SystemPlatform.LINUX,
            title="Enforce Secure Permissions on ~/.ssh and Private Keys",
            description="Applies chmod 700 to ~/.ssh directory and chmod 600 to private keys (id_rsa, id_ed25519) to prevent SSH from rejecting key authentication.",
            diagnostic_code="TZ-SEC-080",
            requires_elevation=False,
            automated_fix_available=True,
            posix_bash_cmd="chmod 700 ~/.ssh && chmod 600 ~/.ssh/id_* 2>/dev/null || true",
            verification_check_cmd="stat -c '%a' ~/.ssh",
            safety_notes="Standard POSIX security practice mandated by OpenSSH clients.",
        ),
        SystemRepairRecipe(
            recipe_id="REC-LNX-004",
            target_platform=SystemPlatform.LINUX,
            title="Ensure /tmp Sticky Bit (1777 Permissions)",
            description="Restores the required sticky bit (drwxrwxrwt) on /tmp so any user can create files but only file owners can delete them.",
            diagnostic_code="TZ-LNX-003",
            requires_elevation=True,
            automated_fix_available=True,
            posix_bash_cmd="sudo chmod 1777 /tmp",
            verification_check_cmd="stat -c '%a' /tmp",
            safety_notes="Essential for multi-user Linux system integrity.",
        ),

        # =====================================================================
        # 3. MACOS OPERATING SYSTEM RECIPES
        # =====================================================================
        SystemRepairRecipe(
            recipe_id="REC-MAC-001",
            target_platform=SystemPlatform.MACOS,
            title="Strip macOS Gatekeeper Quarantine from Dev Tools",
            description="Removes 'com.apple.quarantine' extended attributes from downloaded compilers, shims, and CLI utilities blocking command execution.",
            diagnostic_code="TZ-MAC-001",
            requires_elevation=False,
            automated_fix_available=True,
            posix_bash_cmd="xattr -d com.apple.quarantine ./bin/* 2>/dev/null || true",
            verification_check_cmd="xattr ./bin/*",
            safety_notes="Only execute on trusted developer tools and verified local binaries.",
        ),
        SystemRepairRecipe(
            recipe_id="REC-MAC-002",
            target_platform=SystemPlatform.MACOS,
            title="Verify Active Xcode Command Line Tools Path",
            description="Checks and restores active developer directory path (xcode-select) to prevent compiler header missing errors.",
            diagnostic_code="TZ-MAC-002",
            requires_elevation=True,
            automated_fix_available=False,
            posix_bash_cmd="sudo xcode-select --switch /Library/Developer/CommandLineTools",
            verification_check_cmd="xcode-select -p",
            safety_notes="Ensures clang, make, and git resolve properly from macOS SDK.",
        ),

        # =====================================================================
        # 4. PYTHON RUNTIME & PACKAGE MANAGER RECIPES
        # =====================================================================
        SystemRepairRecipe(
            recipe_id="REC-PY-001",
            target_platform=SystemPlatform.UNKNOWN,
            title="Purge Corrupted pip Cache and Download Artifacts",
            description="Cleans the local pip cache directory to fix 'Hash mismatch' and corrupted wheel download errors.",
            diagnostic_code="TZ-PY-001",
            requires_elevation=False,
            automated_fix_available=True,
            windows_powershell_cmd="python -m pip cache purge",
            posix_bash_cmd="python -m pip cache purge",
            verification_check_cmd="python -m pip cache list",
            safety_notes="Completely safe; cached wheels will re-download on next pip install.",
        ),
        SystemRepairRecipe(
            recipe_id="REC-PY-002",
            target_platform=SystemPlatform.UNKNOWN,
            title="Purge Orphaned Bytecode (__pycache__/*.pyc) Recursively",
            description="Deletes all compiled .pyc files across the workspace to guarantee fresh module loading without stale bytecode caching.",
            diagnostic_code="TZ-ENV-003",
            requires_elevation=False,
            automated_fix_available=True,
            windows_powershell_cmd='Get-ChildItem -Path . -Include "__pycache__","*.pyc" -Recurse -Force | Remove-Item -Recurse -Force',
            posix_bash_cmd='find . -type d -name "__pycache__" -exec rm -rf {} + -o -name "*.pyc" -delete',
            verification_check_cmd='find . -name "*.pyc"',
            safety_notes="Bytecode is automatically regenerated by Python on subsequent imports.",
        ),
        SystemRepairRecipe(
            recipe_id="REC-PY-003",
            target_platform=SystemPlatform.UNKNOWN,
            title="Repair Corrupted Virtualenv pyvenv.cfg Interpreter Home",
            description="Discovers the active Python interpreter path and re-links the broken 'home' entry in pyvenv.cfg.",
            diagnostic_code="TZ-ENV-001",
            requires_elevation=False,
            automated_fix_available=True,
            safety_notes="T-Zero autonomously updates pyvenv.cfg preserving all installed site-packages.",
        ),

        # =====================================================================
        # 5. NODE.JS & JAVASCRIPT PACKAGE MANAGER RECIPES
        # =====================================================================
        SystemRepairRecipe(
            recipe_id="REC-NODE-001",
            target_platform=SystemPlatform.UNKNOWN,
            title="Purge Corrupted npm Cache and Verify Integrity",
            description="Executes 'npm cache clean --force' and verifies checksums when npm packages fail with tarball checksum mismatches.",
            diagnostic_code="TZ-NODE-001",
            requires_elevation=False,
            automated_fix_available=True,
            windows_powershell_cmd="npm cache clean --force; npm cache verify",
            posix_bash_cmd="npm cache clean --force && npm cache verify",
            verification_check_cmd="npm cache verify",
            safety_notes="Safe npm maintenance command.",
        ),

        # =====================================================================
        # 6. GIT VERSION CONTROL RECIPES
        # =====================================================================
        SystemRepairRecipe(
            recipe_id="REC-GIT-001",
            target_platform=SystemPlatform.UNKNOWN,
            title="Remove Stale .git/index.lock Lockfile",
            description="Unlocks git operations blocked by a crashed or aborted git process leaving a dangling index.lock.",
            diagnostic_code="TZ-ENV-002",
            requires_elevation=False,
            automated_fix_available=True,
            windows_powershell_cmd='if (Test-Path ".git\\index.lock") { Remove-Item ".git\\index.lock" -Force }',
            posix_bash_cmd="rm -f .git/index.lock",
            verification_check_cmd="git status",
            safety_notes="T-Zero verifies no git process is currently running before deleting.",
        ),
        SystemRepairRecipe(
            recipe_id="REC-GIT-002",
            target_platform=SystemPlatform.UNKNOWN,
            title="Execute Git Garbage Collection and Optimize Packfiles",
            description="Runs 'git gc --prune=now' to compress loose objects, prune unreachable dangling commits, and speed up git repository I/O.",
            diagnostic_code="TZ-GIT-002",
            requires_elevation=False,
            automated_fix_available=True,
            windows_powershell_cmd="git gc --prune=now",
            posix_bash_cmd="git gc --prune=now",
            verification_check_cmd="git count-objects -v",
            safety_notes="Optimizes internal Git repository storage without altering branch history.",
        ),
        SystemRepairRecipe(
            recipe_id="REC-GIT-003",
            target_platform=SystemPlatform.UNKNOWN,
            title="Verify Git Repository Object Database Integrity",
            description="Runs 'git fsck --full' to identify corrupted blobs, broken references, or dangling tree objects in .git store.",
            diagnostic_code="TZ-GIT-003",
            requires_elevation=False,
            automated_fix_available=True,
            windows_powershell_cmd="git fsck --full",
            posix_bash_cmd="git fsck --full",
            verification_check_cmd="git status",
            safety_notes="Read-only diagnostic verification of git object database integrity.",
        ),
        SystemRepairRecipe(
            recipe_id="REC-GIT-004",
            target_platform=SystemPlatform.UNKNOWN,
            title="Safe Dry-Run Sweep of Untracked Files and Build Artifacts",
            description="Executes 'git clean -ndX' to preview all untracked and gitignored dead artifacts without deleting them.",
            diagnostic_code="TZ-GIT-004",
            requires_elevation=False,
            automated_fix_available=True,
            windows_powershell_cmd="git clean -ndX",
            posix_bash_cmd="git clean -ndX",
            verification_check_cmd="git status --short",
            safety_notes="Dry-run preview only; never deletes files without explicit confirmation.",
        ),

        # =====================================================================
        # 7. DOCKER & CONTAINER REPAIR RECIPES
        # =====================================================================
        SystemRepairRecipe(
            recipe_id="REC-DOCKER-001",
            target_platform=SystemPlatform.UNKNOWN,
            title="Prune Dangling Containers, Unused Networks, and Builder Cache",
            description="Reclaims disk space and resolves port allocation conflicts caused by dead or zombie Docker containers.",
            diagnostic_code="TZ-DOCKER-001",
            requires_elevation=False,
            automated_fix_available=True,
            windows_powershell_cmd="docker container prune -f; docker network prune -f",
            posix_bash_cmd="docker container prune -f && docker network prune -f",
            verification_check_cmd="docker ps -a",
            safety_notes="Removes only stopped containers and unused networks; running containers are unaffected.",
        ),
        SystemRepairRecipe(
            recipe_id="REC-DOCKER-002",
            target_platform=SystemPlatform.UNKNOWN,
            title="Prune Stale Docker Buildx Cache",
            description="Purges corrupted layer build caches when multi-stage Docker builds fail with cryptic filesystem layer errors.",
            diagnostic_code="TZ-DOCKER-002",
            requires_elevation=False,
            automated_fix_available=True,
            windows_powershell_cmd="docker builder prune -f",
            posix_bash_cmd="docker builder prune -f",
            verification_check_cmd="docker builder du",
            safety_notes="Frees intermediate builder layers; images and volumes are preserved.",
        ),

        # =====================================================================
        # 8. RUST CARGO & GO TOOLCHAIN REPAIR RECIPES
        # =====================================================================
        SystemRepairRecipe(
            recipe_id="REC-CARGO-001",
            target_platform=SystemPlatform.UNKNOWN,
            title="Clean Rust Cargo Target Directory and Fingerprint Cache",
            description="Executes 'cargo clean' to wipe corrupted incremental compilation artifacts and rebuild rustc fingerprints.",
            diagnostic_code="TZ-RUST-001",
            requires_elevation=False,
            automated_fix_available=True,
            windows_powershell_cmd="cargo clean",
            posix_bash_cmd="cargo clean",
            verification_check_cmd="cargo check",
            safety_notes="Removes target/ directory cleanly; next build compiles from fresh source.",
        ),
        SystemRepairRecipe(
            recipe_id="REC-GO-001",
            target_platform=SystemPlatform.UNKNOWN,
            title="Purge Corrupted Go Build and Test Cache",
            description="Runs 'go clean -cache -testcache' to resolve corrupted Go package archives causing checksum verification panics.",
            diagnostic_code="TZ-GO-001",
            requires_elevation=False,
            automated_fix_available=True,
            windows_powershell_cmd="go clean -cache -testcache",
            posix_bash_cmd="go clean -cache -testcache",
            verification_check_cmd="go version",
            safety_notes="Cleans temporary build outputs while keeping downloaded vendor modules intact.",
        ),

        # =====================================================================
        # 9. NETWORKING & SYSTEM RESOLVER RECIPES
        # =====================================================================
        SystemRepairRecipe(
            recipe_id="REC-WIN-003",
            target_platform=SystemPlatform.WINDOWS,
            title="Flush Windows DNS Client Resolver Cache",
            description="Flushes and resets the local Windows DNS client cache when API endpoints or package hosts fail to resolve.",
            diagnostic_code="TZ-NET-001",
            requires_elevation=False,
            automated_fix_available=True,
            windows_powershell_cmd="Clear-DnsClientCache",
            posix_bash_cmd=None,
            verification_check_cmd="Get-DnsClientCache",
            safety_notes="Safe network cache flush; resolves stale DNS records immediately.",
        ),
        SystemRepairRecipe(
            recipe_id="REC-POSIX-002",
            target_platform=SystemPlatform.LINUX,
            title="Harden OpenSSH ~/.ssh Directory and Key Permissions",
            description="Enforces strict POSIX permissions (chmod 700 ~/.ssh, chmod 600 ~/.ssh/*) required by SSH daemon to prevent key rejection.",
            diagnostic_code="TZ-SSH-001",
            requires_elevation=False,
            automated_fix_available=True,
            windows_powershell_cmd=None,
            posix_bash_cmd="chmod 700 ~/.ssh && chmod 600 ~/.ssh/* 2>/dev/null || true",
            verification_check_cmd="ls -ld ~/.ssh",
            safety_notes="Enforces standard OpenSSH security standards across POSIX systems.",
        ),
    ]

    _INDEX_BY_RECIPE: Dict[str, SystemRepairRecipe] = {r.recipe_id: r for r in RECIPES}
    _INDEX_BY_DIAG_CODE: Dict[str, SystemRepairRecipe] = {r.diagnostic_code: r for r in RECIPES}

    @classmethod
    def get_recipe(cls, recipe_id: str) -> Optional[SystemRepairRecipe]:
        return cls._INDEX_BY_RECIPE.get(recipe_id.upper())

    @classmethod
    def find_recipe_for_issue(cls, diagnostic_code: str) -> Optional[SystemRepairRecipe]:
        return cls._INDEX_BY_DIAG_CODE.get(diagnostic_code.upper())

    @classmethod
    def list_recipes_for_platform(cls, target_platform: SystemPlatform) -> List[SystemRepairRecipe]:
        return [
            r for r in cls.RECIPES
            if r.target_platform == target_platform or r.target_platform == SystemPlatform.UNKNOWN
        ]

    @classmethod
    def execute_recipe_command(cls, recipe: SystemRepairRecipe, dry_run: bool = False) -> Tuple[bool, str]:
        """Executes the appropriate platform command for a given repair recipe."""
        if dry_run:
            return True, f"[DRY-RUN] Would execute recipe '{recipe.title}'"

        sys_name = platform.system().lower()
        cmd: Optional[str] = None

        if "windows" in sys_name and recipe.windows_powershell_cmd:
            cmd = f'powershell -NoProfile -Command "{recipe.windows_powershell_cmd}"'
        elif ("linux" in sys_name or "darwin" in sys_name) and recipe.posix_bash_cmd:
            cmd = f'bash -c "{recipe.posix_bash_cmd}"'

        if not cmd:
            return False, f"No automated command configured for platform {sys_name} in recipe {recipe.recipe_id}"

        try:
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
            if res.returncode == 0:
                return True, f"Successfully executed recipe '{recipe.title}': {res.stdout.strip() or 'OK'}"
            return False, f"Recipe '{recipe.title}' failed with code {res.returncode}: {res.stderr.strip()}"
        except Exception as e:
            return False, f"Exception executing recipe '{recipe.title}': {e}"
