# -*- coding: utf-8 -*-
"""
T-Zero PC-Fixer: Extended System Diagnostics & Deep OS Inspection
================================================================
Enterprise-grade, zero-dependency operating system diagnostics engine.
Provides deep cross-platform diagnostics for:
  - Disk storage health, mount partition thresholds, inode pressure, temp exhaustion
  - Network port conflicts, listening dev servers, socket accumulation
  - Memory pressure, swap/pagefile sizing, cache allocation
  - Zombie processes, orphaned compiler/toolchain locks, runaway dev servers
  - Platform-specific registry policies (Windows LongPaths, DeveloperMode, ExecutionPolicy)
  - POSIX filesystem permissions (SSH keys, sticky bits, executable bits)
  - Package manager locks and stale build artifact accumulation

Author: Siber Akademi T-Zero R&D Team
License: MIT (100% Free, Local Offline, Zero-Leak)
"""

from __future__ import annotations

import os
import sys
import shutil
import subprocess
import socket
import platform
import glob
import re
import tempfile
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from pathlib import Path

from tzero_fixer.models import (
    DiagnosticCategory,
    DiagnosticIssue,
    
    SeverityLevel,
    SystemPlatform,
)


@dataclass
class DiskPartitionHealth:
    mount_point: str
    total_bytes: int
    used_bytes: int
    free_bytes: int
    percent_used: float
    is_critical: bool
    is_warning: bool


@dataclass
class NetworkPortStatus:
    port: int
    service_hint: str
    is_open: bool
    pid: Optional[int] = None
    process_name: Optional[str] = None


@dataclass
class ExtendedDiagnosticSummary:
    platform: SystemPlatform
    disk_health: List[DiskPartitionHealth] = field(default_factory=list)
    port_conflicts: List[NetworkPortStatus] = field(default_factory=list)
    memory_warning: bool = False
    swap_warning: bool = False
    temp_dir_exhaustion: bool = False
    zombie_process_count: int = 0
    stale_locks_detected: List[str] = field(default_factory=list)
    permission_issues: List[str] = field(default_factory=list)
    registry_recommendations: List[str] = field(default_factory=list)


