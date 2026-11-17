"""Conservative, local Python repair with verification, policy guards, and rollback.

Commands are run locally with risk assessment and secret redaction.
Repairs are intentionally limited to cases that can be checked syntactically
and verified against local workspace ground truth.
"""
from __future__ import annotations

import ast
import difflib
import hashlib
import io
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time
import tokenize
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from tzero.tzero_jarvis.causal_graph import CausalTemporalGraph
from tzero.tzero_jarvis.agent_guard import (
    CommandRiskLevel,
    CommandEvaluation,
    CommandRiskAssessor,
    CommandExecutionPolicy,
    PathGuard,
    SecretRedactor,
    AIGroundingVerifier,
    MultiFileRollbackStack,
    GLOBAL_AUDIT_LOGGER,
)


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
    risk_level: Optional[str] = None
    blocked_by_policy: bool = False
    dry_run: bool = False
    verified_evidence: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class RepairProposal:
    path: Path
    original: bytes
    replacement: bytes
    description: str
    diff: str
    sha256: str = ""


class SelfHealingExecutionEngine:
    """Propose limited repairs, then retain them only after command success."""

    def __init__(
        self,
        causal_graph: Optional[CausalTemporalGraph] = None,
        work_dir: Optional[str] = None,
        policy: Optional[CommandExecutionPolicy] = None,
        enforce_agent_policy: bool = False
    ):
        self.causal_graph = causal_graph or CausalTemporalGraph()
        self.work_dir = str(Path(work_dir or os.getcwd()).resolve())
        self.policy = policy or CommandExecutionPolicy.from_environment()
        self.enforce_agent_policy = enforce_agent_policy or (os.environ.get("TZERO_ENFORCE_AGENT_POLICY") == "1")
        self.rollback_stack = MultiFileRollbackStack()
        self._attempted_patch_hashes: Set[str] = set()

    def run_command(self, command: str, timeout: int = 30, dry_run: Optional[bool] = None) -> ExecutionResult:
        """Execute command with risk assessment, policy gate, and secret sanitization."""
        evaluation = CommandRiskAssessor.assess(command)

        # Enforce operator security policy when running under agent execution context
        if self.enforce_agent_policy:
            allowed, reason = self.policy.is_command_allowed(evaluation)
            if not allowed:
                GLOBAL_AUDIT_LOGGER.record("COMMAND_BLOCKED", command, "DENY", reason)
                return ExecutionResult(
                    command=command,
                    exit_code=-1,
                    stdout="",
                    stderr=f"Command blocked by safety policy: {reason}",
                    duration_ms=0.0,
                    success=False,
                    error_type="SecurityPolicyViolation",
                    diagnostics=[f"Security policy violation: {reason}"],
                    risk_level=evaluation.risk_level.value,
                    blocked_by_policy=True
                )

        is_dry = self.policy.dry_run if dry_run is None else dry_run
        if is_dry:
            GLOBAL_AUDIT_LOGGER.record("COMMAND_DRY_RUN", command, "PREVIEW", "Dry-run mode active; execution skipped.")
            return ExecutionResult(
                command=command,
                exit_code=0,
                stdout="[Dry-Run] Command execution skipped.",
                stderr="",
                duration_ms=0.0,
                success=True,
                diagnostics=["[Dry-Run] Command execution skipped by safety policy."],
                risk_level=evaluation.risk_level.value,
                dry_run=True,
                resolved=True
            )

        start = time.monotonic()
        try:
            # Prefer direct argument list execution (shell=False) when command can be cleanly tokenized
            # and does not rely on shell metacharacters.
            use_argv = (
                self.policy.prefer_argv
                and evaluation.argv
                and not evaluation.is_chained
                and not evaluation.has_redirection
                and not evaluation.has_substitution
            )

            if use_argv:
                try:
                    proc = subprocess.run(
                        evaluation.argv, shell=False, capture_output=True,
                        text=True, errors="replace", timeout=timeout,
                        cwd=self.work_dir
                    )
                except (FileNotFoundError, OSError):
                    # Fall back to shell if direct binary execution failed but shell is permitted
                    proc = subprocess.run(
                        command, shell=True, capture_output=True,
                        text=True, errors="replace", timeout=timeout,
                        cwd=self.work_dir
                    )
            else:
                proc = subprocess.run(
                    command, shell=True, capture_output=True,
                    text=True, errors="replace", timeout=timeout,
                    cwd=self.work_dir
                )

            # Redact accidental secret disclosures in stdout / stderr
            safe_stdout = SecretRedactor.sanitize(proc.stdout)
            safe_stderr = SecretRedactor.sanitize(proc.stderr)

            if proc.returncode != 0:
                kind, path, line = self.diagnose_error(safe_stderr or safe_stdout)
                evidence = AIGroundingVerifier.audit_traceback_evidence(self.work_dir, safe_stderr or safe_stdout)
            else:
                kind, path, line = None, None, None
                evidence = None

            duration_ms = round((time.monotonic() - start) * 1000, 2)
            return ExecutionResult(
                command=command,
                exit_code=proc.returncode,
                stdout=safe_stdout,
                stderr=safe_stderr,
                duration_ms=duration_ms,
                success=(proc.returncode == 0),
                error_type=kind,
                error_line=line,
                error_file=path,
                resolved=(proc.returncode == 0),
                risk_level=evaluation.risk_level.value,
                verified_evidence=evidence
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            duration_ms = round((time.monotonic() - start) * 1000, 2)
            err_msg = SecretRedactor.sanitize(str(exc))
            GLOBAL_AUDIT_LOGGER.record("COMMAND_ERROR", command, "ERROR", err_msg)
            return ExecutionResult(
                command=command,
                exit_code=-1,
                stdout="",
                stderr=err_msg,
                duration_ms=duration_ms,
                success=False,
                error_type=type(exc).__name__,
                diagnostics=[f"Execution process error: {err_msg}"],
                risk_level=evaluation.risk_level.value
            )

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
        """Validate target path within workspace boundary and without symlink escapes."""
        valid, reason, resolved = PathGuard.validate_target_path(file_path, self.work_dir, for_write=True)
        if not valid or not resolved or resolved.suffix != ".py":
            GLOBAL_AUDIT_LOGGER.record("PATH_BLOCKED", str(file_path), "DENY", reason)
            return None
        return resolved

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

        # Verify ground truth of line using AIGroundingVerifier
        is_grounded, _ = AIGroundingVerifier.verify_line(self.work_dir, str(path), error_line)
        if not is_grounded:
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
        sha256 = hashlib.sha256(original).hexdigest()
        return RepairProposal(path, original, replacement, f"Add missing colon at line {error_line}", diff, sha256)

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
            GLOBAL_AUDIT_LOGGER.record("FILE_REPLACED", str(path), "SUCCESS", "Atomic file replacement completed.")
            return True
        finally:
            if temp_name is not None:
                try:
                    os.unlink(temp_name)
                except FileNotFoundError:
                    pass

    def execute_and_heal(self, command: str, max_retries: int = 3, dry_run: Optional[bool] = None) -> ExecutionResult:
        """Execute command and apply verified, syntax-checked repairs with rollback on failure."""
        is_dry = self.policy.dry_run if dry_run is None else dry_run
        if is_dry:
            result = self.run_command(command, dry_run=True)
            return result

        result = self.run_command(command)
        if result.success or max_retries <= 0 or result.blocked_by_policy:
            return result

        if not result.error_file:
            return result

        proposal = self.propose_repair(result.error_file, result.error_type or "", result.error_line,
                                       result.stderr or result.stdout)
        if proposal is None:
            result.diagnostics.append("No supported safe repair proposal found.")
            return result

        # Anti-cycling guard: avoid reapplying identical failed patches
        patch_hash = hashlib.sha256(proposal.diff.encode()).hexdigest()
        if patch_hash in self._attempted_patch_hashes:
            result.diagnostics.append(f"Anti-cycling guard: Identical patch ({patch_hash[:8]}) previously failed; skipping re-application.")
            return result
        self._attempted_patch_hashes.add(patch_hash)

        try:
            if not self._replace_if_unchanged(proposal.path, proposal.original, proposal.replacement):
                result.diagnostics.append("File changed before repair; no patch applied.")
                return result

            # Register in multi-file rollback stack
            self.rollback_stack.push(proposal.path, proposal.original, proposal.replacement, proposal.diff)

            verified = self.run_command(command)
            # Strict evidence of success
            if (
                verified.success
                and self._target(str(proposal.path)) == proposal.path
                and proposal.path.read_bytes() == proposal.replacement
            ):
                # Ensure post-repair file AST parses without error
                try:
                    ast.parse(proposal.replacement.decode("utf-8", errors="replace"), filename=str(proposal.path))
                    verified.applied_patches.append(proposal.description + "\n" + proposal.diff)
                    self.rollback_stack.clear()
                    GLOBAL_AUDIT_LOGGER.record("REPAIR_VERIFIED", str(proposal.path), "SUCCESS", proposal.description)
                    return verified
                except SyntaxError as parse_err:
                    verified.success = False
                    verified.resolved = False
                    verified.diagnostics.append(f"Post-verification AST parse failed: {parse_err}")

            # Verification failed: restore original bytes
            if self._replace_if_unchanged(proposal.path, proposal.replacement, proposal.original):
                verified.diagnostics.append("Verification failed; original file restored.")
                self.rollback_stack.clear()
            else:
                verified.success = False
                verified.resolved = False
                verified.diagnostics.append("File changed during verification; repair is unverified and automatic rollback was skipped.")

            GLOBAL_AUDIT_LOGGER.record("REPAIR_ROLLED_BACK", str(proposal.path), "FAILURE", "Verification failed; rolled back.")
            return verified
        except OSError as exc:
            result.diagnostics.append(f"Repair failed: {exc}")
            try:
                if self._replace_if_unchanged(proposal.path, proposal.replacement, proposal.original):
                    result.diagnostics.append("Original file restored after repair error.")
                    self.rollback_stack.clear()
            except OSError as rollback_error:
                result.diagnostics.append(f"Rollback failed: {rollback_error}")
            return result
