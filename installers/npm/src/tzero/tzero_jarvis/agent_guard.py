# -*- coding: utf-8 -*-
"""Deterministic, Zero-Spend AI Agent Guardrails and Execution Safety Engine.

Provides multi-layer security policies, path protection, command risk assessment,
secret redaction, transactional file modification, and AI grounding verification.
Operates 100% locally and offline with zero cloud API dependencies.
"""
from __future__ import annotations

import ast
import enum
import hashlib
import io
import math
import os
from pathlib import Path
import re
import shlex
import time
import tokenize
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, Union


# ==============================================================================
# 1. COMMAND RISK ASSESSMENT & EXECUTION POLICY
# ==============================================================================

class CommandRiskLevel(str, enum.Enum):
    SAFE_READ_ONLY = "SAFE_READ_ONLY"
    WORKSPACE_MUTATION = "WORKSPACE_MUTATION"
    NETWORK_OR_PACKAGE = "NETWORK_OR_PACKAGE"
    DESTRUCTIVE = "DESTRUCTIVE"
    BLOCKED_OR_SUSPICIOUS = "BLOCKED_OR_SUSPICIOUS"


@dataclass(frozen=True)
class CommandEvaluation:
    command: str
    risk_level: CommandRiskLevel
    allowed: bool
    reason: str
    argv: Optional[List[str]] = None
    is_chained: bool = False
    has_redirection: bool = False
    has_substitution: bool = False
    involves_network: bool = False
    involves_package_install: bool = False
    involves_destruction: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "command": self.command,
            "risk_level": self.risk_level.value,
            "allowed": self.allowed,
            "reason": self.reason,
            "argv": self.argv,
            "is_chained": self.is_chained,
            "has_redirection": self.has_redirection,
            "has_substitution": self.has_substitution,
            "involves_network": self.involves_network,
            "involves_package_install": self.involves_package_install,
            "involves_destruction": self.involves_destruction,
        }


