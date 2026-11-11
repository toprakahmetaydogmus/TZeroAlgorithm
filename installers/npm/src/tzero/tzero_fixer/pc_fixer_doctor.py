# -*- coding: utf-8 -*-
"""
T-Zero PC Fixer Doctor Classic Facade and Compatibility Layer
============================================================
Provides backward-compatible PCFixerDoctor class for legacy test suites and APIs.
"""

from __future__ import annotations

import ast
import difflib
import json
import os
import re
import shutil
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from tzero.tzero_fixer.models import (
    DiagnosticCategory,
    DiagnosticIssue,
    DiagnosticReport,
    HealAction,
    HealReport,
    SeverityLevel,
)

class PCFixerDoctor:
    """Enterprise-grade self-healing PC, runtime environment, and codebase doctor."""

    COMMON_STDLIB_SYMBOLS = {
        "os": "import os",
        "sys": "import sys",
        "re": "import re",
        "json": "import json",
        "math": "import math",
        "time": "import time",
        "pathlib": "from pathlib import Path",
        "Path": "from pathlib import Path",
        "ast": "import ast",
        "dataclass": "from dataclasses import dataclass",
        "field": "from dataclasses import field",
        "asdict": "from dataclasses import asdict",
        "Dict": "from typing import Dict",
        "List": "from typing import List",
        "Optional": "from typing import Optional",
        "Union": "from typing import Union",
        "Tuple": "from typing import Tuple",
        "Any": "from typing import Any",
        "Callable": "from typing import Callable",
        "Set": "from typing import Set",
    }

    IGNORE_DIRS = {
        ".git", ".svn", ".hg", "__pycache__", ".pytest_cache", ".mypy_cache",
        "node_modules", ".venv", "venv", "env", "build", "dist", ".idea", ".vscode"
    }

    @classmethod
    def check_tools_on_path(cls) -> Dict[str, bool]:
        """Check availability of essential development CLI tools on system PATH."""
        tools = ["git", "python", "pip", "npm", "npx", "code", "cursor"]
        res = {}
        for t in tools:
            res[t] = shutil.which(t) is not None
        return res

    @classmethod
    def inspect_virtualenv(cls, target_dir: str = ".") -> Dict[str, Any]:
        """Check integrity of local virtual environments (.venv, venv, env)."""
        root = Path(target_dir).resolve()
        candidates = [root / ".venv", root / "venv", root / "env"]
        found = None
        for c in candidates:
            if c.is_dir() and (c / "pyvenv.cfg").is_file():
                found = c
                break

        if not found:
            return {
                "active": hasattr(sys, "real_prefix") or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix),
                "detected": False,
                "path": None,
                "valid": True,
                "error": None
            }

        cfg_file = found / "pyvenv.cfg"
        home_path = None
        try:
            with open(cfg_file, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    if line.strip().startswith("home ="):
                        home_path = line.split("=", 1)[1].strip()
                        break
        except Exception as e:
            return {"active": True, "detected": True, "path": str(found), "valid": False, "error": f"Cannot read pyvenv.cfg: {e}"}

        home_valid = bool(home_path and os.path.isdir(home_path))
        return {
            "active": True,
            "detected": True,
            "path": str(found),
            "cfg_home": home_path,
            "valid": home_valid,
            "error": None if home_valid else f"Base python home invalid: '{home_path}'"
        }

    @classmethod
    def scan_syntax_and_imports(cls, file_path: str) -> List[DiagnosticIssue]:
        """Scan a single Python file for syntax flaws, BOM artifacts, and missing imports."""
        issues: List[DiagnosticIssue] = []
        path = Path(file_path)
        if not path.is_file() or path.suffix != ".py":
            return issues

        try:
            with open(path, "rb") as f:
                raw_bytes = f.read()
        except Exception as e:
            issues.append(DiagnosticIssue(
                category="env",
                severity="error",
                file_path=str(path),
                line=None,
                message=f"Permission or read error: {e}",
                suggested_fix="Check file permissions",
                auto_fixable=False
            ))
            return issues

        # Check BOM / Zero-width characters
        if raw_bytes.startswith(b"\xef\xbb\xbf"):
            issues.append(DiagnosticIssue(
                category="encoding",
                severity="warning",
                file_path=str(path),
                line=1,
                message="File contains UTF-8 Byte Order Mark (BOM) which may disrupt interpreters",
                suggested_fix="Strip UTF-8 BOM",
                auto_fixable=True,
                metadata={"action": "strip_bom"}
            ))

        try:
            content = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            issues.append(DiagnosticIssue(
                category="encoding",
                severity="error",
                file_path=str(path),
                line=1,
                message="File encoding is not valid UTF-8",
                suggested_fix="Transcode to clean UTF-8",
                auto_fixable=True,
                metadata={"action": "fix_encoding"}
            ))
            content = raw_bytes.decode("utf-8", errors="replace")

        # Zero-width spaces
        if "\u200b" in content or "\ufeff" in content:
            issues.append(DiagnosticIssue(
                category="encoding",
                severity="warning",
                file_path=str(path),
                line=1,
                message="File contains hidden zero-width spaces causing phantom syntax bugs",
                suggested_fix="Strip zero-width characters",
                auto_fixable=True,
                metadata={"action": "strip_zero_width"}
            ))

        # Check AST parse
        try:
            tree = ast.parse(content, filename=str(path))
        except SyntaxError as se:
            # Analyze syntax error reason
            err_line = se.lineno or 1
            err_msg = se.msg or "Syntax error"
            suggested = "Fix syntax error"
            action = "syntax_fix"

            lines = content.splitlines()
            if 0 < err_line <= len(lines):
                line_str = lines[err_line - 1].strip()
                # Check missing colon
                block_starters = ("def ", "class ", "if ", "elif ", "else", "try", "except", "finally", "for ", "while ", "with ")
                if any(line_str.startswith(b) for b in block_starters) and not line_str.endswith(":"):
                    suggested = "Append missing colon ':' to block definition"
                    action = "append_colon"
                # Check Python 2 print
                elif re.match(r"^print\s+[\"'].*", line_str):
                    suggested = "Convert Python 2 print statement to print(...) function call"
                    action = "convert_print2"

            issues.append(DiagnosticIssue(
                category="syntax",
                severity="error",
                file_path=str(path),
                line=err_line,
                message=f"SyntaxError: {err_msg} on line {err_line}",
                suggested_fix=suggested,
                auto_fixable=True,
                metadata={"action": action, "lineno": err_line}
            ))
            return issues

        # Check missing top-level standard library imports
        imported_symbols: Set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_symbols.add(alias.name.split(".")[0])
                    imported_symbols.add(alias.asname or alias.name)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    imported_symbols.add(alias.asname or alias.name)

        referenced_names: Set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                referenced_names.add(node.id)

        # Builtins
        builtins_set = set(dir(__builtins__))

        for sym, import_stmt in cls.COMMON_STDLIB_SYMBOLS.items():
            if sym in referenced_names and sym not in imported_symbols and sym not in builtins_set:
                issues.append(DiagnosticIssue(
                    category="import",
                    severity="warning",
                    file_path=str(path),
                    line=1,
                    message=f"Referenced symbol '{sym}' is missing explicit import statement",
                    suggested_fix=f"Add '{import_stmt}' at top of file",
                    auto_fixable=True,
                    metadata={"action": "add_import", "symbol": sym, "stmt": import_stmt}
                ))

        return issues

    @classmethod
    def scan_cache_and_bloat(cls, target_dir: str = ".") -> List[DiagnosticIssue]:
        """Scan for orphaned .pyc files, stale git locks, and bloated caches."""
        issues: List[DiagnosticIssue] = []
        root = Path(target_dir).resolve()

        # Check stale .git/index.lock
        git_lock = root / ".git" / "index.lock"
        if git_lock.is_file():
            age_sec = time.time() - os.path.getmtime(git_lock)
            if age_sec > 300:  # older than 5 minutes
                issues.append(DiagnosticIssue(
                    category="cache",
                    severity="warning",
                    file_path=str(git_lock),
                    line=None,
                    message=f"Stale git lockfile detected ({int(age_sec)}s old) blocking git operations",
                    suggested_fix="Remove stale .git/index.lock",
                    auto_fixable=True,
                    metadata={"action": "remove_file", "path": str(git_lock)}
                ))

        # Check orphaned .pyc in __pycache__
        for root_dir, dirs, files in os.walk(str(root)):
            # skip ignored
            dirs[:] = [d for d in dirs if d not in cls.IGNORE_DIRS or d == "__pycache__"]
            if os.path.basename(root_dir) == "__pycache__":
                parent_dir = Path(root_dir).parent
                for f in files:
                    if f.endswith(".pyc"):
                        base_name = f.split(".")[0]
                        py_sibling = parent_dir / f"{base_name}.py"
                        if not py_sibling.is_file():
                            pyc_path = os.path.join(root_dir, f)
                            issues.append(DiagnosticIssue(
                                category="cache",
                                severity="info",
                                file_path=pyc_path,
                                line=None,
                                message=f"Orphaned bytecode {f} has no corresponding .py source file",
                                suggested_fix="Purge orphaned bytecode",
                                auto_fixable=True,
                                metadata={"action": "remove_file", "path": pyc_path}
                            ))

        return issues

    @classmethod
    def diagnose(cls, target_dir: str = ".") -> DiagnosticReport:
        """Run comprehensive diagnostic inspection across environment, workspace, and files."""
        root = Path(target_dir).resolve()
        tools_status = cls.check_tools_on_path()
        venv_status = cls.inspect_virtualenv(target_dir)

        issues: List[DiagnosticIssue] = []

        # Check Python version
        py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        if sys.version_info < (3, 9):
            issues.append(DiagnosticIssue(
                category="env",
                severity="error",
                file_path=None,
                line=None,
                message=f"Python version {py_ver} is below minimum supported 3.9",
                suggested_fix="Upgrade Python to 3.9 or higher",
                auto_fixable=False
            ))

        # Check venv
        if venv_status.get("detected") and not venv_status.get("valid"):
            issues.append(DiagnosticIssue(
                category="env",
                severity="error",
                file_path=os.path.join(venv_status["path"], "pyvenv.cfg"),
                line=None,
                message=f"Virtualenv corrupted: {venv_status.get('error')}",
                suggested_fix="Re-point pyvenv.cfg home to active python interpreter",
                auto_fixable=True,
                metadata={"action": "repair_venv_cfg", "path": venv_status["path"]}
            ))

        # Scan files
        for root_dir, dirs, files in os.walk(str(root)):
            dirs[:] = [d for d in dirs if d not in cls.IGNORE_DIRS]
            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root_dir, file)
                    issues.extend(cls.scan_syntax_and_imports(full_path))

        # Scan cache & bloat
        issues.extend(cls.scan_cache_and_bloat(target_dir))

        # Tally counts
        syntax_errors = sum(1 for i in issues if i.category == "syntax")
        missing_imports = sum(1 for i in issues if i.category == "import")
        env_issues = sum(1 for i in issues if i.category == "env")
        cache_issues = sum(1 for i in issues if i.category in ("cache", "encoding"))

        # Health score calculation
        penalty = (syntax_errors * 20) + (missing_imports * 5) + (env_issues * 15) + (cache_issues * 2)
        score = max(0, min(100, 100 - penalty))

        return DiagnosticReport(
            timestamp=time.time(),
            target_dir=str(root),
            health_score_pct=score,
            total_issues=len(issues),
            syntax_errors=syntax_errors,
            missing_imports=missing_imports,
            env_issues=env_issues,
            cache_issues=cache_issues,
            issues=issues,
            tools_status=tools_status,
            python_version=py_ver,
            virtualenv_status=venv_status
        )

    @classmethod
    def auto_heal(cls, target_dir: str = ".", dry_run: bool = False,
                  fix_syntax: bool = True, add_imports: bool = True,
                  clean_caches: bool = True, repair_venv: bool = True) -> HealReport:
        """Execute autonomous self-healing for detected codebase and environment issues."""
        diag_before = cls.diagnose(target_dir)
        actions: List[HealAction] = []

        files_to_recheck: Set[str] = set()

        for issue in diag_before.issues:
            action_type = issue.metadata.get("action")
            if not issue.auto_fixable or not action_type:
                continue

            # 1. Clean UTF-8 BOM or Zero-width chars
            if action_type in ("strip_bom", "strip_zero_width", "fix_encoding") and issue.file_path:
                try:
                    p = Path(issue.file_path)
                    with open(p, "rb") as f:
                        data = f.read()
                    if action_type == "strip_bom" and data.startswith(b"\xef\xbb\xbf"):
                        data = data[3:]
                    text = data.decode("utf-8", errors="replace")
                    if action_type == "strip_zero_width":
                        text = text.replace("\u200b", "").replace("\ufeff", "")
                    if not dry_run:
                        with open(p, "w", encoding="utf-8", newline="\n") as f:
                            f.write(text)
                    actions.append(HealAction(
                        category="encoding",
                        file_path=issue.file_path,
                        description=f"Sanitized encoding/BOM in {p.name}",
                        success=True
                    ))
                    files_to_recheck.add(issue.file_path)
                except Exception as e:
                    actions.append(HealAction(
                        category="encoding",
                        file_path=issue.file_path,
                        description=f"Failed sanitizing encoding: {e}",
                        success=False
                    ))

            # 2. Fix syntax errors (missing colon, Python 2 print)
            elif action_type in ("append_colon", "convert_print2") and fix_syntax and issue.file_path:
                try:
                    p = Path(issue.file_path)
                    with open(p, "r", encoding="utf-8", errors="replace") as f:
                        lines = f.readlines()
                    lineno = issue.metadata.get("lineno", 1)
                    if 0 < lineno <= len(lines):
                        orig_line = lines[lineno - 1]
                        mod_line = orig_line
                        if action_type == "append_colon":
                            mod_line = orig_line.rstrip("\r\n") + ":\n"
                        elif action_type == "convert_print2":
                            mod_line = re.sub(r"^(\s*)print\s+(.*)$", r"\1print(\2)", orig_line)

                        if orig_line != mod_line:
                            diff = "".join(difflib.unified_diff(
                                [orig_line], [mod_line], fromfile="before", tofile="after"
                            ))
                            lines[lineno - 1] = mod_line
                            if not dry_run:
                                with open(p, "w", encoding="utf-8", newline="\n") as f:
                                    f.writelines(lines)
                            actions.append(HealAction(
                                category="syntax",
                                file_path=issue.file_path,
                                description=f"Patched {action_type} on line {lineno} of {p.name}",
                                success=True,
                                diff=diff
                            ))
                            files_to_recheck.add(issue.file_path)
                except Exception as e:
                    actions.append(HealAction(
                        category="syntax",
                        file_path=issue.file_path,
                        description=f"Failed patching syntax: {e}",
                        success=False
                    ))

            # 3. Add missing standard library import
            elif action_type == "add_import" and add_imports and issue.file_path:
                try:
                    p = Path(issue.file_path)
                    with open(p, "r", encoding="utf-8", errors="replace") as f:
                        lines = f.readlines()
                    stmt = issue.metadata.get("stmt")
                    if stmt:
                        # Find safe insert location (after future imports / docstring or line 0)
                        insert_idx = 0
                        for idx, l in enumerate(lines[:15]):
                            if l.startswith("#") or "coding:" in l or l.startswith('"""') or l.startswith("'''"):
                                insert_idx = idx + 1
                            elif l.startswith("from __future__"):
                                insert_idx = idx + 1

                        lines.insert(insert_idx, f"{stmt}\n")
                        diff = f"+ {stmt}\n"
                        if not dry_run:
                            with open(p, "w", encoding="utf-8", newline="\n") as f:
                                f.writelines(lines)
                        actions.append(HealAction(
                            category="import",
                            file_path=issue.file_path,
                            description=f"Injected missing '{stmt}' into {p.name}",
                            success=True,
                            diff=diff
                        ))
                        files_to_recheck.add(issue.file_path)
                except Exception as e:
                    actions.append(HealAction(
                        category="import",
                        file_path=issue.file_path,
                        description=f"Failed adding import: {e}",
                        success=False
                    ))

            # 4. Remove stale lockfiles or orphaned bytecode
            elif action_type == "remove_file" and clean_caches:
                target_path = issue.metadata.get("path") or issue.file_path
                if target_path and os.path.exists(target_path):
                    try:
                        if not dry_run:
                            os.remove(target_path)
                        actions.append(HealAction(
                            category="cache",
                            file_path=target_path,
                            description=f"Purged {os.path.basename(target_path)}",
                            success=True
                        ))
                    except Exception as e:
                        actions.append(HealAction(
                            category="cache",
                            file_path=target_path,
                            description=f"Failed removing {target_path}: {e}",
                            success=False
                        ))

            # 5. Repair virtualenv config
            elif action_type == "repair_venv_cfg" and repair_venv:
                venv_dir = issue.metadata.get("path")
                if venv_dir:
                    cfg_file = os.path.join(venv_dir, "pyvenv.cfg")
                    curr_py_home = os.path.dirname(sys.executable)
                    try:
                        lines = []
                        if os.path.isfile(cfg_file):
                            with open(cfg_file, "r", encoding="utf-8", errors="replace") as f:
                                for line in f:
                                    if line.strip().startswith("home ="):
                                        lines.append(f"home = {curr_py_home}\n")
                                    else:
                                        lines.append(line)
                            if not dry_run:
                                with open(cfg_file, "w", encoding="utf-8", newline="\n") as f:
                                    f.writelines(lines)
                            actions.append(HealAction(
                                category="env",
                                file_path=cfg_file,
                                description=f"Updated pyvenv.cfg home path to '{curr_py_home}'",
                                success=True
                            ))
                    except Exception as e:
                        actions.append(HealAction(
                            category="env",
                            file_path=cfg_file,
                            description=f"Failed updating pyvenv.cfg: {e}",
                            success=False
                        ))

        # Re-diagnose to evaluate final score
        diag_after = cls.diagnose(target_dir) if not dry_run else diag_before
        successful_heals = sum(1 for a in actions if a.success)

        return HealReport(
            timestamp=time.time(),
            target_dir=str(Path(target_dir).resolve()),
            initial_health_score=diag_before.health_score_pct,
            final_health_score=diag_after.health_score_pct,
            issues_detected=diag_before.total_issues,
            issues_healed=successful_heals,
            dry_run=dry_run,
            actions=actions
        )

    @classmethod
    def render_cli(cls, report: DiagnosticReport, heal_report: Optional[HealReport] = None):
        """Render beautiful, ANSI-colored doctor report to terminal."""
        print("=" * 80)
        print("\033[1;36m🩺 T-ZERO PC-FIXER & ENVIRONMENT AUTONOMOUS DOCTOR\033[0m")
        print("=" * 80)
        print(f"Target Directory: \033[33m{report.target_dir}\033[0m")
        print(f"Python Runtime:   \033[32mv{report.python_version}\033[0m ({sys.executable})")
        print(f"Virtualenv:       \033[32m{report.virtualenv_status.get('path') or 'Global / System'}\033[0m")

        # Tools status
        tools_str = " ".join([
            f"\033[32m[OK] {t}\033[0m" if ok else f"\033[31m[--] {t}\033[0m"
            for t, ok in report.tools_status.items()
        ])
        print(f"CLI Tools:        {tools_str}")

        score_color = "\033[32m" if report.health_score_pct >= 90 else ("\033[33m" if report.health_score_pct >= 70 else "\033[31m")
        print(f"Health Score:     {score_color}{report.health_score_pct} / 100\033[0m")
        print("-" * 80)

        if report.total_issues == 0:
            print("\033[32m✨ Codebase and Environment are in 100% pristine condition! Zero issues found.\033[0m")
        else:
            print(f"Detected Issues: \033[1;31m{report.total_issues}\033[0m "
                  f"(Syntax: {report.syntax_errors}, Imports: {report.missing_imports}, "
                  f"Env: {report.env_issues}, Cache: {report.cache_issues})")
            print()
            for idx, issue in enumerate(report.issues[:15], start=1):
                loc = f"{os.path.basename(issue.file_path or 'system')}:{issue.line or '-'}"
                icon = "\033[31m[FAIL]\033[0m" if issue.severity == "error" else "\033[33m[WARN]\033[0m"
                print(f"  {idx:2d}. {icon} \033[1m{loc:<22}\033[0m {issue.message}")
                print(f"      \033[36mFix:\033[0m {issue.suggested_fix}")

            if len(report.issues) > 15:
                print(f"  ... and {len(report.issues) - 15} more issues.")

        if heal_report:
            print("-" * 80)
            print("\033[1;32m💉 AUTONOMOUS SELF-HEALING RESULTS:\033[0m")
            print(f"  Issues Healed:    \033[32m{heal_report.issues_healed} / {heal_report.issues_detected}\033[0m")
            print(f"  Health Boost:     \033[33m{heal_report.initial_health_score}%\033[0m -> \033[1;32m{heal_report.final_health_score}%\033[0m")
            for a in heal_report.actions:
                status_icon = "\033[32m✔\033[0m" if a.success else "\033[31m✘\033[0m"
                print(f"  {status_icon} [{a.category.upper()}] {a.description}")
                if a.diff:
                    for dline in a.diff.splitlines()[:3]:
                        print(f"      \033[35m{dline}\033[0m")

        print("=" * 80)
