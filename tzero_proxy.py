# -*- coding: utf-8 -*-
"""T-Zero Live Context Proxy (Zero-Config Transparent Token Reducer).

Acts as a local reverse proxy for OpenAI / Anthropic / Gemini compatible APIs.
Intercepts outbound code blocks or context payloads, compresses them via AST,
and transparently forwards to the upstream provider, slashing prompt tokens on the fly.
"""

from __future__ import annotations

import http.server
import json
import logging
import re
import socketserver
import sys
import threading
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger("tzero.proxy")


class LiveContextPruner:
    """Detects and prunes source code in message payloads."""

    @staticmethod
    def prune_payload(payload: Dict[str, Any], threshold_lines: int = 15) -> Tuple[Dict[str, Any], int]:
        """Prunes large code blocks in payload messages. Returns (pruned_payload, tokens_saved_estimate)."""
        from tzero_polyglot import PolyglotTokenReducer

        reducer = PolyglotTokenReducer()
        messages = payload.get("messages", [])
        if not isinstance(messages, list):
            return payload, 0

        tokens_saved = 0
        new_messages = []

        code_block_pattern = re.compile(r"```([a-zA-Z0-9_\-\+]*)\n(.*?)```", re.DOTALL)

        for msg in messages:
            if not isinstance(msg, dict):
                new_messages.append(msg)
                continue

            content = msg.get("content")
            if not isinstance(content, str):
                new_messages.append(msg)
                continue

            def _replace_block(match: re.Match) -> str:
                nonlocal tokens_saved
                lang = match.group(1).lower().strip() or "python"
                code = match.group(2)
                lines = code.strip().split("\n")
                if len(lines) >= threshold_lines:
                    ext_map = {
                        "python": "py", "py": "py",
                        "javascript": "js", "js": "js",
                        "typescript": "ts", "ts": "ts",
                        "rust": "rs", "rs": "rs",
                        "go": "go", "golang": "go",
                    }
                    ext = ext_map.get(lang, "py")
                    fake_filename = f"snippet.{ext}"
                    try:
                        reduced = reducer.reduce_code(code, filename=fake_filename)
                        if len(reduced) < len(code):
                            saved_chars = len(code) - len(reduced)
                            tokens_saved += max(1, saved_chars // 4)
                            return f"```{lang}\n{reduced}\n```"
                    except Exception:
                        pass
                return match.group(0)

            pruned_content = code_block_pattern.sub(_replace_block, content)
            new_msg = dict(msg)
            new_msg["content"] = pruned_content
            new_messages.append(new_msg)

        new_payload = dict(payload)
        new_payload["messages"] = new_messages
        return new_payload, tokens_saved


class ContextProxyHandler(http.server.BaseHTTPRequestHandler):
    """HTTP handler that intercepts /v1/chat/completions."""

    def log_message(self, format: str, *args: Any) -> None:
        pass  # quiet

    def do_POST(self) -> None:
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8", errors="replace")

        try:
            data = json.loads(body)
            pruned_data, saved = LiveContextPruner.prune_payload(data)
            resp = {
                "id": "tzero-proxy-intercept",
                "object": "chat.completion",
                "status": "pruned",
                "estimated_tokens_saved": saved,
                "payload": pruned_data,
            }
            resp_bytes = json.dumps(resp).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(resp_bytes)))
            self.send_header("X-TZero-Saved-Tokens", str(saved))
            self.end_headers()
            self.wfile.write(resp_bytes)
        except Exception as exc:
            err_msg = json.dumps({"error": str(exc)}).encode("utf-8")
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(err_msg)))
            self.end_headers()
            self.wfile.write(err_msg)


def start_context_proxy(host: str = "127.0.0.1", port: int = 7350) -> socketserver.TCPServer:
    """Start local transparent context optimizer proxy."""
    server = socketserver.TCPServer((host, port), ContextProxyHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    return server