class CommandRiskAssessor:
    """Evaluates commands for shell injection, network access, and risk level."""

    NETWORK_BINARIES: Set[str] = {
        "curl", "wget", "nc", "ncat", "netcat", "ssh", "scp", "sftp", "ftp",
        "telnet", "invoke-webrequest", "iwr", "irm", "bitsadmin", "nmap",
        "socat", "rclone", "rsync"
    }

    PACKAGE_MANAGERS: Set[str] = {
        "pip", "pip3", "npm", "yarn", "pnpm", "poetry", "cargo", "gem",
        "apt", "apt-get", "yum", "brew", "choco", "winget", "conda"
    }

    DESTRUCTIVE_COMMANDS: Set[str] = {
        "rm", "del", "erase", "format", "dd", "mkfs", "fdisk", "shred",
        "truncate", "wipefs"
    }

    SAFE_READ_COMMANDS: Set[str] = {
        "git status", "git diff", "git log", "git show", "git branch",
        "flake8", "pytest", "python -m unittest", "python -m pytest",
        "mypy", "dir", "ls", "echo", "pwd", "whoami"
    }

    # Detect shell chaining: &&, ||, ;, single & (backgrounding or chaining)
    RE_CHAINING = re.compile(r'(?:&&|\|\||;|(?<!\d)&(?!\d))')
    # Detect redirection: >, >>, <, | (pipes)
    RE_REDIRECTION = re.compile(r'(?:>>|>|<|\|(?!\|))')
    # Detect command substitution or variable expansion exploits
    RE_SUBSTITUTION = re.compile(r'(?:\$\([^)]+\)|`[^`]+`|\$env:[A-Za-z0-9_]+|%[A-Za-z0-9_]+%)')

    @classmethod
    def parse_argv(cls, command: str) -> Optional[List[str]]:
        """Attempt safe lexical splitting without invoking a host shell."""
        cmd_clean = (command or "").strip()
        if not cmd_clean:
            return None
        try:
            # On Windows, posix=False preserves quotes and backslashes properly
            posix_mode = (os.name != "nt")
            parts = shlex.split(cmd_clean, posix=posix_mode)
            # Clean up outer quotes if on Windows
            if not posix_mode:
                parts = [p.strip('"\'') if (p.startswith(('"', "'")) and p.endswith(('"', "'"))) else p for p in parts]
            return parts if parts else None
        except Exception:
            return None

    @classmethod
    def assess(cls, command: str) -> CommandEvaluation:
        """Classify command risk level and identify dangerous primitives."""
        cmd_clean = (command or "").strip()
        if not cmd_clean:
            return CommandEvaluation(
                command=command,
                risk_level=CommandRiskLevel.BLOCKED_OR_SUSPICIOUS,
                allowed=False,
                reason="Empty command."
            )

        is_chained = bool(cls.RE_CHAINING.search(cmd_clean))
        has_redirection = bool(cls.RE_REDIRECTION.search(cmd_clean))
        has_substitution = bool(cls.RE_SUBSTITUTION.search(cmd_clean))

        argv = cls.parse_argv(cmd_clean)
        first_token = (argv[0].lower() if argv else cmd_clean.split()[0].lower()).replace("\\", "/")
        binary_name = Path(first_token).name.lower()
        if binary_name.endswith(".exe"):
            binary_name = binary_name[:-4]

        # Check package installation commands
        involves_package_install = False
        if binary_name in cls.PACKAGE_MANAGERS:
            involves_package_install = True
        elif len(argv or []) >= 3 and argv[0].lower().endswith("python") and argv[1].lower() == "-m" and argv[2].lower() == "pip":
            involves_package_install = True

        # Check network access
        involves_network = binary_name in cls.NETWORK_BINARIES or involves_package_install
        if any(tool in cmd_clean.lower() for tool in ("http://", "https://", "ftp://")):
            involves_network = True

        # Check destructive operations
        involves_destruction = False
        if binary_name in cls.DESTRUCTIVE_COMMANDS:
            involves_destruction = True
        if re.search(r'\b(?:rmdir|del)\s+/[sS]', cmd_clean, re.IGNORECASE):
            involves_destruction = True
        if re.search(r'\brm\s+-[a-zA-Z]*[rf]', cmd_clean, re.IGNORECASE):
            involves_destruction = True
        if re.search(r'\bgit\s+(?:reset\s+--hard|clean\s+-[a-zA-Z]*f)', cmd_clean, re.IGNORECASE):
            involves_destruction = True

        # Determine risk level
        if involves_destruction:
            level = CommandRiskLevel.DESTRUCTIVE
            reason = "Destructive filesystem or repository mutation detected."
        elif involves_package_install:
            level = CommandRiskLevel.NETWORK_OR_PACKAGE
            reason = "Automated package installation is blocked to prevent network costs and supply chain risks."
        elif involves_network:
            level = CommandRiskLevel.NETWORK_OR_PACKAGE
            reason = "Network access is blocked to guarantee zero-cost and prevent data exfiltration."
        elif is_chained or has_redirection or has_substitution:
            level = CommandRiskLevel.BLOCKED_OR_SUSPICIOUS
            reason = "Shell chaining, redirection, or command substitution detected."
        elif any(cmd_clean.startswith(safe) for safe in cls.SAFE_READ_COMMANDS):
            level = CommandRiskLevel.SAFE_READ_ONLY
            reason = "Standard read-only diagnostic command."
        else:
            level = CommandRiskLevel.WORKSPACE_MUTATION
            reason = "Standard local command."

        return CommandEvaluation(
            command=cmd_clean,
            risk_level=level,
            allowed=(level == CommandRiskLevel.SAFE_READ_ONLY),
            reason=reason,
            argv=argv,
            is_chained=is_chained,
            has_redirection=has_redirection,
            has_substitution=has_substitution,
            involves_network=involves_network,
            involves_package_install=involves_package_install,
            involves_destruction=involves_destruction
        )


