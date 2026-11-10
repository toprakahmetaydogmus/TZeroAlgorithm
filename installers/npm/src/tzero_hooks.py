# -*- coding: utf-8 -*-
"""T-Zero 2026 Lifecycle Hook Runner (PreToolUse / PostToolUse).

Supports Claude Code, Gemini CLI, and Cursor native hook JSON protocols:
  - PreToolUse: Blocks writes/edits/commands containing leaked credentials or layer violations (exit code 2).
  - PostToolUse: Auto-prunes oversized file reads into compact AST skeletons cleanly.

100% Free, Local, Offline, Zero-Leak Certified.
"""

from __future__ import annotations

import ast
import fnmatch
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional, Set

from tzero_polyglot import PolyglotTokenReducer, count_bpe_tokens
from tzero_security import ZeroLeakEngine


WRITE_TOOL_NAMES = {
    "write", "edit", "multiedit", "write_file", "edit_file",
    "replace_file_content", "multi_replace_file_content",
}
SHELL_TOOL_NAMES = {"bash", "run_command", "terminal", "shell"}
READ_TOOL_NAMES = {"read", "read_file", "view_file", "view_file_outline"}

SAFE_SECRET_TEMPLATES = {
    ".env.example",
    ".env.template",
    ".env.sample",
    ".env.schema",
}

EXACT_SENSITIVE_FILES = {
    ".env",
    ".env.local",
    ".env.production",
    ".env.staging",
    ".env.development",
    "id_rsa",
    "id_ed25519",
    ".npmrc",
    ".pypirc",
    "credentials.json",
    "secrets.json",
}

SENSITIVE_EXTENSIONS = {".pem", ".key", ".p12"}

HOOK_TARGET_FILES = {
    "claude": os.path.join(".claude", "settings.local.json"),
    "cursor": os.path.join(".cursor", "hooks.json"),
    "gemini": os.path.join(".gemini", "settings.json"),
}


def _extract_write_blobs(tool_input: Dict[str, Any]) -> List[str]:
    blobs: List[str] = []
    for key in ("content", "Content", "text", "Text", "new_string", "Replacement", "CodeContent"):
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


def _is_sensitive_file_read(file_path: str) -> bool:
    if not file_path:
        return False
    base_name = os.path.basename(file_path.replace("\\", "/")).lower()
    if not base_name:
        return False
    if base_name in SAFE_SECRET_TEMPLATES or any(base_name.endswith(tmpl) for tmpl in SAFE_SECRET_TEMPLATES):
        return False
    if base_name in EXACT_SENSITIVE_FILES:
        return True
    if any(base_name.endswith(ext) for ext in SENSITIVE_EXTENSIONS):
        return True
    return False


def _is_shell_exfiltration(cmd: str) -> bool:
    if not cmd:
        return False
    cmd_lower = cmd.lower()
    if re.search(
        r"\b(env|printenv|set)\b[^\n|;&]*\|[^\n|;&]*\b(curl|wget|invoke-webrequest|iwr|nc|ncat|ssh|scp)(\.exe)?\b",
        cmd_lower,
    ):
        return True

    has_net_tool = bool(re.search(
        r"\b(curl|wget|invoke-webrequest|iwr|nc|ncat|ssh|scp)(\.exe)?\b",
        cmd_lower,
    ))
    if not has_net_tool:
        return False

    has_secret_var = bool(re.search(
        r"(\$|%)(api_key|secret|token|aws_secret|password)",
        cmd_lower,
    ))
    if has_secret_var:
        return True

    if re.search(r"(?<![\w\.-])\.env(?!\.(example|template|sample|schema))\b", cmd_lower):
        return True
    if re.search(r"\b(id_rsa|id_ed25519)\b", cmd_lower):
        return True
    if re.search(r"(?<![\w\.-])(\.npmrc|\.pypirc)\b", cmd_lower):
        return True

    return False


def _matches_layer_pattern(file_rel: str, patterns: List[str]) -> bool:
    file_rel_norm = file_rel.replace("\\", "/")
    base_name = os.path.basename(file_rel_norm)
    for p in patterns:
        p_norm = p.replace("\\", "/")
        p_clean = p_norm.rstrip("/*")
        if p_norm.endswith("/*") or p_norm.endswith("/**"):
            if file_rel_norm.startswith(p_clean + "/") or file_rel_norm == p_clean:
                return True
        elif file_rel_norm == p_clean or base_name == p_clean:
            return True
        elif fnmatch.fnmatch(file_rel_norm, p_norm) or fnmatch.fnmatch(base_name, p_norm):
            return True
    return False


