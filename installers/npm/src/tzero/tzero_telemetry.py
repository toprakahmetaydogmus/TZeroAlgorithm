# -*- coding: utf-8 -*-
"""Local SQLite Token Savings & ROI Telemetry Engine for T-Zero.

100% offline, zero-network telemetry store persisted under `.tzero/telemetry.db`
(or `TZERO_TELEMETRY_DB` env override) so developers can measure cumulative
raw vs. pruned tokens, reduction ratio, and USD savings across local runs.
"""

from __future__ import annotations

import os
import sqlite3
import time
from typing import Any, Dict, List, Optional


DEFAULT_PRICE_PER_M_TOKENS = 3.00  # Conservative Sonnet-tier blended input rate


def _resolve_db_path(workspace_dir: str = ".") -> str:
    env_override = os.environ.get("TZERO_TELEMETRY_DB")
    if env_override:
        db_dir = os.path.dirname(os.path.abspath(env_override))
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        return os.path.abspath(env_override)
    ws_tzero = os.path.join(os.path.abspath(workspace_dir), ".tzero")
    os.makedirs(ws_tzero, exist_ok=True)
    return os.path.join(ws_tzero, "telemetry.db")


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, timeout=5.0)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS savings_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts REAL NOT NULL,
            command TEXT NOT NULL,
            raw_tokens INTEGER NOT NULL,
            pruned_tokens INTEGER NOT NULL,
            saved_tokens INTEGER NOT NULL,
            usd_saved REAL NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def record_event(
    command: str,
    raw_tokens: int,
    pruned_tokens: int,
    workspace_dir: str = ".",
    price_per_million: float = DEFAULT_PRICE_PER_M_TOKENS,
) -> Dict[str, Any]:
    """Records a local compression/telemetry event into SQLite."""
    raw = max(0, int(raw_tokens))
    pruned = max(0, int(pruned_tokens))
    saved = max(0, raw - pruned)
    usd = (saved / 1_000_000.0) * float(price_per_million)
    db_path = _resolve_db_path(workspace_dir)
    conn = _connect(db_path)
    try:
        with conn:
            conn.execute(
                "INSERT INTO savings_events (ts, command, raw_tokens, pruned_tokens, saved_tokens, usd_saved) VALUES (?, ?, ?, ?, ?, ?)",
                (time.time(), str(command)[:64], raw, pruned, saved, round(usd, 6)),
            )
    finally:
        conn.close()
    return {
        "command": command,
        "raw_tokens": raw,
        "pruned_tokens": pruned,
        "saved_tokens": saved,
        "usd_saved": round(usd, 6),
        "db_path": db_path,
    }


def get_summary(workspace_dir: str = ".", days: int = 30) -> Dict[str, Any]:
    """Returns aggregated local telemetry stats over the trailing `days` window."""
    db_path = _resolve_db_path(workspace_dir)
    since_ts = time.time() - (max(1, int(days)) * 86400.0)
    conn = _connect(db_path)
    try:
        with conn:
            row = conn.execute(
                """
                SELECT COUNT(*), COALESCE(SUM(raw_tokens), 0), COALESCE(SUM(pruned_tokens), 0),
                       COALESCE(SUM(saved_tokens), 0), COALESCE(SUM(usd_saved), 0.0)
                FROM savings_events WHERE ts >= ?
                """,
                (since_ts,),
            ).fetchone()
            recent_rows = conn.execute(
                """
                SELECT command, COUNT(*), COALESCE(SUM(saved_tokens), 0), COALESCE(SUM(usd_saved), 0.0)
                FROM savings_events WHERE ts >= ?
                GROUP BY command ORDER BY SUM(saved_tokens) DESC LIMIT 8
                """,
                (since_ts,),
            ).fetchall()
    finally:
        conn.close()

    runs, total_raw, total_pruned, total_saved, total_usd = row
    reduction_pct = round((total_saved / total_raw) * 100.0, 2) if total_raw > 0 else 0.0
    by_command: List[Dict[str, Any]] = [
        {"command": r[0], "runs": r[1], "saved_tokens": r[2], "usd_saved": round(float(r[3]), 4)}
        for r in recent_rows
    ]
    return {
        "days": days,
        "db_path": db_path,
        "runs": int(runs),
        "raw_tokens": int(total_raw),
        "pruned_tokens": int(total_pruned),
        "saved_tokens": int(total_saved),
        "reduction_pct": reduction_pct,
        "usd_saved": round(float(total_usd), 4),
        "by_command": by_command,
    }


def render_report(workspace_dir: str = ".", days: int = 30) -> str:
    """Formats a human-readable ASCII/Markdown telemetry summary."""
    summary = get_summary(workspace_dir=workspace_dir, days=days)
    lines = [
        f"### 📊 T-Zero Offline SQLite Telemetry (Last {summary['days']} Days)",
        f"- **Store:** `{summary['db_path']}` (100% Local / Zero Network)",
        f"- **Recorded Runs:** `{summary['runs']}`",
        f"- **Raw Tokens Scanned:** `{summary['raw_tokens']:,}`",
        f"- **Pruned Tokens Emitted:** `{summary['pruned_tokens']:,}`",
        f"- **Net Tokens Saved:** `{summary['saved_tokens']:,}` (`{summary['reduction_pct']}%`)",
        f"- **Estimated Cost Avoided:** `${summary['usd_saved']:.4f}`",
    ]
    if summary["by_command"]:
        lines.append("\n#### Top Commands:")
        for item in summary["by_command"]:
            lines.append(
                f"- `{item['command']}`: {item['runs']} run(s), {item['saved_tokens']:,} tokens saved (`${item['usd_saved']:.4f}`)"
            )
    return "\n".join(lines)