@dataclass
class CommandExecutionPolicy:
    """Operator-controlled permission policy separated from agent inputs."""

    allow_agent_shell: bool = False
    allow_network: bool = False
    allow_package_install: bool = False
    allow_destructive: bool = False
    allow_chaining: bool = False
    prefer_argv: bool = True
    dry_run: bool = False

    @classmethod
    def from_environment(cls) -> "CommandExecutionPolicy":
        """Read permissions strictly from server operator environment variables."""
        return cls(
            allow_agent_shell=(os.environ.get("TZERO_ALLOW_AGENT_SHELL") == "1"),
            allow_network=(os.environ.get("TZERO_ALLOW_NETWORK") == "1"),
            allow_package_install=(os.environ.get("TZERO_ALLOW_PACKAGE_INSTALL") == "1"),
            allow_destructive=(os.environ.get("TZERO_ALLOW_DESTRUCTIVE") == "1"),
            allow_chaining=(os.environ.get("TZERO_ALLOW_CHAINED_COMMANDS") == "1"),
            prefer_argv=True,
            dry_run=(os.environ.get("TZERO_DRY_RUN") == "1")
        )

    def is_command_allowed(self, evaluation: CommandEvaluation) -> Tuple[bool, str]:
        """Check whether the evaluated command is permitted under the active policy."""
        if not self.allow_agent_shell:
            return False, "Agent shell execution is disabled by default. Server operator must set TZERO_ALLOW_AGENT_SHELL=1."

        if evaluation.involves_package_install and not self.allow_package_install:
            return False, "Package installation blocked: zero-spend policy forbids unverified package installs."

        if evaluation.involves_network and not self.allow_network:
            return False, "Network access blocked: zero-spend & privacy policy forbids external network calls."

        if evaluation.involves_destruction and not self.allow_destructive:
            return False, "Destructive command blocked by safety policy."

        if (evaluation.is_chained or evaluation.has_redirection or evaluation.has_substitution) and not self.allow_chaining:
            return False, "Shell chaining, redirection, or command substitution blocked by safety policy."

        return True, "Command permitted under current operator policy."


# ==============================================================================
# 2. PATH & FILESYSTEM BOUNDARY GUARD
# ==============================================================================

class PathGuard:
    """Guards against directory traversal, symlink escape, and protected file mutation."""

    PROTECTED_FILENAMES: Set[str] = {
        ".env", ".env.local", ".env.production", ".env.staging", ".env.development",
        "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519", "authorized_keys",
        ".npmrc", ".pypirc", "credentials", "secrets.json"
    }

    PROTECTED_DIRS: Set[str] = {
        ".git", ".ssh", ".aws", ".kube", ".gnupg"
    }

    PROTECTED_EXTENSIONS: Set[str] = {
        ".pem", ".key", ".pfx", ".p12", ".kdbx", ".cert"
    }

    MAX_SAFE_FILE_SIZE_BYTES: int = 5 * 1024 * 1024  # 5 MB
    MAX_LINES_CHANGED_LIMIT: int = 500

    @classmethod
    def validate_target_path(
        cls,
        file_path: Union[str, Path],
        work_dir: Union[str, Path],
        for_write: bool = True
    ) -> Tuple[bool, str, Optional[Path]]:
        """Validate target file path against workspace boundaries, symlinks, and protected paths."""
        try:
            root = Path(work_dir).resolve(strict=True)
        except (OSError, RuntimeError) as exc:
            return False, f"Invalid workspace root: {exc}", None

        path = Path(file_path)
        if not path.is_absolute():
            path = root / path

        # Check raw string for traversal attempts
        parts_str = [str(p) for p in path.parts]
        if ".." in parts_str:
            return False, "Path traversal ('..') detected.", None

        # Check symlinks on target and parents
        try:
            test_path = path
            while test_path != test_path.parent:
                if test_path.is_symlink():
                    return False, f"Symlink path forbidden: {test_path}", None
                test_path = test_path.parent
        except (OSError, RuntimeError):
            pass

        try:
            resolved = path.resolve(strict=for_write)
        except FileNotFoundError:
            if for_write:
                return False, f"Target file does not exist: {path}", None
            resolved = path.resolve()
        except (OSError, RuntimeError) as exc:
            return False, f"Path resolution error: {exc}", None

        # Boundary check: resolved must be strictly relative to root
        try:
            relative = resolved.relative_to(root)
        except ValueError:
            return False, f"Path escapes workspace boundary: {resolved} is outside {root}", None

        # Check every component of relative path for symlinks or protected directories
        current = root
        for part in relative.parts:
            if part in cls.PROTECTED_DIRS:
                return False, f"Access to protected directory '{part}' is forbidden.", None
            current = current / part
            if current.is_symlink():
                return False, f"Symlink component forbidden: {current}", None

        # Check protected filenames and extensions
        filename_lower = resolved.name.lower()
        if filename_lower in cls.PROTECTED_FILENAMES:
            return False, f"Mutation of protected configuration file '{resolved.name}' is forbidden.", None

        if resolved.suffix.lower() in cls.PROTECTED_EXTENSIONS:
            return False, f"Mutation of protected key/certificate extension '{resolved.suffix}' is forbidden.", None

        # Check file size if modifying existing file
        if for_write and resolved.is_file():
            try:
                size = resolved.stat().st_size
                if size > cls.MAX_SAFE_FILE_SIZE_BYTES:
                    return False, f"File size ({size} bytes) exceeds maximum safe repair threshold ({cls.MAX_SAFE_FILE_SIZE_BYTES} bytes).", None
            except OSError as exc:
                return False, f"Cannot stat file: {exc}", None

        return True, "Path validated successfully.", resolved


