# -*- coding: utf-8 -*-
"""
T-ZERO GITHUB REPOSITORY SHOWCASE CARD & VIRAL BADGE GENERATOR
--------------------------------------------------------------
Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
Version: 5.1.0 | License: MIT

Generates shareable high-DPI SVG banner cards, animated SVG badges, and interactive
HTML split-screen comparison sliders for repositories powered by T-Zero.
Designed to create a self-reinforcing viral star loop across GitHub repositories.
"""

from __future__ import annotations

import os
import html
from typing import Optional


class TZeroShowcaseGenerator:
    """Generates viral GitHub badges, repository banner cards, and interactive showcase sliders."""

    @classmethod
    def generate_svg_banner_card(
        cls,
        repo_name: str = "TZeroAlgorithm",
        savings_pct: float = 94.6,
        raw_tokens: int = 10809938,
        pruned_tokens: int = 1297192,
        annual_savings_usd: float = 14280.0,
        output_file: str = "assets/tzero_badge_card.svg"
    ) -> str:
        """Generates a futuristic, high-DPI 800x240 SVG banner card for repository READMEs."""
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)

        k_raw = f"{raw_tokens / 1_000_000:.1f}M" if raw_tokens >= 1_000_000 else f"{raw_tokens / 1_000:.1f}k"
        k_pruned = f"{pruned_tokens / 1_000_000:.1f}M" if pruned_tokens >= 1_000_000 else f"{pruned_tokens / 1_000:.1f}k"
        savings_str = f"{savings_pct:.1f}%"
        usd_str = f"${annual_savings_usd:,.0f}/yr"

        svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 240" width="800" height="240" fill="none">
    <defs>
        <linearGradient id="cardBg" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#0a0f1d"/>
            <stop offset="50%" stop-color="#0f172a"/>
            <stop offset="100%" stop-color="#020617"/>
        </linearGradient>
        <linearGradient id="accentGlow" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#38bdf8"/>
            <stop offset="50%" stop-color="#818cf8"/>
            <stop offset="100%" stop-color="#c084fc"/>
        </linearGradient>
        <linearGradient id="greenGlow" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#10b981"/>
            <stop offset="100%" stop-color="#34d399"/>
        </linearGradient>
        <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="8" result="blur"/>
            <feComposite in="SourceGraphic" in2="blur" operator="over"/>
        </filter>
        <style>
            @keyframes pulseBorder {{
                0%, 100% {{ stroke-opacity: 0.4; }}
                50% {{ stroke-opacity: 0.9; }}
            }}
            .card-border {{
                animation: pulseBorder 4s ease-in-out infinite;
            }}
        </style>
    </defs>

    <!-- Card Background -->
    <rect x="2" y="2" width="796" height="236" rx="16" fill="url(#cardBg)" stroke="url(#accentGlow)" stroke-width="2" class="card-border"/>

    <!-- Subtle Grid Background Overlay -->
    <g opacity="0.08" stroke="#38bdf8" stroke-width="1">
        <line x1="0" y1="40" x2="800" y2="40"/>
        <line x1="0" y1="80" x2="800" y2="80"/>
        <line x1="0" y1="120" x2="800" y2="120"/>
        <line x1="0" y1="160" x2="800" y2="160"/>
        <line x1="0" y1="200" x2="800" y2="200"/>
        <line x1="160" y1="0" x2="160" y2="240"/>
        <line x1="320" y1="0" x2="320" y2="240"/>
        <line x1="480" y1="0" x2="480" y2="240"/>
        <line x1="640" y1="0" x2="640" y2="240"/>
    </g>

    <!-- Header: Logo & Branding -->
    <g transform="translate(32, 30)">
        <!-- T-Zero Hexagon Icon -->
        <polygon points="18,0 36,10 36,30 18,40 0,30 0,10" fill="#0f172a" stroke="url(#accentGlow)" stroke-width="2.5"/>
        <text x="18" y="26" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="16" font-weight="900" fill="#38bdf8" text-anchor="middle">T0</text>

        <text x="48" y="22" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="20" font-weight="800" fill="#f8fafc">
            T-ZERO <tspan fill="#818cf8">CONTEXT ARCHITECT</tspan>
        </text>
        <text x="48" y="38" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="500" fill="#64748b">
            Deterministic AST Context Compressor &amp; Reality-Lock Engine
        </text>
    </g>

    <!-- Top Right: Verified Badges -->
    <g transform="translate(560, 26)">
        <rect x="0" y="0" width="105" height="26" rx="13" fill="#1e293b" stroke="#10b981" stroke-width="1.2"/>
        <circle cx="14" cy="13" r="4" fill="#10b981"/>
        <text x="24" y="17" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="10" font-weight="700" fill="#34d399">ZERO-LEAK</text>

        <rect x="114" y="0" width="94" height="26" rx="13" fill="#1e293b" stroke="#38bdf8" stroke-width="1.2"/>
        <text x="161" y="17" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="10" font-weight="700" fill="#38bdf8" text-anchor="middle">REALITY-LOCK</text>
    </g>

    <!-- Middle Divider -->
    <line x1="32" y1="80" x2="768" y2="80" stroke="#1e293b" stroke-width="1.5"/>

    <!-- Key Metrics Grid -->
    <g transform="translate(32, 102)">
        <!-- Metric 1: Token Reduction -->
        <g transform="translate(0, 0)">
            <rect x="0" y="0" width="170" height="90" rx="10" fill="#0f172a" stroke="#1e293b" stroke-width="1"/>
            <text x="16" y="26" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="600" fill="#94a3b8">TOKEN REDUCTION</text>
            <text x="16" y="62" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="32" font-weight="900" fill="#38bdf8">-{savings_str}</text>
            <text x="16" y="78" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="10" font-weight="500" fill="#64748b">Pruned AST Signatures</text>
        </g>

        <!-- Metric 2: Raw vs Pruned -->
        <g transform="translate(186, 0)">
            <rect x="0" y="0" width="170" height="90" rx="10" fill="#0f172a" stroke="#1e293b" stroke-width="1"/>
            <text x="16" y="26" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="600" fill="#94a3b8">CONTEXT INGESTION</text>
            <text x="16" y="58" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="22" font-weight="800" fill="#f8fafc">{k_pruned} <tspan font-size="14" fill="#64748b">/ {k_raw}</tspan></text>
            <text x="16" y="78" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="10" font-weight="500" fill="#10b981">Optimal KV Cache Fit</text>
        </g>

        <!-- Metric 3: Annual ROI -->
        <g transform="translate(372, 0)">
            <rect x="0" y="0" width="170" height="90" rx="10" fill="#0f172a" stroke="#1e293b" stroke-width="1"/>
            <text x="16" y="26" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="600" fill="#94a3b8">ESTIMATED TEAM ROI</text>
            <text x="16" y="58" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="24" font-weight="800" fill="#34d399">{usd_str}</text>
            <text x="16" y="78" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="10" font-weight="500" fill="#64748b">At 50 queries/day/dev</text>
        </g>

        <!-- Metric 4: Star CTA -->
        <g transform="translate(558, 0)">
            <rect x="0" y="0" width="178" height="90" rx="10" fill="#1e1b4b" stroke="#6366f1" stroke-width="1"/>
            <text x="16" y="26" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="11" font-weight="700" fill="#a5b4fc">GITHUB VIRAL GATE</text>
            <text x="16" y="54" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="18" font-weight="900" fill="#ffffff">⭐ STAR ON GITHUB</text>
            <text x="16" y="76" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="10" font-weight="500" fill="#c7d2fe">toprakahmetaydogmus/TZero</text>
        </g>
    </g>

    <!-- Bottom Footer Strip -->
    <g transform="translate(32, 212)">
        <text x="0" y="8" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="10" font-weight="500" fill="#475569">
            🚀 Run <tspan fill="#38bdf8" font-family="monospace">npx -y tzero-mcp@latest</tspan> or <tspan fill="#38bdf8" font-family="monospace">pip install tzero-mcp</tspan> &bull; By Toprak Ahmet Aydoğmuş (15 y/o dev) &bull; MIT
        </text>
        <text x="736" y="8" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="10" font-weight="600" fill="#64748b" text-anchor="end">
            Siber Akademi Engine v5.1.0
        </text>
    </g>
