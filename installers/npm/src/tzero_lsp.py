# -*- coding: utf-8 -*-
"""T-Zero Stdio JSON-RPC Language Server (tzero lsp).

Provides real-time in-editor diagnostics and CodeLens via Language Server Protocol:
  - 100% Zero-Leak hardcoded credential detection (Severity: Error)
  - tzero.rules.json architectural layer boundary violations (Severity: Error)
  - Breaking AST public contract change warnings (Severity: Warning)
  - AST token compression CodeLens per class/function symbol

100% Free, Local, Offline, Stdlib JSON-RPC.
"""

from __future__ import annotations

import ast
import fnmatch
import json
import os
import re
import sys
import urllib.parse
from typing import Any, BinaryIO, Dict, List, Optional

from tzero_polyglot import count_bpe_tokens
from tzero_security import ZeroLeakEngine


def uri_to_path(uri: str) -> str:
    """Converts a file:// URI to a local filesystem path."""
    if not uri.startswith("file://"):
        return uri
    parsed = urllib.parse.urlparse(uri)
    raw_path = urllib.parse.unquote(parsed.path)
    if os.name == "nt" and raw_path.startswith("/") and len(raw_path) > 2 and raw_path[2] == ":":
        raw_path = raw_path[1:]
    return os.path.normpath(raw_path)


def encode_lsp_frame(payload: Dict[str, Any]) -> bytes:
    """Encodes a JSON-RPC message with LSP Content-Length header framing."""
    body = json.dumps(payload).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
    return header + body


def read_lsp_frame(in_stream: BinaryIO) -> Optional[Dict[str, Any]]:
    """Reads a single Content-Length framed JSON-RPC message from a binary stream."""
    content_length: Optional[int] = None
    while True:
        raw_line = in_stream.readline()
        if not raw_line:
            return None
        line = raw_line.decode("ascii", errors="ignore").strip()
        if line == "":
            break
        if ":" in line:
            k, v = line.split(":", 1)
            if k.strip().lower() == "content-length":
                try:
                    content_length = int(v.strip())
                except ValueError:
                    pass
    if content_length is None or content_length <= 0:
        return None
    body = in_stream.read(content_length)
    if not body or len(body) < content_length:
        return None
    return json.loads(body.decode("utf-8"))