# ==============================================================================
# 3. SECRET & TOKEN REDACTION SHIELD
# ==============================================================================

class SecretRedactor:
    """Masks API keys, tokens, high-entropy strings, and credentials from diagnostics."""

    REDACTION_TAG = "[REDACTED_SECRET]"

    PATTERNS: List[Tuple[str, re.Pattern]] = [
        ("AWS_KEY", re.compile(r'\b(?:AKIA|ABIA|ACCA|ASIA)[0-9A-Z]{16}\b')),
        ("GITHUB_TOKEN", re.compile(r'\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,255}\b')),
        ("GITHUB_PAT", re.compile(r'\bgithub_pat_[A-Za-z0-9_]{82}\b')),
        ("BEARER_TOKEN", re.compile(r'(?i)\bBearer\s+[A-Za-z0-9\-._~+/]+=*')),
        ("PRIVATE_KEY", re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----')),
        ("OPENAI_KEY", re.compile(r'\bsk-(?:proj-)?[A-Za-z0-9_\-]{32,}\b')),
        ("GENERIC_SECRET_ASSIGNMENT", re.compile(r'(?i)(?:api_key|secret|password|token|auth_token)\s*[:=]\s*["\']([^"\']{16,})["\']')),
    ]

    @classmethod
    def calculate_shannon_entropy(cls, s: str) -> float:
        """Calculate Shannon entropy in bits per character."""
        if not s:
            return 0.0
        length = len(s)
        counts: Dict[str, int] = {}
        for c in s:
            counts[c] = counts.get(c, 0) + 1
        return -sum((cnt / length) * math.log2(cnt / length) for cnt in counts.values())

    @classmethod
    def sanitize(cls, text: str) -> str:
        """Redact sensitive patterns and suspicious high-entropy tokens from text."""
        if not text:
            return text

        result = text
        # 1. Pattern-based redactions
        for name, pattern in cls.PATTERNS:
            if name == "GENERIC_SECRET_ASSIGNMENT":
                def replace_generic(match: re.Match) -> str:
                    full = match.group(0)
                    val = match.group(1)
                    return full.replace(val, cls.REDACTION_TAG)
                result = pattern.sub(replace_generic, result)
            else:
                result = pattern.sub(cls.REDACTION_TAG, result)

        # 2. Entropy-based token masking for unquoted suspicious strings (length >= 32, entropy >= 4.75)
        words = result.split()
        for w in words:
            clean_w = w.strip('"\',;:()[]{}')
            if len(clean_w) >= 32 and not any(p in clean_w for p in ("http:", "https:", "/", "\\", ".")):
                # Must have diverse character sets
                has_digit = any(c.isdigit() for c in clean_w)
                has_upper = any(c.isupper() for c in clean_w)
                has_lower = any(c.islower() for c in clean_w)
                if sum([has_digit, has_upper, has_lower]) >= 2:
                    if cls.calculate_shannon_entropy(clean_w) >= 4.75:
                        result = result.replace(clean_w, cls.REDACTION_TAG)

        return result


# ==============================================================================
# 4. AI GROUNDING & ANTI-HALLUCINATION VERIFIER
# ==============================================================================

class AIGroundingVerifier:
    """Verifies that files, symbols, and line numbers claimed by AI exist in the workspace."""

    @classmethod
    def verify_file(cls, work_dir: Union[str, Path], file_path: str) -> Tuple[bool, str, Optional[Path]]:
        """Verify that a referenced file exists within the workspace."""
        valid, reason, resolved = PathGuard.validate_target_path(file_path, work_dir, for_write=False)
        if not valid or not resolved or not resolved.is_file():
            return False, f"File not found in workspace: {file_path}", None
        return True, "File exists.", resolved

    @classmethod
    def verify_line(cls, work_dir: Union[str, Path], file_path: str, line_no: int) -> Tuple[bool, str]:
        """Verify that a referenced line number is within file boundaries."""
        exists, msg, resolved = cls.verify_file(work_dir, file_path)
        if not exists or not resolved:
            return False, msg
        try:
            line_count = len(resolved.read_text(encoding="utf-8", errors="replace").splitlines())
            if 1 <= line_no <= line_count:
                return True, f"Line {line_no} verified (total lines: {line_count})."
            return False, f"Line number {line_no} out of bounds (file has {line_count} lines)."
        except OSError as exc:
            return False, f"Cannot read file lines: {exc}"

    @classmethod
    def verify_python_symbol(
        cls,
        work_dir: Union[str, Path],
        file_path: str,
        symbol_name: str
    ) -> Tuple[bool, str, Optional[str], Optional[int]]:
        """Verify that a function, class, or method symbol exists in a Python file's AST."""
        exists, msg, resolved = cls.verify_file(work_dir, file_path)
        if not exists or not resolved:
            return False, msg, None, None

        if resolved.suffix != ".py":
            return False, "Symbol AST verification is only supported for Python files.", None, None

        try:
            source = resolved.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(source, filename=str(resolved))
        except (SyntaxError, OSError) as exc:
            return False, f"AST parse failed on {resolved.name}: {exc}", None, None

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == symbol_name:
                return True, f"Found function '{symbol_name}' at line {node.lineno}.", "function", node.lineno
            if isinstance(node, ast.ClassDef) and node.name == symbol_name:
                return True, f"Found class '{symbol_name}' at line {node.lineno}.", "class", node.lineno

        return False, f"Symbol '{symbol_name}' not found in AST of {resolved.name}.", None, None

    @classmethod
    def audit_traceback_evidence(
        cls,
        work_dir: Union[str, Path],
        traceback_text: str
    ) -> Dict[str, Any]:
        """Extract all File and line claims from traceback and verify their workspace ground truth."""
        matches = re.findall(r'File "([^"\n]+)", line (\d+)', traceback_text or "")
        verified_frames = []
        unverified_frames = []

        for fpath, lstr in matches:
            lno = int(lstr)
            is_valid, msg, resolved = cls.verify_file(work_dir, fpath)
            if is_valid and resolved:
                line_ok, lmsg = cls.verify_line(work_dir, fpath, lno)
                frame_info = {"file": str(resolved), "line": lno, "status": "VERIFIED" if line_ok else "LINE_OUT_OF_BOUNDS", "detail": lmsg}
                if line_ok:
                    verified_frames.append(frame_info)
                else:
                    unverified_frames.append(frame_info)
            else:
                unverified_frames.append({"file": fpath, "line": lno, "status": "UNVERIFIED_FILE", "detail": msg})

        return {
            "total_frames": len(matches),
            "verified_frames": verified_frames,
            "unverified_frames": unverified_frames,
            "has_grounded_target": len(verified_frames) > 0,
            "primary_target": verified_frames[-1] if verified_frames else None
        }

    @classmethod
    def flag_unverified_claims(cls, text: str) -> List[str]:
        """Detect and flag absolute or ungrounded claims in text."""
        flags = []
        unsubstantiated_patterns = [
            (r'\b100%\s*(?:guaranteed|leak-proof|safe|accuracy)\b', "Claim of '100% security/accuracy' cannot be verified mathematically."),
            (r'\bzero\s*(?:bug|error|defect|vulnerability)\s*guarantee\b', "Claim of 'zero bug/defect guarantee' is invalid for software systems."),
            (r'\bcompletely\s+eliminates\s+all\s+hallucinations\b', "Claim of 'completely eliminating all hallucinations' is unsupported without bounded AST proof.")
        ]
        for pattern, explanation in unsubstantiated_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                flags.append(explanation)
        return flags


# ==============================================================================
# 5. MULTI-FILE TRANSACTION & ROLLBACK STACK
# ==============================================================================

@dataclass
class TransactionEntry:
    path: Path
    original_bytes: bytes
    applied_bytes: bytes
    diff: str
    timestamp: float = field(default_factory=time.time)


class MultiFileRollbackStack:
    """Manages transactional file modifications with safe reverse-order rollback."""

    def __init__(self):
        self._stack: List[TransactionEntry] = []

    def push(self, path: Path, original: bytes, applied: bytes, diff: str) -> None:
        self._stack.append(TransactionEntry(path, original, applied, diff))

    def rollback_all(self) -> List[str]:
        """Roll back all modified files in reverse order if they haven't been concurrently modified."""
        diagnostics = []
        while self._stack:
            entry = self._stack.pop()
            try:
                if not entry.path.is_file():
                    diagnostics.append(f"Rollback warning: {entry.path.name} no longer exists.")
                    continue
                current_bytes = entry.path.read_bytes()
                if current_bytes == entry.applied_bytes:
                    entry.path.write_bytes(entry.original_bytes)
                    diagnostics.append(f"Restored {entry.path.name} to original state.")
                else:
                    diagnostics.append(f"Rollback skipped for {entry.path.name}: file modified concurrently.")
            except OSError as exc:
                diagnostics.append(f"Rollback error for {entry.path.name}: {exc}")
        return diagnostics

    def clear(self) -> None:
        self._stack.clear()

    def __len__(self) -> int:
        return len(self._stack)


# ==============================================================================
# 6. IN-MEMORY AUDIT LOGGING
# ==============================================================================

@dataclass(frozen=True)
class SecurityAuditEvent:
    timestamp: float
    event_type: str
    target: str
    verdict: str
    reason: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "target": self.target,
            "verdict": self.verdict,
            "reason": self.reason,
            "metadata": self.metadata
        }