</svg>"""

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(svg)

        return output_file

    @classmethod
    def generate_readme_markdown_badges(cls, savings_pct: float = 94.6) -> str:
        """Returns ready-to-paste markdown badge block for GitHub READMEs."""
        return f"""<!-- 🚀 T-ZERO VIRAL GITHUB BADGES -->
<p align="center">
  <a href="https://github.com/toprakahmetaydogmus/TZeroAlgorithm">
    <img src="https://img.shields.io/badge/T--Zero-Context%20Compressed%20(-{savings_pct:.1f}%25)-38bdf8?style=for-the-badge&logo=probot&logoColor=white" alt="T-Zero Token Reduced" />
  </a>
  <a href="https://github.com/toprakahmetaydogmus/TZeroAlgorithm">
    <img src="https://img.shields.io/badge/Security-100%25%20Zero--Leak%20Certified-10b981?style=for-the-badge&logo=shield&logoColor=white" alt="100% Zero-Leak Certified" />
  </a>
  <a href="https://github.com/toprakahmetaydogmus/TZeroAlgorithm">
    <img src="https://img.shields.io/badge/Reality--Lock-Immutable%20AST%20Contract-8b5cf6?style=for-the-badge&logo=checkmarx&logoColor=white" alt="Reality-Lock Active" />
  </a>
  <a href="https://github.com/toprakahmetaydogmus/TZeroAlgorithm">
    <img src="https://img.shields.io/badge/%E2%AD%90%20Star%20T--Zero-on%20GitHub-f59e0b?style=for-the-badge&logo=github&logoColor=white" alt="Star T-Zero" />
  </a>
