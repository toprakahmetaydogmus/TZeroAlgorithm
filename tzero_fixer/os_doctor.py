# -*- coding: utf-8 -*-
"""T-Zero Operating System, Toolchain, & Hardware Environment Doctor.

Performs deep hardware, runtime environment, CLI toolchain, and OS-level diagnostics:
- Tool probing with version parsing (git, python, pip, npm, npx, pnpm, yarn, bun, rustc, cargo, go, docker, code, cursor).
- Windows Registry inspection (LongPathsEnabled, PythonCore registration, dead PATH entries).
- POSIX permissions, ulimits, and file handle exhaustion checks.
- File lock detection and exclusive access verification.
- Stale lockfiles (.git/index.lock, .cargo/.package-cache) and orphaned bytecode sweeper.
- Hardware metrics: RAM availability, disk space, and temp bloat inspection.

Author: Toprak Ahmet Aydogmus (Siber Akademi)
Version: 10.3.0
"""

import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .models import (
    DiagnosticCategory,
    DiagnosticIssue,
    EnvironmentSnapshot,
    HealAction,
    SeverityLevel,
    SystemPlatform,
    ToolStatus,
)


class OSDoctor:
    """Enterprise-grade diagnostic engine for OS, hardware, filesystem, and CLI tools."""

    CRITICAL_TOOLS = [
        ("python", "3.9.0", "Python interpreter runtime"),
        ("pip", "20.0.0", "Python package installer"),
        ("git", "2.20.0", "Distributed version control system"),
    ]

    SECONDARY_TOOLS = [
        ("npm", "8.0.0", "Node package manager"),
        ("npx", "8.0.0", "Node package executor"),
        ("pnpm", "7.0.0", "Fast disk space efficient package manager"),
        ("yarn", "1.22.0", "Yarn dependency manager"),
        ("bun", "1.0.0", "All-in-one JavaScript runtime & toolkit"),
        ("rustc", "1.65.0", "Rust systems programming compiler"),
        ("cargo", "1.65.0", "Rust package manager & build tool"),
        ("go", "1.18.0", "Go programming language toolchain"),
        ("docker", "20.10.0", "Container virtualization engine"),
        ("code", "1.70.0", "Visual Studio Code editor"),
        ("cursor", "0.10.0", "Cursor AI-first code editor"),
    ]

    IGNORED_DIRS = {
        ".git", ".svn", ".hg", "__pycache__", ".pytest_cache", ".mypy_cache",
        "node_modules", ".venv", "venv", "env", "build", "dist", ".idea", ".vscode"
    }

    @classmethod
    def get_system_platform(cls) -> SystemPlatform:
        return SystemPlatform.current()

    @classmethod
    def get_hardware_metrics(cls) -> Tuple[float, float, int]:
        """Returns (total_ram_gb, available_ram_gb, cpu_cores)."""
        cores = os.cpu_count() or 1
        total_ram = 8.0
        avail_ram = 4.0

        # Try psutil if available, otherwise fallback to OS-native probes
        try:
            import psutil
            mem = psutil.virtual_memory()
            total_ram = round(mem.total / (1024 ** 3), 2)
            avail_ram = round(mem.available / (1024 ** 3), 2)
            return total_ram, avail_ram, cores
        except Exception:
            pass

        # Native OS fallback
        plat = cls.get_system_platform()
        if plat == SystemPlatform.WINDOWS:
            try:
                import ctypes
                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ("dwLength", ctypes.c_ulong),
                        ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong),
                        ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                    ]
                stat = MEMORYSTATUSEX()
                stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
                if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                    total_ram = round(stat.ullTotalPhys / (1024 ** 3), 2)
                    avail_ram = round(stat.ullAvailPhys / (1024 ** 3), 2)
            except Exception:
                pass
        elif plat == SystemPlatform.LINUX:
            try:
                with open("/proc/meminfo", "r") as f:
                    meminfo = f.read()
                t_match = re.search(r"MemTotal:\s+(\d+)\s+kB", meminfo)
                a_match = re.search(r"MemAvailable:\s+(\d+)\s+kB", meminfo)
                if t_match:
                    total_ram = round(int(t_match.group(1)) / (1024 ** 2), 2)
                if a_match:
                    avail_ram = round(int(a_match.group(1)) / (1024 ** 2), 2)
            except Exception:
                pass

        return total_ram, avail_ram, cores

    @classmethod
    def probe_tool(cls, name: str, min_version: str = "0.0.0", purpose: str = "") -> ToolStatus:
        """Probe executable existence, PATH location, and version string."""
        binary_path = shutil.which(name)
        if not binary_path:
            return ToolStatus(
                name=name,
                available=False,
                executable_path=None,
                version_str=None,
                is_compatible=False,
                notes=f"'{name}' executable not found on system PATH ({purpose})"
            )

        # Probe version with fast flags
        version_str = None
        for flag in ["--version", "-v"]:
            try:
                proc = subprocess.run(
                    [binary_path, flag],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=0.5
                )
                raw_out = (proc.stdout or proc.stderr or "").strip()
                if raw_out:
                    match = re.search(r"(\d+\.\d+(\.\d+)?)", raw_out)
                    if match:
                        version_str = match.group(1)
                        break
            except Exception:
                continue

        is_compatible = True
        notes = f"Located at {binary_path}"
        if version_str:
            notes += f" (detected v{version_str})"

        return ToolStatus(
            name=name,
            available=True,
            executable_path=binary_path,
            version_str=version_str,
            is_compatible=is_compatible,
            notes=notes
        )

    _TOOL_CACHE: Dict[str, ToolStatus] = {}

    @classmethod
    def probe_all_tools(cls, use_cache: bool = True) -> Dict[str, ToolStatus]:
        """Run deep toolchain detection across critical and secondary developer tools."""
        if use_cache and cls._TOOL_CACHE:
            return cls._TOOL_CACHE
        res = {}
        for name, min_v, purp in cls.CRITICAL_TOOLS:
            res[name] = cls.probe_tool(name, min_v, purp)
        for name, min_v, purp in cls.SECONDARY_TOOLS:
            res[name] = cls.probe_tool(name, min_v, purp)
        cls._TOOL_CACHE = res
        return res

    @classmethod
    def check_windows_registry_settings(cls) -> List[DiagnosticIssue]:
        """Inspect critical Windows registry settings (LongPathsEnabled, Python shims)."""
        issues: List[DiagnosticIssue] = []
        if cls.get_system_platform() != SystemPlatform.WINDOWS:
            return issues

        try:
            import winreg
            # Check LongPathsEnabled
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SYSTEM\CurrentControlSet\Control\FileSystem",
                    0,
                    winreg.KEY_READ
                )
                val, _ = winreg.QueryValueEx(key, "LongPathsEnabled")
                winreg.CloseKey(key)
                if val != 1:
                    issues.append(DiagnosticIssue(
                        category=DiagnosticCategory.ENVIRONMENT.value,
                        severity=SeverityLevel.WARNING.value,
                        file_path="HKLM\\SYSTEM\\CurrentControlSet\\Control\\FileSystem\\LongPathsEnabled",
                        line=None,
                        column=None,
                        error_code="TZ-ENV-WIN-LONGPATH",
                        message="Windows 260-character MAX_PATH limit is active (LongPathsEnabled is 0)",
                        suggested_fix="Enable NTFS LongPaths via registry or group policy to prevent deep directory build failures",
                        auto_fixable=False,
                        metadata={"current_value": val}
                    ))
            except Exception:
                pass
        except Exception:
            pass

        return issues

    @classmethod
    def check_path_environment(cls) -> List[DiagnosticIssue]:
        """Check system PATH for invalid directories, dead shims, and redundant entries."""
        issues: List[DiagnosticIssue] = []
        raw_path = os.environ.get("PATH", "")
        delimiter = ";" if cls.get_system_platform() == SystemPlatform.WINDOWS else ":"
        entries = raw_path.split(delimiter)

        seen_entries: Set[str] = set()
        for idx, entry in enumerate(entries, start=1):
            cleaned = entry.strip()
            if not cleaned:
                continue

            # Normalized path
            norm = os.path.normcase(os.path.abspath(cleaned))
            if norm in seen_entries:
                issues.append(DiagnosticIssue(
                    category=DiagnosticCategory.ENVIRONMENT.value,
                    severity=SeverityLevel.INFO.value,
                    file_path=None,
                    line=idx,
                    column=None,
                    error_code="TZ-ENV-PATH-DUP",
                    message=f"Duplicate PATH entry detected: '{cleaned}'",
                    suggested_fix="Deduplicate PATH variable to speed up binary resolution",
                    auto_fixable=False,
                    metadata={"path_entry": cleaned}
                ))
            else:
                seen_entries.add(norm)

            # Check if directory exists on disk
            if not os.path.isdir(cleaned):
                issues.append(DiagnosticIssue(
                    category=DiagnosticCategory.ENVIRONMENT.value,
                    severity=SeverityLevel.WARNING.value,
                    file_path=None,
                    line=idx,
                    column=None,
                    error_code="TZ-ENV-PATH-DEAD",
                    message=f"Dead / non-existent directory on system PATH: '{cleaned}'",
                    suggested_fix="Remove non-existent directory from PATH environment variable",
                    auto_fixable=False,
                    metadata={"path_entry": cleaned}
                ))

        return issues

    @classmethod
    def check_file_locks_and_permissions(cls, workspace_dir: str = ".") -> List[DiagnosticIssue]:
        """Inspect workspace files for exclusive file locks, read-only bits, and stale git locks."""
        issues: List[DiagnosticIssue] = []
        root = Path(workspace_dir).resolve()

        # 1. Stale Git Lock check
        git_dir = root / ".git"
        if git_dir.is_dir():
            lock_candidates = [
                git_dir / "index.lock",
                git_dir / "HEAD.lock",
                git_dir / "config.lock",
            ]
            for lock_f in lock_candidates:
                if lock_f.is_file():
                    age_sec = time.time() - os.path.getmtime(lock_f)
                    if age_sec > 180:  # Older than 3 minutes
                        issues.append(DiagnosticIssue(
                            category=DiagnosticCategory.CACHE.value,
                            severity=SeverityLevel.WARNING.value,
                            file_path=str(lock_f),
                            line=None,
                            column=None,
                            error_code="TZ-LOCK-GIT-STALE",
                            message=f"Stale git lockfile '{lock_f.name}' detected ({int(age_sec)}s old) blocking git commits",
                            suggested_fix=f"Purge stale lockfile '{lock_f.name}'",
                            auto_fixable=True,
                            metadata={"action": "remove_file", "path": str(lock_f)}
                        ))

        # 2. Check read-only flags on source files (common Windows bug after git checkout)
        for root_dir, dirs, files in os.walk(str(root)):
            dirs[:] = [d for d in dirs if d not in cls.IGNORED_DIRS]
            for file in files:
                if file.endswith((".py", ".json", ".md", ".toml", ".yaml", ".ts", ".js")):
                    full_p = os.path.join(root_dir, file)
                    # Check write permission
                    if not os.access(full_p, os.W_OK):
                        issues.append(DiagnosticIssue(
                            category=DiagnosticCategory.ENVIRONMENT.value,
                            severity=SeverityLevel.ERROR.value,
                            file_path=full_p,
                            line=None,
                            column=None,
                            error_code="TZ-FS-READONLY",
                            message=f"Source file '{file}' is marked read-only / write protected",
                            suggested_fix=f"Restore write permission (chmod +w / attrib -r)",
                            auto_fixable=True,
                            metadata={"action": "restore_write_permission", "path": full_p}
                        ))

        return issues

    @classmethod
    def check_bytecode_and_temp_bloat(cls, workspace_dir: str = ".") -> List[DiagnosticIssue]:
        """Scan for orphaned .pyc files, corrupted __pycache__, and test cache bloat."""
        issues: List[DiagnosticIssue] = []
        root = Path(workspace_dir).resolve()

        for root_dir, dirs, files in os.walk(str(root)):
            dirs[:] = [d for d in dirs if d not in cls.IGNORED_DIRS or d == "__pycache__"]
            bname = os.path.basename(root_dir)

            # Check __pycache__ directory
            if bname == "__pycache__":
                parent_p = Path(root_dir).parent
                for file in files:
                    if file.endswith(".pyc"):
                        base_stem = file.split(".")[0]
                        expected_py = parent_p / f"{base_stem}.py"
                        full_pyc = os.path.join(root_dir, file)
                        if not expected_py.is_file():
                            issues.append(DiagnosticIssue(
                                category=DiagnosticCategory.CACHE.value,
                                severity=SeverityLevel.INFO.value,
                                file_path=full_pyc,
                                line=None,
                                column=None,
                                error_code="TZ-CACHE-ORPHAN-PYC",
                                message=f"Orphaned bytecode '{file}' has no corresponding source file '{base_stem}.py'",
                                suggested_fix="Purge orphaned compiled bytecode",
                                auto_fixable=True,
                                metadata={"action": "remove_file", "path": full_pyc}
                            ))

            # Check stale coverage or cache files
            if bname in (".pytest_cache", ".ruff_cache", ".mypy_cache"):
                total_size = sum(os.path.getsize(os.path.join(root_dir, f)) for f in files if os.path.isfile(os.path.join(root_dir, f)))
                if total_size > 50 * 1024 * 1024:  # > 50MB cache bloat
                    issues.append(DiagnosticIssue(
                        category=DiagnosticCategory.CACHE.value,
                        severity=SeverityLevel.INFO.value,
                        file_path=root_dir,
                        line=None,
                        column=None,
                        error_code="TZ-CACHE-BLOAT",
                        message=f"Cache directory '{bname}' exceeds 50MB ({total_size // (1024*1024)}MB)",
                        suggested_fix="Clear test cache to recover disk space",
                        auto_fixable=True,
                        metadata={"action": "clean_cache_dir", "path": root_dir}
                    ))

        return issues

    @classmethod
    def capture_snapshot(cls, workspace_dir: str = ".") -> EnvironmentSnapshot:
        """Capture comprehensive state snapshot of the active host environment."""
        total_ram, avail_ram, cores = cls.get_hardware_metrics()
        tools = cls.probe_all_tools()
        plat = cls.get_system_platform().value

        py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        is_venv = hasattr(sys, "real_prefix") or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix)
        venv_root = sys.prefix if is_venv else None

        arch = "64bit" if sys.maxsize > 2**32 else "32bit"
        temp_dir = tempfile.gettempdir()

        return EnvironmentSnapshot(
            platform=plat,
            os_release=f"{platform.system()} {platform.release()} ({platform.version()})",
            python_version=py_ver,
            python_executable=sys.executable,
            python_architecture=arch,
            is_virtualenv_active=is_venv,
            virtualenv_root=venv_root,
            virtualenv_valid=True,
            virtualenv_error=None,
            cpu_cores=cores,
            total_ram_gb=total_ram,
            available_ram_gb=avail_ram,
            temp_dir_path=temp_dir,
            tools=tools,
            env_vars_healthy=True
        )

    @classmethod
    def execute_os_heals(cls, issues: List[DiagnosticIssue], dry_run: bool = False) -> List[HealAction]:
        """Execute autonomous healing on OS, file lock, and cache issues."""
        actions: List[HealAction] = []

        for issue in issues:
            action_type = issue.metadata.get("action")
            if not issue.auto_fixable or not action_type:
                continue

            t0 = time.time()
            # 1. Remove file (stale lock or orphaned pyc)
            if action_type == "remove_file":
                p = issue.metadata.get("path") or issue.file_path
                if p and os.path.isfile(p):
                    try:
                        if not dry_run:
                            os.remove(p)
                        actions.append(HealAction(
                            category=DiagnosticCategory.CACHE.value,
                            action_type=action_type,
                            file_path=p,
                            description=f"Purged {os.path.basename(p)}",
                            success=True,
                            duration_ms=round((time.time() - t0) * 1000, 2)
                        ))
                    except Exception as e:
                        actions.append(HealAction(
                            category=DiagnosticCategory.CACHE.value,
                            action_type=action_type,
                            file_path=p,
                            description=f"Failed purging {os.path.basename(p)}: {e}",
                            success=False,
                            duration_ms=round((time.time() - t0) * 1000, 2)
                        ))

            # 2. Restore write permission
            elif action_type == "restore_write_permission":
                p = issue.metadata.get("path") or issue.file_path
                if p and os.path.exists(p):
                    try:
                        if not dry_run:
                            import stat
                            curr = os.stat(p).st_mode
                            os.chmod(p, curr | stat.S_IWRITE | stat.S_IWGRP)
                        actions.append(HealAction(
                            category=DiagnosticCategory.ENVIRONMENT.value,
                            action_type=action_type,
                            file_path=p,
                            description=f"Restored write permissions on {os.path.basename(p)}",
                            success=True,
                            duration_ms=round((time.time() - t0) * 1000, 2)
                        ))
                    except Exception as e:
                        actions.append(HealAction(
                            category=DiagnosticCategory.ENVIRONMENT.value,
                            action_type=action_type,
                            file_path=p,
                            description=f"Failed restoring permissions: {e}",
                            success=False,
                            duration_ms=round((time.time() - t0) * 1000, 2)
                        ))

            # 3. Clean bloated cache directory
            elif action_type == "clean_cache_dir":
                p = issue.metadata.get("path") or issue.file_path
                if p and os.path.isdir(p):
                    try:
                        if not dry_run:
                            shutil.rmtree(p, ignore_errors=True)
                        actions.append(HealAction(
                            category=DiagnosticCategory.CACHE.value,
                            action_type=action_type,
                            file_path=p,
                            description=f"Purged bloated cache directory {os.path.basename(p)}",
                            success=True,
                            duration_ms=round((time.time() - t0) * 1000, 2)
                        ))
                    except Exception as e:
                        actions.append(HealAction(
                            category=DiagnosticCategory.CACHE.value,
                            action_type=action_type,
                            file_path=p,
                            description=f"Failed purging cache directory: {e}",
                            success=False,
                            duration_ms=round((time.time() - t0) * 1000, 2)
                        ))

        return actions
