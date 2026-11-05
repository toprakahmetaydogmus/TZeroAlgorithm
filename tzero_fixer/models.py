# -*- coding: utf-8 -*-
"""T-Zero Autonomous PC-Fixer & Codebase Doctor: Core Models and Enums.

Defines all diagnostic entities, severity tiers, platform descriptors,
diff structures, transactional rollback manifests, and reporting schemas.

Author: Toprak Ahmet Aydogmus (Siber Akademi)
Version: 10.4.0
Master Edition / Security Certified Zero-Leak
"""

import enum
import json
import os
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union


class SeverityLevel(enum.Enum):
    """Severity classification for diagnostic issues."""
    CRITICAL = "critical"      # Code fails to parse, interpreter won't start, secrets leaked
    ERROR = "error"            # Runtime crash, missing import, broken virtualenv
    WARNING = "warning"        # Anti-pattern, circular import, deprecated API, stale lock
    INFO = "info"              # Orphaned bytecode, optimization advice, code smell
    CLEAN = "clean"            # Perfectly healthy check

    @property
    def ansi_color(self) -> str:
        if self == SeverityLevel.CRITICAL:
            return "\033[1;31m"  # Bold Red
        elif self == SeverityLevel.ERROR:
            return "\033[31m"    # Red
        elif self == SeverityLevel.WARNING:
            return "\033[33m"    # Yellow
        elif self == SeverityLevel.INFO:
            return "\033[36m"    # Cyan
        return "\033[32m"        # Green

    @property
    def badge(self) -> str:
        if self == SeverityLevel.CRITICAL:
            return "[CRIT]"
        elif self == SeverityLevel.ERROR:
            return "[FAIL]"
        elif self == SeverityLevel.WARNING:
            return "[WARN]"
        elif self == SeverityLevel.INFO:
            return "[INFO]"
        return "[PASS]"


class DiagnosticCategory(enum.Enum):
    """Category classification for doctor checks."""
    SYNTAX = "syntax"              # AST syntax, indentation, unclosed strings, delimiters
    IMPORTS = "imports"            # Missing imports, dead imports, circular dependency cycles
    ENVIRONMENT = "environment"    # Python runtime, virtualenvs, PATH tools, shims
    SECURITY = "security"          # Hardcoded secrets, insecure deserialization, SQL injection
    SMELLS = "smells"              # Mutable defaults, bare except, unclosed file handles
    ENCODING = "encoding"          # UTF-8 BOM, zero-width characters, non-ascii noise
    CACHE = "cache"                # Orphaned .pyc files, stale .git locks, temp bloat
    POLYGLOT = "polyglot"          # Node, Rust, Go, Git, Docker system diagnostics
    TYPE_HINTS = "type_hints"      # PEP-484 / 585 / 604 type annotation modernizations
    PERFORMANCE = "performance"    # Quadratic string concatenations, memory leaks
    WORKSPACE = "workspace"        # Workspace layout, git, VCS, locks, editorconfig
    DEPENDENCY = "dependency"      # PEP 517 build, virtualenv packages, ABI drift


# Backward & forward compatibility alias bindings
DiagnosticCategory.PYTHON_SYNTAX = DiagnosticCategory.SYNTAX  # type: ignore
DiagnosticCategory.CODE_SMELLS = DiagnosticCategory.SMELLS    # type: ignore
DiagnosticCategory.SECURITY_CREDENTIAL = DiagnosticCategory.SECURITY  # type: ignore
DiagnosticCategory.POLYGLOT_CONFIG = DiagnosticCategory.POLYGLOT      # type: ignore
DiagnosticCategory.SYSTEM_ENVIRONMENT = DiagnosticCategory.ENVIRONMENT  # type: ignore


class SystemPlatform(enum.Enum):
    """Host operating system platform."""
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"
    UNKNOWN = "unknown"

    @classmethod
    def current(cls) -> "SystemPlatform":
        if sys.platform.startswith("win"):
            return cls.WINDOWS
        elif sys.platform.startswith("linux"):
            return cls.LINUX
        elif sys.platform.startswith("darwin"):
            return cls.MACOS
        return cls.UNKNOWN


@dataclass
class DiffHunk:
    """Represents a unified diff modification hunk."""
    file_path: str
    old_start_line: int
    old_line_count: int
    new_start_line: int
    new_line_count: int
    header: str
    lines: List[str] = field(default_factory=list)

    def to_unified_string(self) -> str:
        res = [f"@@ -{self.old_start_line},{self.old_line_count} +{self.new_start_line},{self.new_line_count} @@ {self.header}"]
        res.extend(self.lines)
        return "\n".join(res)