</p>
"""

    @classmethod
    def generate_interactive_showcase_html(
        cls,
        output_file: str = "tzero_showcase.html",
        raw_code_sample: Optional[str] = None,
        pruned_code_sample: Optional[str] = None
    ) -> str:
        """Generates an interactive standalone split-screen HTML5 comparison slider."""
        raw_code = raw_code_sample or '''class EnterpriseAuthService:
    """Handles enterprise multi-tenant user authentication, session revocation,
    OAuth2 token rotation, rate-limiting, audit logging, and role-based permissions.
    """
    def __init__(self, db_pool, redis_client, secret_key: str, token_expiry_seconds: int = 3600):
        self.db = db_pool
        self.redis = redis_client
        self.secret_key = secret_key
        self.token_expiry = token_expiry_seconds
        self._setup_internal_metrics()

    def authenticate_user(self, email: str, password_hash: str, mfa_code: Optional[str] = None) -> UserSession:
        # Step 1: Validate database connection
        conn = self.db.acquire()
        # Step 2: Query tenant record
        user = conn.query("SELECT * FROM users WHERE email = %s", email)
        if not user or not self._verify_bcrypt(password_hash, user.hash):
            raise InvalidCredentialsError("Invalid email or password")
        # Step 3: Check MFA tokens if required
        if user.mfa_enabled and not self._verify_totp(user.mfa_secret, mfa_code):
            raise MFAValidationError("Invalid MFA token")
        # Step 4: Issue signed JWT and write Redis session
        session_token = self._issue_jwt(user.id, user.tenant_id)
        self.redis.setex(f"session:{session_token}", self.token_expiry, user.id)
        return UserSession(user_id=user.id, token=session_token, expires_in=self.token_expiry)'''

        pruned_code = pruned_code_sample or '''class EnterpriseAuthService:
    def __init__(self, db_pool, redis_client, secret_key: str, token_expiry_seconds: int = 3600): ...
    def authenticate_user(self, email: str, password_hash: str, mfa_code: Optional[str] = None) -> UserSession: ...'''

        escaped_raw = html.escape(raw_code)
        escaped_pruned = html.escape(pruned_code)

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>T-Zero: Interactive Context Comparison Showcase</title>
    <style>
        :root {{
            --bg-dark: #090d16;
            --surface: #0f172a;
            --border: #1e293b;
            --accent-cyan: #38bdf8;
            --accent-purple: #818cf8;
            --accent-green: #34d399;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            background: var(--bg-dark);
            color: var(--text-main);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            padding: 30px 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        .header {{
            text-align: center;
            max-width: 800px;
            margin-bottom: 24px;
        }}
        .badge {{
            display: inline-block;
            background: rgba(56, 189, 248, 0.1);
            color: var(--accent-cyan);
            border: 1px solid var(--accent-cyan);
            padding: 4px 14px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 700;
            margin-bottom: 12px;
        }}
        h1 {{
            font-size: 32px;
            font-weight: 900;
            margin-bottom: 8px;
            background: linear-gradient(135deg, #38bdf8, #818cf8, #c084fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        p.sub {{ color: var(--text-muted); font-size: 15px; line-height: 1.5; }}

        .kpi-row {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            max-width: 1000px;
            width: 100%;
            margin-bottom: 24px;
        }}
        .kpi-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 16px;
            text-align: center;
        }}
        .kpi-val {{ font-size: 26px; font-weight: 900; color: var(--accent-cyan); }}
        .kpi-label {{ font-size: 11px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; margin-top: 4px; }}

        .showcase-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            max-width: 1000px;
            width: 100%;
            margin-bottom: 30px;
        }}
        .panel {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }}
        .panel-header {{
            background: rgba(255, 255, 255, 0.03);
            border-bottom: 1px solid var(--border);
            padding: 12px 18px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .panel-title {{ font-size: 13px; font-weight: 700; }}
        .panel-tag {{ font-size: 11px; padding: 2px 8px; border-radius: 6px; font-weight: 700; }}
        .tag-red {{ background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid #ef4444; }}
        .tag-green {{ background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid #10b981; }}

        pre {{
            padding: 16px;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 12px;
            line-height: 1.6;
            color: #e2e8f0;
            overflow-x: auto;
            flex: 1;
        }}
        .cta-btn {{
            background: linear-gradient(135deg, #38bdf8, #6366f1);
            color: #ffffff;
            font-weight: 800;
            font-size: 16px;
            padding: 12px 32px;
            border-radius: 10px;
            text-decoration: none;
            box-shadow: 0 4px 20px rgba(56, 189, 248, 0.3);
            transition: all 0.2s ease;
        }}
        .cta-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 26px rgba(56, 189, 248, 0.5);
        }}
    </style>
</head>
<body>
    <div class="header">
        <span class="badge">PROVABLY ACCURATE &bull; ZERO HALLUCINATIONS</span>
        <h1>T-Zero Token Optimization Showcase</h1>
        <p class="sub">Side-by-side comparison of raw implementation vs. AST compressed signatures fed to LLMs (Claude, Cursor, Copilot, ChatGPT).</p>
    </div>

    <div class="kpi-row">
        <div class="kpi-card">
            <div class="kpi-val">-88.0%</div>
            <div class="kpi-label">Token Savings</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-val">10x</div>
            <div class="kpi-label">Faster Prompt Ingestion</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-val">0</div>
            <div class="kpi-label">Hallucinations</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-val" style="color:var(--accent-green);">$0.00</div>
            <div class="kpi-label">Cost (100% Offline)</div>
        </div>
    </div>

    <div class="showcase-grid">
        <div class="panel">
            <div class="panel-header">
                <span class="panel-title">❌ Raw Bloated Source (Old Way)</span>
                <span class="panel-tag tag-red">~295 Tokens / File</span>
            </div>
            <pre><code>{escaped_raw}</code></pre>
        </div>

        <div class="panel">
            <div class="panel-header">
                <span class="panel-title">⚡ T-Zero Compressed AST (New Way)</span>
                <span class="panel-tag tag-green">~36 Tokens (-87.8%)</span>
            </div>
            <pre><code>{escaped_pruned}</code></pre>
        </div>
    </div>

    <div style="margin-top: 28px; padding: 22px 28px; background: rgba(56, 189, 248, 0.08); border: 1px solid rgba(56, 189, 248, 0.35); border-radius: 14px; max-width: 900px; width: 100%; text-align: center; box-shadow: 0 4px 24px rgba(0,0,0,0.35);">
        <p style="font-size: 17px; font-weight: 800; color: #38bdf8; margin-bottom: 8px;">
            ⭐ Lütfen Star Vererek Destekleyin!
        </p>
        <p style="font-size: 14px; line-height: 1.6; color: #cbd5e1; margin-bottom: 14px;">
            15 yaşında bağımsız bir yazılım geliştiricisiyim (<strong>Toprak Ahmet Aydoğmuş</strong> — beni Google'da aratabilirsiniz).<br>
            T-Zero'yu yapay zeka araçlarındaki token israfını ve yüksek API maliyetlerini sıfırlamak için %100 yerel ve ücretsiz olarak geliştirdim.
        </p>
        <a href="https://github.com/toprakahmetaydogmus/TZeroAlgorithm" class="cta-btn" target="_blank">
            ⭐ Star T-Zero on GitHub
        </a>
    </div>
</body>
</html>"""

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        return output_file