class TZeroLSPServer:
    """Stateful Language Server handling LSP lifecycle, diagnostics, and CodeLens."""

    def __init__(self, workspace_dir: str = ".") -> None:
        self.workspace_dir = os.path.abspath(workspace_dir)
        self.documents: Dict[str, str] = {}
        self.baselines: Dict[str, str] = {}
        self.shutdown_requested = False
        self.running = True
        self._rules_cache: Optional[Dict[str, Any]] = None

    def _load_arch_rules(self) -> Dict[str, Any]:
        if self._rules_cache is not None:
            return self._rules_cache
        rules_p = os.path.join(self.workspace_dir, "tzero.rules.json")
        if os.path.isfile(rules_p):
            try:
                with open(rules_p, "r", encoding="utf-8", errors="replace") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self._rules_cache = data
                        return data
            except Exception:
                pass
        self._rules_cache = {}
        return self._rules_cache

    def _classify_layer(self, rel_path: str, rules: Dict[str, Any]) -> Optional[str]:
        norm = rel_path.replace("\\", "/")
        layers = rules.get("layers", {})
        if not isinstance(layers, dict):
            return None
        for layer_name, patterns in layers.items():
            if not isinstance(patterns, list):
                continue
            for pat in patterns:
                pat_norm = str(pat).replace("\\", "/")
                prefix = pat_norm.split("*")[0].rstrip("/")
                if fnmatch.fnmatch(norm, pat_norm) or (prefix and (norm.startswith(prefix + "/") or norm == prefix)):
                    return str(layer_name)
        return None

    def _extract_imports(self, text: str, file_path: str) -> List[tuple]:
        imports: List[tuple] = []
        if file_path.endswith(".py"):
            try:
                tree = ast.parse(text)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.append((getattr(node, "lineno", 1), alias.name))
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        imports.append((getattr(node, "lineno", 1), node.module))
                return imports
            except SyntaxError:
                pass
        for idx, line in enumerate(text.splitlines(), start=1):
            m = re.match(r"""^\s*(?:from|import)\s+([A-Za-z0-9_./@-]+)""", line)
            if m:
                imports.append((idx, m.group(1)))
        return imports

    def _resolve_module_rel(self, mod_name: str, rules: Dict[str, Any]) -> Optional[str]:
        """Resolves a dotted/slash module reference to a workspace relative path if determinable."""
        cand_rel = mod_name.replace(".", "/")
        for suffix in ("", ".py", ".ts", ".js"):
            p = os.path.join(self.workspace_dir, cand_rel + suffix)
            if os.path.exists(p):
                return os.path.relpath(p, self.workspace_dir).replace("\\", "/")
        top = mod_name.split(".")[0].split("/")[0]
        if top and any(top == k or any(top in str(pt) for pt in v) for k, v in (rules.get("layers") or {}).items() if isinstance(v, list)):
            return top
        return None

    def analyze_document(self, uri: str, text: str) -> List[Dict[str, Any]]:
        """Runs Zero-Leak, architecture boundary, and breaking contract checks on buffer text."""
        diags: List[Dict[str, Any]] = []
        file_path = uri_to_path(uri)
        try:
            rel_path = os.path.relpath(file_path, self.workspace_dir).replace("\\", "/")
        except ValueError:
            rel_path = os.path.basename(file_path)

        # 1. Zero-Leak hardcoded secrets
        for finding in ZeroLeakEngine.scan_text(text):
            ln = max(0, int(getattr(finding, "line_no", 1)) - 1)
            desc = getattr(finding, "description", None) or getattr(finding, "rule_id", "Secret leak")
            diags.append({
                "range": {"start": {"line": ln, "character": 0}, "end": {"line": ln, "character": 80}},
                "severity": 1,
                "code": "zero-leak",
                "source": "tzero-lsp",
                "message": f"T-Zero Zero-Leak Guard: {desc}",
            })

        # 2. Architecture boundaries (tzero.rules.json)
        rules = self._load_arch_rules()
        src_layer = self._classify_layer(rel_path, rules)
        forbidden = rules.get("forbidden_imports", [])
        if src_layer and isinstance(forbidden, list):
            for ln_no, imp_mod in self._extract_imports(text, file_path):
                tgt_rel = self._resolve_module_rel(imp_mod, rules)
                tgt_layer = self._classify_layer(tgt_rel, rules) if tgt_rel else None
                for rule in forbidden:
                    if rule.get("from_layer") == src_layer and tgt_layer in (rule.get("cannot_import") or []):
                        diags.append({
                            "range": {"start": {"line": max(0, ln_no - 1), "character": 0}, "end": {"line": max(0, ln_no - 1), "character": 80}},
                            "severity": 1,
                            "code": "arch-boundary",
                            "source": "tzero-lsp",
                            "message": f"Layer '{src_layer}' cannot import '{tgt_layer}' ({imp_mod}): {rule.get('reason', 'Boundary violation')}",
                        })

        # 3. Breaking API contract warnings against baseline
        baseline = self.baselines.get(uri)
        if baseline and file_path.endswith(".py") and baseline != text:
            try:
                from tzero_contracts import ASTContractComparator
                rep = ASTContractComparator.compare_code(baseline, text, file_path=rel_path)
                if getattr(rep, "is_breaking", False):
                    diags.append({
                        "range": {"start": {"line": 0, "character": 0}, "end": {"line": 0, "character": 1}},
                        "severity": 2,
                        "code": "ast-contract",
                        "source": "tzero-lsp",
                        "message": f"T-Zero Contract Warning: breaking public API change in {rel_path}",
                    })
            except Exception:
                pass

        return diags

    def compute_code_lenses(self, uri: str, text: str) -> List[Dict[str, Any]]:
        """Computes token-cost CodeLenses for classes and functions in the document."""
        file_path = uri_to_path(uri)
        lenses: List[Dict[str, Any]] = []
        lines = text.splitlines()

        if file_path.endswith(".py"):
            try:
                tree = ast.parse(text)
                for node in tree.body:
                    if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                        start_l = max(0, node.lineno - 1)
                        end_l = getattr(node, "end_lineno", node.lineno)
                        block = "\n".join(lines[start_l:end_l])
                        sig = lines[start_l] if start_l < len(lines) else ""
                        raw_t = count_bpe_tokens(block)
                        sig_t = count_bpe_tokens(sig)
                        sav = max(0, int(round((1.0 - sig_t / max(1, raw_t)) * 100)))
                        lenses.append({
                            "range": {"start": {"line": start_l, "character": 0}, "end": {"line": start_l, "character": len(sig)}},
                            "command": {
                                "title": f"⚡ ~{raw_t} tok → {sig_t} sig ({sav}% saved)",
                                "command": "tzero.copySymbolContract",
                                "arguments": [file_path, start_l],
                            },
                        })
                return lenses
            except SyntaxError:
                pass

        decl_re = re.compile(r'^\s*(?:export\s+)?(?:class|interface|struct|function|func|fn|def)\s+([A-Za-z_][A-Za-z0-9_]*)')
        for idx, line in enumerate(lines):
            if decl_re.match(line):
                sig_t = count_bpe_tokens(line.strip())
                lenses.append({
                    "range": {"start": {"line": idx, "character": 0}, "end": {"line": idx, "character": len(line)}},
                    "command": {
                        "title": f"⚡ ~{sig_t} tok AST sig",
                        "command": "tzero.copySymbolContract",
                        "arguments": [file_path, idx],
                    },
                })
        return lenses

    def _publish_diagnostics(self, uri: str, text: str) -> Dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "method": "textDocument/publishDiagnostics",
            "params": {"uri": uri, "diagnostics": self.analyze_document(uri, text)},
        }

    def handle_message(self, msg: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Processes one decoded JSON-RPC payload and returns outbound messages."""
        method = msg.get("method", "")
        msg_id = msg.get("id")
        params = msg.get("params") or {}

        if method == "initialize":
            root_uri = params.get("rootUri")
            if isinstance(root_uri, str) and root_uri.startswith("file://"):
                self.workspace_dir = uri_to_path(root_uri)
                self._rules_cache = None
            return [{
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "capabilities": {
                        "textDocumentSync": 1,
                        "codeLensProvider": {"resolveProvider": False},
                    },
                    "serverInfo": {"name": "tzero-lsp", "version": "10.9.0"},
                },
            }]

        if method == "textDocument/didOpen":
            td = params.get("textDocument") or {}
            uri = td.get("uri", "")
            text = td.get("text", "")
            self.documents[uri] = text
            self.baselines.setdefault(uri, text)
            return [self._publish_diagnostics(uri, text)]

        if method == "textDocument/didChange":
            td = params.get("textDocument") or {}
            uri = td.get("uri", "")
            changes = params.get("contentChanges") or []
            text = changes[-1].get("text", "") if changes else self.documents.get(uri, "")
            self.documents[uri] = text
            return [self._publish_diagnostics(uri, text)]

        if method == "textDocument/didSave":
            td = params.get("textDocument") or {}
            uri = td.get("uri", "")
            text = td.get("text")
            if text is None:
                fpath = uri_to_path(uri)
                if os.path.isfile(fpath):
                    with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                        text = f.read()
                else:
                    text = self.documents.get(uri, "")
            self.documents[uri] = text
            self._rules_cache = None
            return [self._publish_diagnostics(uri, text)]

        if method == "textDocument/codeLens":
            td = params.get("textDocument") or {}
            uri = td.get("uri", "")
            text = self.documents.get(uri, "")
            return [{"jsonrpc": "2.0", "id": msg_id, "result": self.compute_code_lenses(uri, text)}]

        if method == "shutdown":
            self.shutdown_requested = True
            return [{"jsonrpc": "2.0", "id": msg_id, "result": None}]

        if method == "exit":
            self.running = False
            return []

        if msg_id is not None:
            return [{"jsonrpc": "2.0", "id": msg_id, "result": None}]
        return []

    def serve_stdio(
        self,
        in_stream: Optional[BinaryIO] = None,
        out_stream: Optional[BinaryIO] = None,
    ) -> None:
        """Runs synchronous Content-Length JSON-RPC stdio message loop."""
        reader = in_stream or sys.stdin.buffer
        writer = out_stream or sys.stdout.buffer
        while self.running:
            msg = read_lsp_frame(reader)
            if msg is None:
                break
            outbound = self.handle_message(msg)
            for pkt in outbound:
                writer.write(encode_lsp_frame(pkt))
                writer.flush()


def main(workspace_dir: str = ".") -> int:
    srv = TZeroLSPServer(workspace_dir=workspace_dir)
    srv.serve_stdio()
    return 0 if srv.shutdown_requested else 0
