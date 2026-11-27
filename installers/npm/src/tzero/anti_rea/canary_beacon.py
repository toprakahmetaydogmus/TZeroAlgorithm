# -*- coding: utf-8 -*-
"""Tier 22: Opt-In Tamper Alert Webhook & Security Telemetry.

Dispatches opt-in security notifications to developer-configured HTTPS webhook
endpoints or an explicit canary domain when an integrity or debugger guard triggers.
Disabled by default unless explicitly configured by the application author.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
Part of Siber Akademi T-Zero Security Suite.
License: MIT
"""

import json
import os
import socket
import sys
import threading
import time
import urllib.request
from typing import Any, Dict, Optional


class CanaryBeacon:
    """Dispatches explicit opt-in tamper alert notifications to developer endpoints."""

    @classmethod
    def encrypt_endpoint(cls, endpoint_str: str, key: int = 0x7E) -> bytes:
        """Obfuscates a developer-configured webhook URL against casual plaintext string scans."""
        return bytes([b ^ ((key + i * 13) & 0xFF) for i, b in enumerate(endpoint_str.encode("utf-8"))])

    @classmethod
    def decrypt_endpoint(cls, enc_bytes: bytes, key: int = 0x7E) -> str:
        """Decodes an obfuscated webhook endpoint when dispatching an opt-in alert."""
        dec = bytes([b ^ ((key + i * 13) & 0xFF) for i, b in enumerate(enc_bytes)])
        return dec.decode("utf-8", errors="replace")

    @classmethod
    def _collect_host_context(cls) -> Dict[str, Any]:
        """Collects minimal execution metadata for developer tamper audit alerts."""
        try:
            hostname = socket.gethostname()
        except Exception:
            hostname = "unknown_host"

        return {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "platform": sys.platform,
            "os_name": os.name,
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "pid": os.getpid(),
            "hostname": hostname[:16],
        }

    @classmethod
    def _dispatch_http(cls, url: str, payload: dict) -> bool:
        """Dispatches a JSON tamper alert payload to an explicitly configured webhook URL."""
        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "SiberAkademi-TZero-SecurityAudit/1.0",
                },
            )
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                return resp.status in (200, 204)
        except Exception:
            return False

    @classmethod
    def _dispatch_dns_ping(cls, threat_code: str, canary_domain: str) -> None:
        """Resolves an explicitly configured canary hostname for developer security alerting."""
        try:
            subdomain = f"{threat_code.lower()[:8]}-{int(time.time())}.{canary_domain}"
            socket.gethostbyname(subdomain)
        except Exception:
            pass

    @classmethod
    def dispatch_alert_async(
        cls,
        threat_type: str,
        detected_tool: str = "x64dbg",
        webhook_url: Optional[str] = None,
        canary_domain: Optional[str] = None,
    ) -> threading.Thread:
        """Dispatches an opt-in tamper alert asynchronously on a background daemon thread."""
        payload = {
            "alert": "SECURITY_VIOLATION_DETECTED",
            "threat_type": threat_type,
            "detected_tool": detected_tool,
            "action_taken": "EXECUTION_TERMINATED_OR_DIVERTED",
            "context": cls._collect_host_context(),
        }

        def _worker():
            if webhook_url:
                cls._dispatch_http(webhook_url, payload)
            if canary_domain:
                cls._dispatch_dns_ping(threat_type, canary_domain)

        t = threading.Thread(target=_worker, name="anti_rea_tamper_alert", daemon=True)
        t.start()
        return t

    @classmethod
    def get_injected_beacon_code(
        cls,
        enc_webhook_bytes: Optional[bytes] = None,
        enc_key: int = 0x7E,
        canary_domain: Optional[str] = None,
    ) -> str:
        """Generates self-contained opt-in tamper alert code for protected builds."""
        enc_repr = repr(enc_webhook_bytes) if enc_webhook_bytes else "None"
        dom_repr = repr(canary_domain) if canary_domain else "None"

        return f'''
# --- SIBER AKADEMI OPT-IN TAMPER ALERT WEBHOOK ---
def _dispatch_tamper_alert(threat_label="DEBUGGER_DETECTED", tool_name="x64dbg"):
    """Dispatches opt-in tamper notification only when configured by application author."""
    import json, os, socket, sys, threading, urllib.request
    enc_bytes = {enc_repr}
    canary_dom = {dom_repr}
    if not enc_bytes and not canary_dom:
        return

    def _alert_job():
        if enc_bytes:
            try:
                url = bytes([b ^ (({enc_key} + i * 13) & 0xFF) for i, b in enumerate(enc_bytes)]).decode("utf-8")
                data = json.dumps({{
                    "threat": threat_label,
                    "tool": tool_name,
                    "platform": sys.platform,
                    "pid": os.getpid(),
                }}).encode("utf-8")
                req = urllib.request.Request(
                    url, data=data,
                    headers={{"Content-Type": "application/json", "User-Agent": "SiberAkademi-TZero-SecurityAudit/1.0"}},
                )
                urllib.request.urlopen(req, timeout=2.0)
            except Exception:
                pass
        if canary_dom:
            try:
                sub = "".join(ch if ch.isalnum() else "-" for ch in str(threat_label).lower()).strip("-") or "alert"
                socket.getaddrinfo(f"{{sub}}.{{canary_dom}}", 80)
            except Exception:
                pass

    threading.Thread(target=_alert_job, daemon=True).start()
'''

    @classmethod
    def inject_beacon_into_source(
        cls,
        source_code: str,
        webhook_url: Optional[str] = None,
        key: int = 0x7E,
        canary_domain: Optional[str] = None,
    ) -> str:
        """Injects opt-in tamper alert helper into protected Python source code."""
        enc_bytes = cls.encrypt_endpoint(webhook_url, key=key) if webhook_url else None
        snippet = cls.get_injected_beacon_code(enc_bytes, enc_key=key, canary_domain=canary_domain)
        return f"{snippet.strip()}\n\n{source_code}"
