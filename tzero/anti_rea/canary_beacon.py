# -*- coding: utf-8 -*-
"""Tier 22: Stealth Canary Beacon & Real-Time Threat Telemetry.

Silently alerts developers via Webhook, Telegram Bot API, or DNS canary
lookup when an adversary attempts reverse engineering or attaches a debugger
(x64dbg, IDA Pro, Frida, or Honeypot trigger).

Features:
- Completely asynchronous (runs in daemon thread, 0ms main thread latency)
- Zero plaintext strings: Webhook URLs/Tokens encrypted with rolling keys
- Fails completely silently: zero exceptions or console outputs if offline
- Evasive network fingerprint mimicking OS background requests

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
Part of Siber Akademi T-Zero Security Suite.
License: MIT
"""

import os
import sys
import time
import json
import socket
import threading
import urllib.request
import urllib.parse
from typing import Dict, Any, Optional, List


class CanaryBeacon:
    """Dispatches stealth threat telemetry alerts to developer endpoints."""

    @classmethod
    def encrypt_endpoint(cls, endpoint_str: str, key: int = 0x7E) -> bytes:
        """Encrypts an endpoint URL or token with rolling XOR to evade string dumping."""
        return bytes([b ^ ((key + i * 13) & 0xFF) for i, b in enumerate(endpoint_str.encode("utf-8"))])

    @classmethod
    def decrypt_endpoint(cls, enc_bytes: bytes, key: int = 0x7E) -> str:
        """Decrypts endpoint bytes in memory only during active dispatch."""
        dec = bytes([b ^ ((key + i * 13) & 0xFF) for i, b in enumerate(enc_bytes)])
        return dec.decode("utf-8", errors="replace")

    @classmethod
    def _collect_host_context(cls) -> Dict[str, Any]:
        """Collects execution context for threat analysis without private data leaks."""
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
            "hostname": hostname[:16],  # Truncate for privacy
        }

    @classmethod
    def _dispatch_http(cls, url: str, payload: dict, is_telegram: bool = False, chat_id: Optional[str] = None) -> bool:
        """Dispatches an HTTPS alert packet silently."""
        try:
            if is_telegram and chat_id:
                # Format message for Telegram Markdown
                text = (
                    f"🚨 *ANTI-REA THREAT ALERT*\n"
                    f"• *Threat:* `{payload.get('threat_type', 'UNKNOWN')}`\n"
                    f"• *Detected Tool:* `{payload.get('detected_tool', 'N/A')}`\n"
                    f"• *Host:* `{payload.get('context', {}).get('hostname', 'host')}`\n"
                    f"• *Platform:* `{payload.get('context', {}).get('platform', 'os')}`\n"
                    f"• *Time:* `{payload.get('context', {}).get('timestamp', 'now')}`\n"
                    f"• *Status:* 🛡️ Neutralized & Diverted"
                )
                data = json.dumps({"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}).encode("utf-8")
            else:
                # Generic Discord / Slack / Webhook JSON
                data = json.dumps(payload).encode("utf-8")

            req = urllib.request.Request(
                url,
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) OS-Telemetry/10.0"
                }
            )
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                return resp.status in (200, 204)
        except Exception:
            return False

    @classmethod
    def _dispatch_dns_ping(cls, threat_code: str, canary_domain: str) -> None:
        """Sends an out-of-band DNS resolution beacon to bypass HTTP firewalls."""
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
        telegram_token: Optional[str] = None,
        telegram_chat_id: Optional[str] = None,
        canary_domain: Optional[str] = None,
    ) -> threading.Thread:
        """Dispatches telemetry asynchronously on a background daemon thread."""
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
            if telegram_token and telegram_chat_id:
                tg_url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
                cls._dispatch_http(tg_url, payload, is_telegram=True, chat_id=telegram_chat_id)
            if canary_domain:
                cls._dispatch_dns_ping(threat_type, canary_domain)

        t = threading.Thread(target=_worker, name="anti_rea_telemetry_beacon", daemon=True)
        t.start()
        return t

    @classmethod
    def get_injected_beacon_code(
        cls,
        enc_webhook_bytes: Optional[bytes] = None,
        enc_key: int = 0x7E,
        canary_domain: Optional[str] = None
    ) -> str:
        """Generates self-contained stealth telemetry boiler for protected programs."""
        enc_repr = repr(enc_webhook_bytes) if enc_webhook_bytes else "None"
        dom_repr = repr(canary_domain) if canary_domain else "None"

        return f'''
# --- SIBER AKADEMI CANARY THREAT TELEMETRY BEACON ---
def _send_stealth_threat_beacon(threat_label="DEBUGGER_DETECTED", tool_name="x64dbg"):
    """Silently dispatches alert to security endpoint without blocking or error logs."""
    import os, sys, threading, urllib.request, json
    enc_bytes = {enc_repr}
    if not enc_bytes:
        return

    def _beacon_job():
        try:
            # Decrypt endpoint dynamically in RAM
            url = bytes([b ^ (({enc_key} + i * 13) & 0xFF) for i, b in enumerate(enc_bytes)]).decode("utf-8")
            data = json.dumps({{
                "threat": threat_label,
                "tool": tool_name,
                "platform": sys.platform,
                "pid": os.getpid()
            }}).encode("utf-8")
            req = urllib.request.Request(
                url, data=data,
                headers={{"Content-Type": "application/json", "User-Agent": "OS-Telemetry/1.0"}}
            )
            urllib.request.urlopen(req, timeout=2.0)
        except Exception:
            pass

    threading.Thread(target=_beacon_job, daemon=True).start()
'''

    @classmethod
    def inject_beacon_into_source(
        cls,
        source_code: str,
        webhook_url: Optional[str] = None,
        key: int = 0x7E,
        canary_domain: Optional[str] = None
    ) -> str:
        """Injects stealth telemetry beacon into Python source code."""
        enc_bytes = cls.encrypt_endpoint(webhook_url, key=key) if webhook_url else None
        snippet = cls.get_injected_beacon_code(enc_bytes, enc_key=key, canary_domain=canary_domain)
        return f"{snippet.strip()}\n\n{source_code}"