@dataclass
class DiagnosticIssue:
    """Represents a single detected diagnostic defect in codebase or environment."""
    category: str                       # Value of DiagnosticCategory
    severity: str                       # Value of SeverityLevel
    file_path: Optional[str] = None     # Path to source file or system config
    line: Optional[int] = None          # Line number (1-based), None for workspace/env
    column: Optional[int] = None        # Column offset (0-based)
    error_code: str = ""                # e.g., 'TZ-SYN-001', 'TZ-SEC-042', 'TZ-ENV-003'
    message: str = ""                   # Human readable problem statement
    suggested_fix: str = ""             # Proposed solution or remedy
    auto_fixable: bool = True           # Can T-Zero auto-heal this defect?
    confidence_score: float = 1.0       # 0.0 to 1.0 confidence in auto-heal safety
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __init__(
        self,
        category: Union[str, DiagnosticCategory] = "syntax",
        severity: Union[str, SeverityLevel] = "warning",
        file_path: Optional[str] = None,
        line: Optional[int] = None,
        column: Optional[int] = None,
        error_code: str = "",
        message: str = "",
        suggested_fix: str = "",
        auto_fixable: bool = True,
        confidence_score: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
        # Tolerant alias kwargs:
        code: Optional[str] = None,
        remediation: Optional[str] = None,
        line_number: Optional[int] = None,
        suggested_action: Any = None,
        **extra: Any,
    ):
        self.category = category.value if isinstance(category, enum.Enum) else str(category)
        self.severity = severity.value if isinstance(severity, enum.Enum) else str(severity)
        self.file_path = file_path
        self.line = line if line is not None else line_number
        self.column = column
        self.error_code = error_code or code or ""
        self.message = message
        self.suggested_fix = suggested_fix or remediation or ""
        self.auto_fixable = auto_fixable
        self.confidence_score = confidence_score
        self.metadata = metadata or {}
        if suggested_action:
            self.metadata["suggested_action"] = str(suggested_action)
        if extra:
            self.metadata.update(extra)

    @property
    def code(self) -> str:
        return self.error_code

    @property
    def remediation(self) -> str:
        return self.suggested_fix

    @property
    def line_number(self) -> Optional[int]:
        return self.line

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @property
    def formatted_location(self) -> str:
        if not self.file_path:
            return "system"
        bname = os.path.basename(self.file_path)
        if self.line is not None:
            if self.column is not None:
                return f"{bname}:{self.line}:{self.column}"
            return f"{bname}:{self.line}"
        return bname


@dataclass
class HealAction:
    """Record of a surgical repair action executed on disk or in memory."""
    category: str = "workspace"         # Value of DiagnosticCategory
    file_path: Optional[str] = None     # Target file modified
    description: str = ""               # Summary of action
    success: bool = True                # Did the patch succeed?
    diff: Optional[str] = None          # Unified diff preview
    action_type: str = "patch"          # e.g., 'append_colon', 'inject_import', 'strip_bom'
    backup_path: Optional[str] = None   # Path to original file snapshot in rollback buffer
    duration_ms: float = 0.0            # Execution latency in milliseconds
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __init__(
        self,
        category: Optional[Any] = None,
        file_path: Optional[str] = None,
        description: str = "",
        success: bool = True,
        diff: Optional[str] = None,
        action_type: str = "patch",
        backup_path: Optional[str] = None,
        duration_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
        # Tolerant alias kwargs:
        issue: Optional[Any] = None,
        details: Optional[str] = None,
        **extra: Any,
    ):
        if issue is not None:
            cat_val = getattr(issue, "category", "workspace")
            self.category = cat_val.value if hasattr(cat_val, "value") else str(cat_val)
            self.file_path = getattr(issue, "file_path", file_path)
        else:
            cat_val = category or "workspace"
            self.category = cat_val.value if hasattr(cat_val, "value") else str(cat_val)
            self.file_path = file_path

        self.description = details if details is not None else description
        self.success = success
        self.diff = diff
        self.action_type = action_type
        self.backup_path = backup_path
        self.duration_ms = duration_ms
        self.metadata = metadata or {}
        if extra:
            self.metadata.update(extra)

    @property
    def details(self) -> str:
        return self.description

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ToolStatus:
    """Status of an external development tool on system PATH."""
    name: str                           # 'git', 'python', 'npm', etc.
    available: bool                     # Found on PATH?
    executable_path: Optional[str]      # Absolute path to binary
    version_str: Optional[str]          # Reported version string
    is_compatible: bool = True          # Compatible with minimum requirements?
    notes: Optional[str] = None         # Warnings or recommendation notes


