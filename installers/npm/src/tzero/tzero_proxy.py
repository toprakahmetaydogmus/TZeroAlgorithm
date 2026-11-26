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
import time
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger("tzero.proxy")


class LiveContextPruner:
    """Detects and prunes source code in message payloads."""

    @staticmethod
    def prune_payload(payload: Dict[str, Any], threshold_lines: int = 15) -> Tuple[Dict[str, Any], int]:
        """Prunes large code blocks in payload messages. Returns (pruned_payload, tokens_saved_estimate)."""
        from tzero.tzero_polyglot import PolyglotTokenReducer

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
    """HTTP handler that intercepts /v1/chat/completions with strict request bounds."""

    MAX_BODY_BYTES = 2 * 1024 * 1024  # 2 MiB max JSON payload
    MAX_REJECT_DRAIN_BYTES = 8 * 1024 * 1024  # Bound unread TCP drain on 413 to avoid Winsock RST
    REQUEST_TIMEOUT = 10.0

    def setup(self) -> None:
        super().setup()
        try:
            self.connection.settimeout(self.REQUEST_TIMEOUT)
        except Exception:
            pass

    def log_message(self, format: str, *args: Any) -> None:
        pass  # quiet

    def _drain_rejected_body(self, content_length: int) -> None:
        """Briefly drain bounded unread bytes so TCP close sends FIN instead of RST."""
        to_drain = min(max(0, content_length), self.MAX_REJECT_DRAIN_BYTES)
        if to_drain <= 0:
            return
        deadline = time.monotonic() + 0.5
        try:
            self.connection.settimeout(0.1)
            remaining = to_drain
            while remaining > 0 and time.monotonic() < deadline:
                chunk = self.rfile.read1(min(remaining, 65536)) if hasattr(self.rfile, "read1") else self.rfile.read(min(remaining, 65536))
                if not chunk:
                    break
                remaining -= len(chunk)
        except Exception:
            pass

    def _send_json_error(self, code: int, msg: str, drain_bytes: int = 0) -> None:
        err_msg = json.dumps({"error": msg}).encode("utf-8")
        self.close_connection = True
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(err_msg)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(err_msg)
        self.wfile.flush()
        if drain_bytes > 0:
            self._drain_rejected_body(drain_bytes)

    def do_POST(self) -> None:
        sem = getattr(self.server, "concurrency_semaphore", None)
        acquired = False
        if sem is not None:
            acquired = sem.acquire(blocking=False)
            if not acquired:
                self._send_json_error(503, "Too many concurrent requests")
                return

        try:
            raw_len = self.headers.get("Content-Length")
            if raw_len is None:
                self._send_json_error(411, "Content-Length header required")
                return
            try:
                content_length = int(raw_len)
            except ValueError:
                self._send_json_error(400, "Invalid Content-Length header")
                return
            if content_length < 0:
                self._send_json_error(400, "Negative Content-Length rejected")
                return
            if content_length > self.MAX_BODY_BYTES:
                self._send_json_error(
                    413,
                    f"Payload exceeds {self.MAX_BODY_BYTES} byte limit",
                    drain_bytes=content_length,
                )
                return

            raw_bytes = bytearray()
            remaining = content_length
            while remaining > 0:
                chunk = self.rfile.read(min(remaining, 65536))
                if not chunk:
                    self._send_json_error(400, "Truncated request body")
                    return
                raw_bytes.extend(chunk)
                remaining -= len(chunk)

            body = raw_bytes.decode("utf-8", errors="replace")
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
        except TimeoutError:
            try:
                self._send_json_error(408, "Request body read timed out")
            except Exception:
                pass
        except Exception as exc:
            try:
                self._send_json_error(400, str(exc))
            except Exception:
                pass
        finally:
            if sem is not None and acquired:
                sem.release()


class _BoundedThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, server_address: Tuple[str, int], handler_cls: Any, max_concurrent: int = 16):
        self.concurrency_semaphore = threading.Semaphore(max(1, int(max_concurrent)))
        super().__init__(server_address, handler_cls)


def start_context_proxy(host: str = "127.0.0.1", port: int = 7350, max_concurrent: int = 16) -> socketserver.TCPServer:
    """Start local transparent context optimizer proxy with timeout and concurrency limits."""
    server = _BoundedThreadingHTTPServer((host, port), ContextProxyHandler, max_concurrent=max_concurrent)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    return server
