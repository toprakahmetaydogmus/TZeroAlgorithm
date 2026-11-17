"""Conservative, local Python repair with verification and rollback.

Commands are run on the host, not in a sandbox. Only run trusted commands.
Repairs are intentionally limited to cases that can be checked syntactically.
"""
from __future__ import annotations

import ast
import difflib
import io
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time
import tokenize
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from tzero.tzero_jarvis.causal_graph import CausalTemporalGraph


def agent_command_execution_enabled() -> bool:
    """Require the server operator to opt in before agent shell execution."""
    return os.environ.get("TZERO_ALLOW_AGENT_SHELL") == "1"


@dataclass
class ExecutionResult:
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    success: bool
    error_type: Optional[str] = None
    error_line: Optional[int] = None
    error_file: Optional[str] = None
    applied_patches: List[str] = field(default_factory=list)
    resolved: bool = False
    diagnostics: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class RepairProposal:
    path: Path
    original: bytes
    replacement: bytes
    description: str
    diff: str


class SelfHealingExecutionEngine:
    """Propose limited repairs, then retain them only after command success."""

    def __init__(self, causal_graph: Optional[CausalTemporalGraph] = None,
                 work_dir: Optional[str] = None):
        self.causal_graph = causal_graph or CausalTemporalGraph()
        self.work_dir = str(Path(work_dir or os.getcwd()).resolve())

    def run_command(self, command: str, timeout: int = 30) -> ExecutionResult:
        start = time.monotonic()
        try:
            proc = subprocess.run(command, shell=True, capture_output=True,
                                  text=True, errors="replace", timeout=timeout,
                                  cwd=self.work_dir)
            kind, path, line = self.diagnose_error(proc.stderr or proc.stdout) if proc.returncode else (None, None, None)
            return ExecutionResult(command, proc.returncode, proc.stdout, proc.stderr,
                                   round((time.monotonic() - start) * 1000, 2),
                                   proc.returncode == 0, kind, line, path,
                                   resolved=proc.returncode == 0)
        except (OSError, subprocess.TimeoutExpired) as exc:
            return ExecutionResult(command, -1, "", str(exc),
                                   round((time.monotonic() - start) * 1000, 2),
                                   False, type(exc).__name__)

    def diagnose_error(self, error_text: str) -> Tuple[Optional[str], Optional[str], Optional[int]]:
        matches = re.findall(r'File "([^"\n]+)", line (\d+)', error_text or "")
        path, line = (matches[-1][0], int(matches[-1][1])) if matches else (None, None)
        kind = None
        for text in reversed((error_text or "").splitlines()):
            match = re.match(r'^\s*([A-Za-z_][\w.]*(?:Error|Exception))(?::|$)', text)
            if match:
                kind = match.group(1)
                break
        return kind or ("GenericExecutionError" if error_text else None), path, line

    def _target(self, file_path: str) -> Optional[Path]:
        root = Path(self.work_dir)
        path = Path(file_path)
        if not path.is_absolute():
            path = root / path
        # Disallow symlinks in every component, including the target.
        try:
            if any(part.is_symlink() for part in (path, *path.parents)):
                return None
            resolved = path.resolve(strict=True)
            relative = resolved.relative_to(root)
            current = root
            for part in relative.parts:
                if part == "..":
                    return None
                current = current / part
                if current.is_symlink():
                    return None
            return resolved if resolved.is_file() and resolved.suffix == ".py" else None
        except (ValueError, OSError, RuntimeError):
            return None

    def propose_repair(self, file_path: str, error_type: str,
                       error_line: Optional[int], stderr: str) -> Optional[RepairProposal]:
        path = self._target(file_path)
        if path is None:
            return None
        try:
            original = path.read_bytes()
            encoding, _ = tokenize.detect_encoding(io.BytesIO(original).readline)
            source = original.decode(encoding)
        except (OSError, SyntaxError, UnicodeError):
            return None
        lines = source.splitlines(keepends=True)
        if error_type not in ("SyntaxError", "IndentationError") or not error_line or not 1 <= error_line <= len(lines):
            return None
        # Only act on Python's explicit missing-colon diagnostic, and only
        # on simple, single-line compound statements without comments.
        if not re.search(r"expected ['\"]:['\"]", stderr):
            return None
        idx = error_line - 1
        line = lines[idx]
        body = line.rstrip("\r\n")
        if not re.match(r'^\s*(?:async\s+def|def|class|if|elif|else|for|while|with|try|except|finally)\b', body):
            return None
        if body.rstrip().endswith(":") or "#" in body or "\\" in body:
            return None
        ending = line[len(body):]
        lines[idx] = body.rstrip() + ":" + ending
        replacement_text = "".join(lines)
        try:
            ast.parse(replacement_text, filename=str(path))
            replacement = replacement_text.encode(encoding)
        except (SyntaxError, UnicodeError):
            return None
        diff = "".join(difflib.unified_diff(source.splitlines(True), replacement_text.splitlines(True),
                                            fromfile=str(path), tofile=str(path)))
        return RepairProposal(path, original, replacement, f"Add missing colon at line {error_line}", diff)

    def auto_repair_python_file(self, file_path: str, error_type: str,
                                error_line: Optional[int], stderr: str) -> bool:
        """Legacy direct repair: syntax checked, but not command verified."""
        proposal = self.propose_repair(file_path, error_type, error_line, stderr)
        if proposal is None:
            return False
        try:
            return self._replace_if_unchanged(proposal.path, proposal.original, proposal.replacement)
        except OSError:
            return False

    def _replace_if_unchanged(self, path: Path, expected: bytes, replacement: bytes) -> bool:
        """Replace from a same-directory temporary file; refuse observed changes.

        This is not a compare-and-swap: another process can still race the final
        check. Atomic replacement avoids exposing a partially written file.
        """
        if self._target(str(path)) != path or path.read_bytes() != expected:
            return False
        mode = path.stat().st_mode & 0o777
        temp_name = None
        try:
            with tempfile.NamedTemporaryFile(dir=str(path.parent), prefix=".tzero-heal-", delete=False) as temp:
                temp_name = temp.name
                temp.write(replacement)
                temp.flush()
                os.fsync(temp.fileno())
            os.chmod(temp_name, mode)
            if self._target(str(path)) != path or path.read_bytes() != expected:
                return False
            os.replace(temp_name, path)
            temp_name = None
            return True
        finally:
            if temp_name is not None:
                try:
                    os.unlink(temp_name)
                except FileNotFoundError:
                    pass

    def execute_and_heal(self, command: str, max_retries: int = 3) -> ExecutionResult:
        result = self.run_command(command)
        if result.success or max_retries <= 0 or not result.error_file:
            return result
        proposal = self.propose_repair(result.error_file, result.error_type or "", result.error_line,
                                       result.stderr or result.stdout)
        if proposal is None:
            result.diagnostics.append("No supported safe repair proposal found.")
            return result
        try:
            if not self._replace_if_unchanged(proposal.path, proposal.original, proposal.replacement):
                result.diagnostics.append("File changed before repair; no patch applied.")
                return result
            verified = self.run_command(command)
            if verified.success and self._target(str(proposal.path)) == proposal.path and proposal.path.read_bytes() == proposal.replacement:
                verified.applied_patches.append(proposal.description + "\n" + proposal.diff)
                return verified
            if self._replace_if_unchanged(proposal.path, proposal.replacement, proposal.original):
                verified.diagnostics.append("Verification failed; original file restored.")
            else:
                verified.success = False
                verified.resolved = False
                verified.diagnostics.append("File changed during verification; repair is unverified and automatic rollback was skipped.")
            return verified
        except OSError as exc:
            result.diagnostics.append(f"Repair failed: {exc}")
            try:
                if self._replace_if_unchanged(proposal.path, proposal.replacement, proposal.original):
                    result.diagnostics.append("Original file restored after repair error.")
            except OSError as rollback_error:
                result.diagnostics.append(f"Rollback failed: {rollback_error}")
            return result