def _find_file_layer(file_path: str, layers: Dict[str, List[str]], workspace_dir: str) -> Optional[str]:
    ws_abs = os.path.abspath(workspace_dir)
    if os.path.isabs(file_path):
        try:
            rel_p = os.path.relpath(file_path, ws_abs).replace("\\", "/")
        except ValueError:
            rel_p = file_path.replace("\\", "/")
    else:
        full_p = os.path.abspath(os.path.join(ws_abs, file_path))
        try:
            rel_p = os.path.relpath(full_p, ws_abs).replace("\\", "/")
        except ValueError:
            rel_p = file_path.replace("\\", "/")

    file_norm = file_path.replace("\\", "/")

    for layer_name, patterns in layers.items():
        if _matches_layer_pattern(rel_p, patterns) or _matches_layer_pattern(file_norm, patterns):
            return layer_name
    return None


def _extract_imported_modules(blob: str, filename: str) -> Set[str]:
    extracted: Set[str] = set()
    if filename.endswith(".py") or not ("." in os.path.basename(filename)):
        try:
            tree = ast.parse(blob, filename=filename)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for n in node.names:
                        extracted.add(n.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        extracted.add(node.module)
            return extracted
        except Exception:
            pass

    for match in re.finditer(r"^\s*from\s+([a-zA-Z0-9_\.]+)\s+import", blob, re.MULTILINE):
        extracted.add(match.group(1))
    for match in re.finditer(r"^\s*import\s+([a-zA-Z0-9_.,\s]+)", blob, re.MULTILINE):
        for part in match.group(1).split(","):
            mod_candidate = part.strip().split()[0] if part.strip() else ""
            if mod_candidate:
                extracted.add(mod_candidate)
    return extracted


def _resolve_module_layer(mod: str, layers: Dict[str, List[str]]) -> Optional[str]:
    if mod in layers:
        return mod
    root_mod = mod.split(".")[0]
    if root_mod in layers:
        return root_mod

    candidates = [mod, f"{mod}.py", root_mod, f"{root_mod}.py", mod.replace(".", "/")]
    for layer_name, patterns in layers.items():
        for cand in candidates:
            if _matches_layer_pattern(cand, patterns):
                return layer_name
    return None


def _check_architecture_rules(
    file_path: str,
    blobs: List[str],
    workspace_dir: str,
) -> Optional[Dict[str, Any]]:
    rules_path = os.path.join(os.path.abspath(workspace_dir), "tzero.rules.json")
    if not os.path.isfile(rules_path):
        return None

    try:
        with open(rules_path, "r", encoding="utf-8") as f:
            rules_data = json.load(f)
    except Exception:
        return None

    if not isinstance(rules_data, dict):
        return None

    layers: Dict[str, List[str]] = rules_data.get("layers", {})
    forbidden_imports: List[Dict[str, Any]] = rules_data.get("forbidden_imports", [])
    if not layers or not forbidden_imports:
        return None

    src_layer = _find_file_layer(file_path, layers, workspace_dir)
    if src_layer is None:
        return None

    applicable_rules = [r for r in forbidden_imports if r.get("from_layer") == src_layer]
    if not applicable_rules:
        return None

    extracted_modules: Set[str] = set()
    for blob in blobs:
        extracted_modules.update(_extract_imported_modules(blob, file_path))

    if not extracted_modules:
        return None

    for mod in extracted_modules:
        target_layer = _resolve_module_layer(mod, layers)
        root_mod = mod.split(".")[0]

        for rule in applicable_rules:
            cannot_import = rule.get("cannot_import", [])
            rule_reason = rule.get("reason", "Decoupling architectural policy violated")

            is_forbidden = False
            violating_target = target_layer

            if target_layer and target_layer in cannot_import:
                is_forbidden = True
            else:
                for forbidden_target in cannot_import:
                    clean_target = forbidden_target.replace("/", ".").rstrip("/*")
                    if (
                        mod == clean_target
                        or root_mod == clean_target
                        or mod.startswith(clean_target + ".")
                        or clean_target in mod.split(".")
                        or fnmatch.fnmatch(mod, forbidden_target)
                    ):
                        is_forbidden = True
                        violating_target = forbidden_target
                        break

            if is_forbidden:
                return {
                    "decision": "block",
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "deny",
                    },
                    "reason": (
                        f"Blocked by T-Zero Architecture Layer Guard: layer '{src_layer}' is forbidden from importing "
                        f"'{mod}' (target layer: '{violating_target}'). Rule: {rule_reason}"
                    ),
                    "findings": 1,
                    "exit_code": 2,
                }

    return None