@dataclass
class EnvironmentSnapshot:
    """Detailed health matrix of the host operating system and execution runtime."""
    platform: str                       # 'windows', 'linux', 'macos'
    os_release: str                     # OS version / kernel details
    python_version: str                 # Active interpreter version
    python_executable: str              # Active sys.executable
    python_architecture: str           # '64bit' or '32bit'
    is_virtualenv_active: bool          # Is active interpreter in a venv?
    virtualenv_root: Optional[str]      # Root directory of virtualenv
    virtualenv_valid: bool              # Is venv properly linked and uncorrupted?
    virtualenv_error: Optional[str]     # Diagnostic message if venv broken
    cpu_cores: int                      # Total CPU core count
    total_ram_gb: float                 # Total system memory in Gigabytes
    available_ram_gb: float             # Available free memory in Gigabytes
    temp_dir_path: str                  # System temporary folder
    tools: Dict[str, ToolStatus] = field(default_factory=dict)
    env_vars_healthy: bool = True       # PATH and critical variables properly formatted?


@dataclass
class DiagnosticReport:
    """Complete diagnostic audit result across all categories."""
    timestamp: float                    # Epoch seconds
    target_dir: str                     # Workspace scanned
    health_score_pct: int               # 0 to 100 overall health rating
    total_issues: int                   # Count of all issues detected
    syntax_errors: int = 0              # Issues in SYNTAX category
    missing_imports: int = 0            # Issues in IMPORTS category
    env_issues: int = 0                 # Issues in ENVIRONMENT category
    cache_issues: int = 0               # Issues in CACHE / ENCODING categories
    issues: List[DiagnosticIssue] = field(default_factory=list) # Complete list of issues
    critical_count: int = 0             # Count of critical severity issues
    error_count: int = 0                # Count of error severity issues
    warning_count: int = 0              # Count of warning severity issues
    info_count: int = 0                 # Count of info/advisory issues
    security_leaks: int = 0             # Issues in SECURITY category
    code_smells: int = 0                # Issues in SMELLS category
    tools_status: Dict[str, bool] = field(default_factory=dict)
    python_version: str = ""
    virtualenv_status: Dict[str, Any] = field(default_factory=dict)
    environment: Optional[EnvironmentSnapshot] = None # Host system environment metrics
    scan_duration_ms: float = 0.0       # Time taken to scan in milliseconds
    scanned_file_count: int = 0         # Total source files inspected

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_sarif(self) -> Dict[str, Any]:
        """Convert diagnostic issues to standard OASIS SARIF v2.1.0 format."""
        results = []
        for issue in self.issues:
            level = "error" if issue.severity in ("critical", "error") else ("warning" if issue.severity == "warning" else "note")
            loc = {
                "physicalLocation": {
                    "artifactLocation": {"uri": issue.file_path or "system"},
                    "region": {
                        "startLine": issue.line or 1,
                        "startColumn": (issue.column or 0) + 1
                    }
                }
            }
            results.append({
                "ruleId": issue.error_code,
                "level": level,
                "message": {"text": f"{issue.message}. Suggestion: {issue.suggested_fix}"},
                "locations": [loc],
                "properties": {"category": issue.category, "autoFixable": issue.auto_fixable}
            })

        return {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [{
                "tool": {
                    "driver": {
                        "name": "T-Zero PC-Fixer Doctor",
                        "version": "10.4.0",
                        "informationUri": "https://tzero-indol.vercel.app"
                    }
                },
                "results": results
            }]
        }


@dataclass
class RollbackManifest:
    """Manifest of files backed up before autonomous healing for atomic rollback."""
    transaction_id: str
    timestamp: float
    target_dir: str
    backup_dir: str
    backed_up_files: Dict[str, str] = field(default_factory=dict)  # original_path -> backup_path

    def save(self, manifest_file: str):
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def load(cls, manifest_file: str) -> "RollbackManifest":
        with open(manifest_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(**data)


@dataclass
class HealReport:
    """Comprehensive outcome report of autonomous self-healing execution."""
    timestamp: float                    # Execution completion timestamp
    target_dir: str                     # Workspace path
    initial_health_score: int           # Health score before repair (0-100)
    final_health_score: int             # Health score after repair (0-100)
    issues_detected: int                # Total issues initially found
    issues_healed: int                  # Total issues successfully repaired
    dry_run: bool                       # True if preview mode without writing
    actions: List[HealAction]           # List of individual repair operations
    transaction_id: str = ""            # Unique ID for rollback tracking
    backup_manifest: Optional[RollbackManifest] = None
    execution_duration_ms: float = 0.0  # Total time taken in milliseconds

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @property
    def is_fully_healthy(self) -> bool:
        return self.final_health_score >= 95
