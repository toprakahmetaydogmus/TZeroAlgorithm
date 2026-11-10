# -*- coding: utf-8 -*-
"""T-Zero 2026 Lifecycle Hook Runner (PreToolUse / PostToolUse).

Supports Claude Code, Gemini CLI, and Cursor native hook JSON protocols:
  - PreToolUse: Blocks writes/edits/commands containing leaked credentials (exit code 2).
  - PostToolUse: Auto-prunes oversized file reads into compact AST skeletons cleanly.

100% Free, Local, Offline, Zero-Leak Certified.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List, Optional

from tzero_polyglot import PolyglotTokenReducer, count_bpe_tokens
from tzero_security import ZeroLeakEngine


WRITE_TOOL_NAMES = {
    "write", "edit", "multiedit", "write_file", "edit_file",
    "replace_file_content", "multi_replace_file_content",
}
SHELL_TOOL_NAMES = {"bash", "run_command", "terminal", "shell"}
READ_TOOL_NAMES = {"read", "read_file", "view_file", "view_file_outline"}


def _extract_write_blobs(tool_input: Dict[str, Any]) -> List[str]:
    blobs: List[str] = []
    for key in ("content", "Content", "new_string", "Replacement", "CodeContent"):
        val = tool_input.get(key)
        if isinstance(val, str) and val:
            blobs.append(val)
    for list_key in ("edits", "ReplacementChunks"):
        items = tool_input.get(list_key)
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    for k in ("new_string", "ReplacementContent", "content"):
                        v = item.get(k)
                        if isinstance(v, str) and v:
                            blobs.append(v)
    return blobs


def evaluate_pre_tool_use(
    payload: Dict[str, Any],
    workspace_dir: str = ".",
) -> Dict[str, Any]:
    """Evaluates PreToolUse payload for Zero-Leak credential violations."""
    del workspace_dir
    tool_name = str(payload.get("tool_name") or payload.get("tool") or "").strip().lower()
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if not isinstance(tool_input, dict):
        tool_input = {}

    file_path = str(
        tool_input.get("file_path")
        or tool_input.get("path")
        or tool_input.get("TargetFile")
        or "snippet.txt"
    )

    if tool_name in WRITE_TOOL_NAMES:
        blobs = _extract_write_blobs(tool_input)
        all_findings: List[Any] = []
        for blob in blobs:
            all_findings.extend(ZeroLeakEngine.scan_text(blob))
        if all_findings:
            patterns = sorted({
                getattr(f, "description", None) or getattr(f, "rule_id", "Secret")
                for f in all_findings
            })
            return {
                "decision": "block",
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                },
                "reason": (
                    f"Blocked by T-Zero Zero-Leak Hook: {len(all_findings)} secret finding(s) "
                    f"in {os.path.basename(file_path)} ({', '.join(patterns[:3])})."
                ),
                "findings": len(all_findings),
                "exit_code": 2,
            }

    elif tool_name in SHELL_TOOL_NAMES:
        cmd = str(tool_input.get("command") or tool_input.get("CommandLine") or "")
        if cmd:
            findings = ZeroLeakEngine.scan_text(cmd)
            if findings:
                return {
                    "decision": "block",
                    "reason": f"Blocked by T-Zero Zero-Leak Hook: hardcoded secret in shell command ({len(findings)} finding(s)).",
                    "findings": len(findings),
                    "exit_code": 2,
                }

    return {"decision": "allow", "reason": "Clean PreToolUse check", "findings": 0, "exit_code": 0}


def evaluate_post_tool_use(
    payload: Dict[str, Any],
    workspace_dir: str = ".",
    max_chars: int = 16000,
) -> Dict[str, Any]:
    """Auto-prunes oversized PostToolUse file read responses using T-Zero AST reduction."""
    del workspace_dir
    tool_name = str(payload.get("tool_name") or payload.get("tool") or "").strip().lower()
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if not isinstance(tool_input, dict):
        tool_input = {}

    raw_resp = payload.get("tool_response") or payload.get("output") or ""
    if isinstance(raw_resp, dict):
        raw_text = str(raw_resp.get("content") or raw_resp.get("text") or "")
    else:
        raw_text = str(raw_resp or "")

    file_path = str(
        tool_input.get("file_path")
        or tool_input.get("path")
        or tool_input.get("AbsolutePath")
        or "module.py"
    )

    if tool_name in READ_TOOL_NAMES and len(raw_text) > max_chars:
        reduced = PolyglotTokenReducer.reduce_code(raw_text, filename=file_path, mode="ultra")
        leaks = ZeroLeakEngine.scan_text(reduced)
        if leaks:
            reduced = ZeroLeakEngine.sanitize_text(reduced)
        raw_tok = count_bpe_tokens(raw_text)
        pruned_tok = count_bpe_tokens(reduced)
        sav_pct = round(max(0.0, (1.0 - pruned_tok / max(1, raw_tok)) * 100.0), 1)
        note = f" [Redacted {len(leaks)} secret(s)]" if leaks else ""
        return {
            "decision": "prune",
            "additionalContext": (
                f"// [T-Zero Auto-Pruned Hook Output{note}: {os.path.basename(file_path)} | "
                f"~{pruned_tok:,} vs {raw_tok:,} tokens (-{sav_pct}%)]\n{reduced}"
            ),
            "raw_tokens": raw_tok,
            "pruned_tokens": pruned_tok,
            "savings_pct": sav_pct,
            "exit_code": 0,
        }

    return {"decision": "allow", "reason": "No post-hook pruning needed", "exit_code": 0}


def run_hook_cli(
    event: str = "PreToolUse",
    payload_json: Optional[str] = None,
    workspace_dir: str = ".",
    max_chars: int = 16000,
) -> int:
    """CLI entrypoint parsing hook JSON payload and emitting decision JSON."""
    raw_in = payload_json
    if raw_in is None:
        raw_in = sys.stdin.read() if not sys.stdin.isatty() else "{}"
    try:
        payload = json.loads(raw_in or "{}")
        if not isinstance(payload, dict):
            payload = {}
    except Exception:
        payload = {}

    ev = (event or str(payload.get("hook_event_name") or "PreToolUse")).strip().lower()
    if ev in ("post", "posttooluse", "post_tool_use"):
        verdict = evaluate_post_tool_use(payload, workspace_dir=workspace_dir, max_chars=max_chars)
    else:
        verdict = evaluate_pre_tool_use(payload, workspace_dir=workspace_dir)

    print(json.dumps(verdict, indent=2))
    return int(verdict.get("exit_code", 0))


def build_claude_cursor_hook_config() -> Dict[str, Any]:
    """Generates declarative PreToolUse/PostToolUse configuration snippet for AI coding tools."""
    return {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "Write|Edit|MultiEdit|Bash",
                    "hooks": [{"type": "command", "command": "tzero hook --event PreToolUse"}],
                }
            ],
            "PostToolUse": [
                {
                    "matcher": "Read",
                    "hooks": [{"type": "command", "command": "tzero hook --event PostToolUse"}],
                }
            ],
        }
    }