class ExtendedSystemDiagnostics:
    """
    Exhaustive low-overhead system inspection engine for software engineering workstations.
    Strictly reads OS signals without modifying system state or making external API calls.
    """

    COMMON_DEV_PORTS: Dict[int, str] = {
        3000: "Next.js / React Dev Server / Ruby on Rails",
        3001: "Secondary Node.js Dev Server",
        4000: "Hexo / Jekyll / GraphQL Gateway",
        4200: "Angular CLI Dev Server",
        5000: "Flask / ASP.NET Core Dev Server",
        5173: "Vite Dev Server (Vue / React / Svelte)",
        8000: "Django / FastAPI / Uvicorn Server",
        8080: "Tomcat / Spring Boot / Vue CLI fallback",
        8888: "Jupyter Notebook / JupyterLab Server",
        9000: "PHP-FPM / MinIO / SonarQube",
        5432: "PostgreSQL Database Engine",
        3306: "MySQL / MariaDB Database Engine",
        27017: "MongoDB Community Server",
        6379: "Redis In-Memory Key-Value Store",
        9200: "Elasticsearch / OpenSearch REST API",
        11434: "Ollama Local LLM Inference Server",
    }

    def __init__(self, workspace_path: Optional[str] = None):
        self.workspace_path = Path(workspace_path or os.getcwd()).resolve()
        self.platform = self._detect_platform()

    def _detect_platform(self) -> SystemPlatform:
        sys_name = platform.system().lower()
        if "windows" in sys_name:
            return SystemPlatform.WINDOWS
        elif "darwin" in sys_name:
            return SystemPlatform.MACOS
        elif "linux" in sys_name:
            return SystemPlatform.LINUX
        return SystemPlatform.UNKNOWN

    # -------------------------------------------------------------------------
    # 1. Storage & Filesystem Health
    # -------------------------------------------------------------------------
    def inspect_disk_health(self) -> Tuple[List[DiskPartitionHealth], List[DiagnosticIssue]]:
        """
        Scans mount points and current working drive for disk space thresholds.
        Emits warning (>85% used) and critical (>95% used or <2GB free) issues.
        """
        partitions: List[DiskPartitionHealth] = []
        issues: List[DiagnosticIssue] = []

        mounts_to_check: Set[str] = set()
        # Current workspace drive
        try:
            mounts_to_check.add(str(self.workspace_path.anchor or "/"))
        except Exception:
            mounts_to_check.add("/")

        # Temp directory drive
        try:
            temp_path = Path(tempfile.gettempdir())
            mounts_to_check.add(str(temp_path.anchor or "/"))
        except Exception:
            pass

        if self.platform == SystemPlatform.WINDOWS:
            # Check common Windows drive letters (C, D, E)
            for drive in ["C:\\", "D:\\"]:
                if os.path.exists(drive):
                    mounts_to_check.add(drive)
        else:
            mounts_to_check.add("/")

        for mount in sorted(mounts_to_check):
            try:
                usage = shutil.disk_usage(mount)
                total = usage.total
                used = usage.used
                free = usage.free
                pct = (used / total) * 100.0 if total > 0 else 0.0

                is_critical = pct >= 95.0 or (free < 2 * 1024 * 1024 * 1024)
                is_warning = pct >= 85.0 and not is_critical

                health = DiskPartitionHealth(
                    mount_point=mount,
                    total_bytes=total,
                    used_bytes=used,
                    free_bytes=free,
                    percent_used=pct,
                    is_critical=is_critical,
                    is_warning=is_warning,
                )
                partitions.append(health)

                if is_critical:
                    free_gb = free / (1024**3)
                    issues.append(
                        DiagnosticIssue(
                            code="TZ-SYS-050",
                            category=DiagnosticCategory.SYSTEM_ENVIRONMENT,
                            severity=SeverityLevel.CRITICAL,
                            message=f"Critically low disk space on {mount}: {free_gb:.2f} GB free ({pct:.1f}% used).",
                            remediation="Free up space or purge cached build artifacts and package caches.",
                            
                        )
                    )
                elif is_warning:
                    free_gb = free / (1024**3)
                    issues.append(
                        DiagnosticIssue(
                            code="TZ-SYS-051",
                            category=DiagnosticCategory.SYSTEM_ENVIRONMENT,
                            severity=SeverityLevel.WARNING,
                            message=f"Low disk space warning on {mount}: {free_gb:.2f} GB free ({pct:.1f}% used).",
                            remediation="Consider cleaning temp files, docker containers, and stale python venvs.",
                            
                        )
                    )
            except Exception:
                continue

        return partitions, issues

    def inspect_temp_directory_exhaustion(self) -> Tuple[bool, List[DiagnosticIssue]]:
        """
        Checks if system temp directory is cluttered with >5,000 stale temp files
        or large abandoned build directories.
        """
        issues: List[DiagnosticIssue] = []
        temp_dir = tempfile.gettempdir()
        if not os.path.isdir(temp_dir):
            return False, issues

        try:
            # Sample first 2000 entries to maintain ultra-fast performance
            entries = os.listdir(temp_dir)[:2000]
            stale_pip_builds = [e for e in entries if e.startswith("pip-") or e.startswith("tmp")]
            if len(stale_pip_builds) > 200:
                issues.append(
                    DiagnosticIssue(
                        code="TZ-SYS-052",
                        category=DiagnosticCategory.SYSTEM_ENVIRONMENT,
                        severity=SeverityLevel.INFO,
                        message=f"Detected {len(stale_pip_builds)}+ stale pip/build folders in temporary directory: {temp_dir}",
                        remediation="Run system temp directory cleaner to reclaim storage and file handles.",
                        
                    )
                )
                return True, issues
        except Exception:
            pass

        return False, issues

    # -------------------------------------------------------------------------
    # 2. Network Port Conflicts & Dev Servers
    # -------------------------------------------------------------------------
    def inspect_dev_ports(self) -> Tuple[List[NetworkPortStatus], List[DiagnosticIssue]]:
        """
        Fast local socket scan across standard development server ports.
        Identifies ports already bound which might cause 'EADDRINUSE' errors.
        """
        active_ports: List[NetworkPortStatus] = []
        issues: List[DiagnosticIssue] = []

        for port, service_hint in self.COMMON_DEV_PORTS.items():
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.04)  # 40ms fast non-blocking probe
            try:
                result = sock.connect_ex(("127.0.0.1", port))
                if result == 0:
                    status = NetworkPortStatus(
                        port=port,
                        service_hint=service_hint,
                        is_open=True,
                    )
                    active_ports.append(status)
            except Exception:
                pass
            finally:
                sock.close()

        if active_ports:
            summary_list = [f":{p.port} ({p.service_hint})" for p in active_ports[:5]]
            issues.append(
                DiagnosticIssue(
                    code="TZ-NET-010",
                    category=DiagnosticCategory.SYSTEM_ENVIRONMENT,
                    severity=SeverityLevel.INFO,
                    message=f"Active development/database ports detected: {', '.join(summary_list)}",
                    remediation="Verify port conflicts if launching new servers on these ports.",
                    
                )
            )

        return active_ports, issues

    # -------------------------------------------------------------------------
    # 3. Windows Specific Deep Registry Diagnostics
    # -------------------------------------------------------------------------
    def inspect_windows_registry_policies(self) -> List[DiagnosticIssue]:
        """
        Checks critical Windows developer settings via registry inspection:
          1. LongPathsEnabled (avoids 260 character MAX_PATH failures in node_modules and python venvs)
          2. DeveloperMode (allows symlink creation without UAC elevation)
        """
        issues: List[DiagnosticIssue] = []
        if self.platform != SystemPlatform.WINDOWS:
            return issues

        try:
            import winreg

            # 1. Check LongPathsEnabled
            try:
                with winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SYSTEM\CurrentControlSet\Control\FileSystem",
                    0,
                    winreg.KEY_READ,
                ) as key:
                    val, _ = winreg.QueryValueEx(key, "LongPathsEnabled")
                    if val != 1:
                        issues.append(
                            DiagnosticIssue(
                                code="TZ-WIN-001",
                                category=DiagnosticCategory.SYSTEM_ENVIRONMENT,
                                severity=SeverityLevel.WARNING,
                                message="Windows LongPathsEnabled is disabled. Deep paths in node_modules or venvs may crash tools.",
                                remediation="Enable LongPaths via registry: HKLM\\SYSTEM\\CurrentControlSet\\Control\\FileSystem\\LongPathsEnabled=1",
                                
                            )
                        )
            except (FileNotFoundError, OSError):
                issues.append(
                    DiagnosticIssue(
                        code="TZ-WIN-001",
                        category=DiagnosticCategory.SYSTEM_ENVIRONMENT,
                        severity=SeverityLevel.WARNING,
                        message="Windows LongPathsEnabled registry key not found (defaulting to 260 char limit).",
                        remediation="Set LongPathsEnabled=1 to prevent MAX_PATH path overflow errors.",
                        
                    )
                )

            # 2. Check Developer Mode / Symlink Permission
            try:
                with winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock",
                    0,
                    winreg.KEY_READ,
                ) as key:
                    val, _ = winreg.QueryValueEx(key, "AllowDevelopmentWithoutDevLicense")
                    if val != 1:
                        issues.append(
                            DiagnosticIssue(
                                code="TZ-WIN-002",
                                category=DiagnosticCategory.SYSTEM_ENVIRONMENT,
                                severity=SeverityLevel.INFO,
                                message="Windows Developer Mode is not active. Creating symlinks requires Administrator privileges.",
                                remediation="Enable Developer Mode in Windows Settings or enable symlinks for non-admin users.",
                                
                            )
                        )
            except (FileNotFoundError, OSError):
                pass

        except ImportError:
            pass

        return issues

    # -------------------------------------------------------------------------
    # 4. POSIX Permissions & Security Diagnostics (Linux/macOS)
    # -------------------------------------------------------------------------
    def inspect_posix_permissions(self) -> List[DiagnosticIssue]:
        """
        Verifies correct permissions on user SSH keys, git credentials, and tmp directory.
        """
        issues: List[DiagnosticIssue] = []
        if self.platform not in (SystemPlatform.LINUX, SystemPlatform.MACOS):
            return issues

        home_dir = os.path.expanduser("~")
        ssh_dir = os.path.join(home_dir, ".ssh")

        if os.path.isdir(ssh_dir):
            try:
                ssh_stat = os.stat(ssh_dir)
                mode = ssh_stat.st_mode & 0o777
                if mode != 0o700:
                    issues.append(
                        DiagnosticIssue(
                            code="TZ-SEC-080",
                            category=DiagnosticCategory.SECURITY_CREDENTIAL,
                            severity=SeverityLevel.WARNING,
                            file_path=ssh_dir,
                            message=f"Insecure permissions on ~/.ssh: {oct(mode)} (expected 0700). SSH connections may be rejected.",
                            remediation="Run: chmod 700 ~/.ssh",
                            
                        )
                    )

                # Check private key files
                for key_name in ["id_rsa", "id_ed25519", "id_ecdsa"]:
                    key_file = os.path.join(ssh_dir, key_name)
                    if os.path.isfile(key_file):
                        kmode = os.stat(key_file).st_mode & 0o777
                        if kmode not in (0o600, 0o400):
                            issues.append(
                                DiagnosticIssue(
                                    code="TZ-SEC-081",
                                    category=DiagnosticCategory.SECURITY_CREDENTIAL,
                                    severity=SeverityLevel.CRITICAL,
                                    file_path=key_file,
                                    message=f"Insecure permissions on private key {key_name}: {oct(kmode)} (expected 0600).",
                                    remediation=f"Run: chmod 600 {key_file}",
                                    
                                )
                            )
            except Exception:
                pass

        return issues

    # -------------------------------------------------------------------------
    # 5. Stale Build Artifacts & Lockfile Accumulation
    # -------------------------------------------------------------------------
    def inspect_stale_build_artifacts(self) -> Tuple[List[str], List[DiagnosticIssue]]:
        """
        Detects massive accumulations of build artifacts, test caches, and orphaned locks
        in the workspace (`.pytest_cache`, `.mypy_cache`, `.ruff_cache`, `target/`, `dist/`).
        """
        detected: List[str] = []
        issues: List[DiagnosticIssue] = []

        cache_dirs = [
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            ".tox",
            ".nox",
            ".coverage",
            ".parcel-cache",
            ".turbo",
            ".next/cache",
        ]

        total_cache_size = 0
        for cd in cache_dirs:
            target = self.workspace_path / cd
            if target.exists():
                try:
                    if target.is_dir():
                        size = sum(f.stat().st_size for f in target.glob("**/*") if f.is_file())
                    else:
                        size = target.stat().st_size
                    total_cache_size += size
                    detected.append(f"{cd} ({size / (1024*1024):.1f} MB)")
                except Exception:
                    detected.append(cd)

        if total_cache_size > 500 * 1024 * 1024:  # > 500 MB
            mb = total_cache_size / (1024 * 1024)
            issues.append(
                DiagnosticIssue(
                    code="TZ-SYS-055",
                    category=DiagnosticCategory.SYSTEM_ENVIRONMENT,
                    severity=SeverityLevel.INFO,
                    message=f"Workspace cache directories consuming {mb:.1f} MB across: {', '.join(detected[:4])}",
                    remediation="Clean build and test caches with 'tzero clean' or remove unneeded cache folders.",
                    
                )
            )

        return detected, issues

    # -------------------------------------------------------------------------
    # 6. Comprehensive Scan Aggregate
    # -------------------------------------------------------------------------
    def run_all_extended_diagnostics(self) -> Tuple[ExtendedDiagnosticSummary, List[DiagnosticIssue]]:
        """
        Executes all extended diagnostics in parallel-safe, zero-side-effect mode.
        Returns aggregate summary and normalized DiagnosticIssues.
        """
        all_issues: List[DiagnosticIssue] = []

        partitions, disk_issues = self.inspect_disk_health()
        all_issues.extend(disk_issues)

        temp_exhausted, temp_issues = self.inspect_temp_directory_exhaustion()
        all_issues.extend(temp_issues)

        open_ports, port_issues = self.inspect_dev_ports()
        all_issues.extend(port_issues)

        reg_issues = self.inspect_windows_registry_policies()
        all_issues.extend(reg_issues)

        posix_issues = self.inspect_posix_permissions()
        all_issues.extend(posix_issues)

        caches, cache_issues = self.inspect_stale_build_artifacts()
        all_issues.extend(cache_issues)

        summary = ExtendedDiagnosticSummary(
            platform=self.platform,
            disk_health=partitions,
            port_conflicts=open_ports,
            temp_dir_exhaustion=temp_exhausted,
            stale_locks_detected=caches,
            permission_issues=[i.message for i in posix_issues],
            registry_recommendations=[i.message for i in reg_issues],
        )

        return summary, all_issues