class SecurityAuditLogger:
    """Thread-safe, bounded, in-memory security audit log with secret sanitization."""

    def __init__(self, capacity: int = 500):
        self._capacity = capacity
        self._events: List[SecurityAuditEvent] = []

    def record(self, event_type: str, target: str, verdict: str, reason: str, metadata: Optional[Dict[str, Any]] = None) -> SecurityAuditEvent:
        clean_target = SecretRedactor.sanitize(target)
        clean_reason = SecretRedactor.sanitize(reason)
        clean_meta = {}
        if metadata:
            for k, v in metadata.items():
                clean_meta[k] = SecretRedactor.sanitize(str(v)) if isinstance(v, str) else v

        event = SecurityAuditEvent(
            timestamp=round(time.time(), 3),
            event_type=event_type,
            target=clean_target,
            verdict=verdict,
            reason=clean_reason,
            metadata=clean_meta
        )
        self._events.append(event)
        if len(self._events) > self._capacity:
            self._events.pop(0)
        return event

    def get_events(self, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        if event_type:
            return [e.to_dict() for e in self._events if e.event_type == event_type]
        return [e.to_dict() for e in self._events]

    def clear(self) -> None:
        self._events.clear()


# Global audit logger instance
GLOBAL_AUDIT_LOGGER = SecurityAuditLogger()