def evaluate_pre_tool_use(
    payload: Dict[str, Any],
    workspace_dir: str = ".",
) -> Dict[str, Any]:
    """Evaluates PreToolUse payload for Zero-Leak credential and architecture violations."""
    tool_name = str(payload.get("tool_name") or payload.get("tool") or "").strip().lower()
    tool_input = payload.get("tool_input") or payload.get("input") or {}
    if not isinstance(tool_input, dict):
        tool_input = {}

    file_path = str(
        tool_input.get("file_path")
        or tool_input.get("filepath")
        or tool_input.get("path")
        or tool_input.get("Path")
        or tool_input.get("AbsolutePath")
        or tool_input.get("TargetFile")
        or "snippet.txt"
    )

    if tool_name in READ_TOOL_NAMES:
        if _is_sensitive_file_read(file_path):
            base_name = os.path.basename(file_path.replace("\\", "/"))
            return {
                "decision": "block",
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                },
                "reason": (
                    f"Blocked by T-Zero Zero-Leak Hook: sensitive secret file read denied "
                    f"for {base_name}."
                ),
                "findings": 1,
                "exit_code": 2,
            }

    elif tool_name in SHELL_TOOL_NAMES:
        cmd = str(tool_input.get("command") or tool_input.get("CommandLine") or "")
        if cmd:
            findings = ZeroLeakEngine.scan_text(cmd)
            if findings:
                return {
                    "decision": "block",
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "deny",
                    },
                    "reason": f"Blocked by T-Zero Zero-Leak Hook: hardcoded secret in shell command ({len(findings)} finding(s)).",
                    "findings": len(findings),
                    "exit_code": 2,
                }
            if _is_shell_exfiltration(cmd):
                return {
                    "decision": "block",
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "deny",
                    },
                    "reason": (
                        "Blocked by T-Zero Zero-Leak Hook: potential secret exfiltration via shell network tool."
                    ),
                    "findings": 1,
                    "exit_code": 2,
                }

    elif tool_name in WRITE_TOOL_NAMES:
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

        arch_block = _check_architecture_rules(file_path, blobs, workspace_dir)
        if arch_block is not None:
            return arch_block

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
    elif isinstance(raw_resp, list):
        raw_text = "".join(
            str(item.get("text") or item.get("content") or "") if isinstance(item, dict) else str(item)
            for item in raw_resp
        )
    else:
        raw_text = str(raw_resp or "")

    file_path = str(
        tool_input.get("file_path")
        or tool_input.get("filepath")
        or tool_input.get("path")
        or tool_input.get("Path")
        or tool_input.get("AbsolutePath")
        or tool_input.get("TargetFile")
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


def build_claude_cursor_hook_config() -> Dict[str, Any]:
    """Generates declarative PreToolUse/PostToolUse configuration snippet for AI coding tools."""
    return {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "Write|Edit|MultiEdit|Bash|Read",
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


def install_hooks(workspace_dir: str = ".", client: str = "all") -> Dict[str, Any]:
    """Installs PreToolUse/PostToolUse hooks idempotently into Claude, Cursor, or Gemini settings."""
    client_norm = str(client or "").strip().lower()
    if client_norm == "all":
        targets = list(HOOK_TARGET_FILES.values())
    elif client_norm in HOOK_TARGET_FILES:
        targets = [HOOK_TARGET_FILES[client_norm]]
    else:
        raise ValueError(
            f"Unknown client '{client}'. Expected one of: all, claude, cursor, gemini."
        )

    installed: List[str] = []
    tzero_cfg = build_claude_cursor_hook_config().get("hooks", {})

    for rel_target in targets:
        target_path = os.path.join(workspace_dir, rel_target)
        target_dir = os.path.dirname(target_path)
        if target_dir:
            os.makedirs(target_dir, exist_ok=True)

        data: Dict[str, Any] = {}
        if os.path.isfile(target_path):
            try:
                with open(target_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        data = loaded
            except Exception:
                data = {}

        if "hooks" not in data or not isinstance(data["hooks"], dict):
            data["hooks"] = {}

        for event_name, tz_entries in tzero_cfg.items():
            existing_event_hooks = data["hooks"].get(event_name)
            if not isinstance(existing_event_hooks, list):
                existing_event_hooks = []
                data["hooks"][event_name] = existing_event_hooks

            for tz_entry in tz_entries:
                already_present = any(
                    isinstance(ex, dict)
                    and any(
                        isinstance(h, dict) and "tzero hook" in str(h.get("command", ""))
                        for h in ex.get("hooks", [])
                    )
                    for ex in existing_event_hooks
                )
                if not already_present:
                    existing_event_hooks.append(tz_entry)

        tmp_path = target_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp_path, target_path)
        installed.append(os.path.normpath(target_path).replace("\\", "/"))

    return {
        "installed": installed,
        "client": client,
        "count": len(installed),
    }


def run_hook_cli(
    event: str = "PreToolUse",
    payload_json: Optional[str] = None,
    workspace_dir: str = ".",
    max_chars: int = 16000,
    install_client: Optional[str] = None,
) -> int:
    """CLI entrypoint parsing hook JSON payload and emitting decision JSON."""
    if install_client is not None:
        result = install_hooks(workspace_dir=workspace_dir, client=install_client)
        print(json.dumps(result, indent=2))
        return 0

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


if __name__ == "__main__":
    sys.exit(run_hook_cli())
