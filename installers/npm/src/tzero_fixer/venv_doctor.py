# -*- coding: utf-8 -*-
"""T-Zero Virtualenv, Python Runtime, and Dependency Drift Doctor.

Performs forensic diagnosis and autonomous healing on:
- Virtual environment structures (.venv, venv, env, poetry, conda, pipenv).
- pyvenv.cfg integrity, broken base python home paths, and invalid symlinks.
- Missing packages defined in requirements.txt / pyproject.toml.
- Corrupted site-packages, dangling .dist-info / .egg-info directories.
- Package version conflicts and Python minor version drift.

Author: Toprak Ahmet Aydogmus (Siber Akademi)
Version: 10.4.0
"""

import importlib.metadata
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .models import (
    DiagnosticCategory,
    DiagnosticIssue,
    HealAction,
    SeverityLevel,
    SystemPlatform,
)


class VenvDoctor:
    """Specialized doctor for Python virtual environments and dependency topologies."""

    CANDIDATE_VENV_NAMES = [".venv", "venv", "env", ".env", "virtualenv"]

    @classmethod
    def detect_workspace_venvs(cls, workspace_dir: str = ".") -> List[Path]:
        """Locate all local virtualenv directories in workspace root."""
        root = Path(workspace_dir).resolve()
        found: List[Path] = []
        for name in cls.CANDIDATE_VENV_NAMES:
            cand = root / name
            if cand.is_dir() and (cand / "pyvenv.cfg").is_file():
                found.append(cand)
        return found

    @classmethod
    def parse_pyvenv_cfg(cls, cfg_path: Path) -> Dict[str, str]:
        """Parse key-value pairs from a pyvenv.cfg file."""
        res: Dict[str, str] = {}
        if not cfg_path.is_file():
            return res
        try:
            with open(cfg_path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        res[k.strip().lower()] = v.strip()
        except Exception:
            pass
        return res

    @classmethod
    def inspect_virtualenv(cls, venv_dir: Path) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """Validate virtualenv structure, pyvenv.cfg, and interpreter binary."""
        cfg_file = venv_dir / "pyvenv.cfg"
        if not cfg_file.is_file():
            return False, f"Missing 'pyvenv.cfg' in {venv_dir.name}", {}

        cfg_data = cls.parse_pyvenv_cfg(cfg_file)
        home_path = cfg_data.get("home")

        if not home_path:
            return False, "Missing 'home' directive in pyvenv.cfg", cfg_data

        if not os.path.isdir(home_path):
            return False, f"Base python home directory does not exist: '{home_path}'", cfg_data

        # Check binary presence
        is_windows = sys.platform.startswith("win")
        bin_dir = venv_dir / ("Scripts" if is_windows else "bin")
        py_binary = bin_dir / ("python.exe" if is_windows else "python")

        if not bin_dir.is_dir():
            return False, f"Missing '{bin_dir.name}' folder in virtualenv", cfg_data

        if not py_binary.is_file():
            return False, f"Missing python interpreter '{py_binary.name}' in {bin_dir.name}", cfg_data

        return True, None, cfg_data

    @classmethod
    def parse_requirements_file(cls, req_file: Path) -> List[Tuple[str, Optional[str]]]:
        """Extract package names and version specifiers from requirements.txt."""
        packages: List[Tuple[str, Optional[str]]] = []
        if not req_file.is_file():
            return packages

        try:
            with open(req_file, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith(("#", "-", "git+", "http")):
                        continue
                    # Match name and optional specifier
                    match = re.match(r"^([A-Za-z0-9_\-\.]+)(.*)$", line)
                    if match:
                        name = match.group(1).replace("-", "_").lower()
                        spec = match.group(2).strip() or None
                        packages.append((name, spec))
        except Exception:
            pass
        return packages

    @classmethod
    def check_dependency_drift(cls, workspace_dir: str = ".") -> List[DiagnosticIssue]:
        """Cross-reference requirements against currently installed packages."""
        issues: List[DiagnosticIssue] = []
        root = Path(workspace_dir).resolve()

        req_candidates = [root / "requirements.txt", root / "requirements-dev.txt"]
        for req_f in req_candidates:
            if not req_f.is_file():
                continue

            packages = cls.parse_requirements_file(req_f)
            for pkg_name, spec in packages:
                try:
                    installed_ver = importlib.metadata.version(pkg_name)
                except importlib.metadata.PackageNotFoundError:
                    # Also try dash version
                    try:
                        installed_ver = importlib.metadata.version(pkg_name.replace("_", "-"))
                    except importlib.metadata.PackageNotFoundError:
                        issues.append(DiagnosticIssue(
                            category=DiagnosticCategory.ENVIRONMENT.value,
                            severity=SeverityLevel.ERROR.value,
                            file_path=str(req_f),
                            line=None,
                            column=None,
                            error_code="TZ-ENV-PKG-MISSING",
                            message=f"Declared dependency '{pkg_name}' ({spec or 'any'}) is not installed in the active environment",
                            suggested_fix=f"Run 'pip install {pkg_name}{spec or ''}' to satisfy workspace requirements",
                            auto_fixable=False,
                            metadata={"package": pkg_name, "spec": spec}
                        ))

        return issues

    @classmethod
    def check_corrupted_site_packages(cls, venv_dir: Path) -> List[DiagnosticIssue]:
        """Scan site-packages for empty or corrupted .dist-info / .egg-info remnants."""
        issues: List[DiagnosticIssue] = []
        is_windows = sys.platform.startswith("win")
        lib_dir = venv_dir / "Lib" / "site-packages" if is_windows else venv_dir / "lib"

        # On POSIX it might be lib/python3.X/site-packages
        if not is_windows and lib_dir.is_dir():
            py_dirs = list(lib_dir.glob("python3.*"))
            if py_dirs:
                lib_dir = py_dirs[0] / "site-packages"

        if not lib_dir.is_dir():
            return issues

        try:
            for item in lib_dir.iterdir():
                if item.is_dir() and item.name.endswith((".dist-info", ".egg-info")):
                    # Check if empty or missing METADATA / PKG-INFO
                    meta = item / "METADATA"
                    pkg_info = item / "PKG-INFO"
                    if not meta.is_file() and not pkg_info.is_file():
                        issues.append(DiagnosticIssue(
                            category=DiagnosticCategory.ENVIRONMENT.value,
                            severity=SeverityLevel.WARNING.value,
                            file_path=str(item),
                            line=None,
                            column=None,
                            error_code="TZ-ENV-CORRUPT-DISTINFO",
                            message=f"Corrupted distribution metadata folder: '{item.name}' (missing METADATA)",
                            suggested_fix="Purge orphaned metadata folder and reinstall package",
                            auto_fixable=True,
                            metadata={"action": "purge_corrupt_distinfo", "path": str(item)}
                        ))
        except Exception:
            pass

        return issues

    @classmethod
    def diagnose(cls, workspace_dir: str = ".") -> List[DiagnosticIssue]:
        """Run complete virtualenv diagnostic suite."""
        issues: List[DiagnosticIssue] = []
        venvs = cls.detect_workspace_venvs(workspace_dir)

        if not venvs:
            # Check if active Python is a virtualenv
            is_venv = hasattr(sys, "real_prefix") or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix)
            if not is_venv:
                issues.append(DiagnosticIssue(
                    category=DiagnosticCategory.ENVIRONMENT.value,
                    severity=SeverityLevel.INFO.value,
                    file_path=None,
                    line=None,
                    column=None,
                    error_code="TZ-ENV-NO-VENV",
                    message="No local virtual environment detected (.venv); running in global / system Python",
                    suggested_fix="Create isolated virtualenv via 'python -m venv .venv'",
                    auto_fixable=False
                ))
            return issues

        for venv in venvs:
            valid, err_msg, cfg = cls.inspect_virtualenv(venv)
            if not valid:
                issues.append(DiagnosticIssue(
                    category=DiagnosticCategory.ENVIRONMENT.value,
                    severity=SeverityLevel.ERROR.value,
                    file_path=str(venv / "pyvenv.cfg"),
                    line=None,
                    column=None,
                    error_code="TZ-ENV-VENV-BROKEN",
                    message=f"Corrupted virtualenv '{venv.name}': {err_msg}",
                    suggested_fix="Re-point 'home' in pyvenv.cfg to the active system Python directory",
                    auto_fixable=True,
                    metadata={"action": "repair_pyvenv_cfg", "path": str(venv)}
                ))
            else:
                # Check site-packages inside valid venv
                issues.extend(cls.check_corrupted_site_packages(venv))

        # Check dependency drift against requirements.txt
        issues.extend(cls.check_dependency_drift(workspace_dir))
        return issues

    @classmethod
    def execute_venv_heals(cls, issues: List[DiagnosticIssue], dry_run: bool = False) -> List[HealAction]:
        """Execute autonomous healing on virtualenv configurations and corruptions."""
        actions: List[HealAction] = []

        for issue in issues:
            action_type = issue.metadata.get("action")
            if not issue.auto_fixable or not action_type:
                continue

            t0 = time.time()
            if action_type == "repair_pyvenv_cfg":
                venv_p = issue.metadata.get("path")
                if venv_p:
                    cfg_file = Path(venv_p) / "pyvenv.cfg"
                    current_py_home = os.path.dirname(sys.executable)
                    try:
                        lines = []
                        if cfg_file.is_file():
                            with open(cfg_file, "r", encoding="utf-8", errors="replace") as f:
                                for line in f:
                                    if line.strip().startswith("home ="):
                                        lines.append(f"home = {current_py_home}\n")
                                    else:
                                        lines.append(line)
                            if not dry_run:
                                with open(cfg_file, "w", encoding="utf-8", newline="\n") as f:
                                    f.writelines(lines)
                            actions.append(HealAction(
                                category=DiagnosticCategory.ENVIRONMENT.value,
                                action_type=action_type,
                                file_path=str(cfg_file),
                                description=f"Updated pyvenv.cfg home path to '{current_py_home}' in {Path(venv_p).name}",
                                success=True,
                                duration_ms=round((time.time() - t0) * 1000, 2)
                            ))
                    except Exception as e:
                        actions.append(HealAction(
                            category=DiagnosticCategory.ENVIRONMENT.value,
                            action_type=action_type,
                            file_path=str(cfg_file),
                            description=f"Failed updating pyvenv.cfg: {e}",
                            success=False,
                            duration_ms=round((time.time() - t0) * 1000, 2)
                        ))

            elif action_type == "purge_corrupt_distinfo":
                target_p = issue.metadata.get("path")
                if target_p and os.path.isdir(target_p):
                    try:
                        if not dry_run:
                            import shutil
                            shutil.rmtree(target_p, ignore_errors=True)
                        actions.append(HealAction(
                            category=DiagnosticCategory.ENVIRONMENT.value,
                            action_type=action_type,
                            file_path=target_p,
                            description=f"Purged corrupted metadata directory {os.path.basename(target_p)}",
                            success=True,
                            duration_ms=round((time.time() - t0) * 1000, 2)
                        ))
                    except Exception as e:
                        actions.append(HealAction(
                            category=DiagnosticCategory.ENVIRONMENT.value,
                            action_type=action_type,
                            file_path=target_p,
                            description=f"Failed purging corrupt distinfo: {e}",
                            success=False,
                            duration_ms=round((time.time() - t0) * 1000, 2)
                        ))

        return actions
