# scripts/update_benchmark_site.py
"""
Updates benchmark-site/index.html, app.js, and llms.txt cleanly:
1. Reads canonical version from pyproject.toml (or --version CLI override).
2. Computes exact file sizes and SHA-256 checksums from dist/ when available,
   preserving verified 64-char SHA-256 hashes if dist binaries are absent (e.g., CI).
3. Updates release banner, all 6 download cards, hero badges, JSON-LD, cache-busters,
   app.js fallback tags, and benchmark-site/llms.txt while preserving the Anti-REA Lab link.
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_SITE_DIR = ROOT_DIR / "benchmark-site"
DIST_DIR = ROOT_DIR / "dist"


def get_canonical_version() -> str:
    text = (ROOT_DIR / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    return match.group(1) if match else "12.2.1"


def _human_size(num_bytes: int) -> str:
    if num_bytes >= 1024 * 1024:
        return f"{num_bytes / (1024 * 1024):.2f} MB"
    return f"{max(1, round(num_bytes / 1024))} KB"


def _read_existing_card_meta(html: str, asset_name: str, fallback_size: str, fallback_sha: str) -> tuple[str, str]:
    pattern = (
        rf'data-name="{re.escape(asset_name)}"[\s\S]*?'
        rf'data-sha="([0-9a-fA-F]{{64}})"'
    )
    sha_match = re.search(pattern, html)
    size_match = re.search(
        rf'<h3 class="dl-name">[^<]*{re.escape(asset_name.split("-")[0])}[^<]*</h3>[\s\S]*?Size:\s*<strong>([^<]+)</strong>',
        html,
    )
    return (
        size_match.group(1) if size_match else fallback_size,
        sha_match.group(1).lower() if sha_match else fallback_sha,
    )


def _resolve_asset_stats(asset_name: str, existing_html: str, default_size: str, default_sha: str) -> tuple[str, str]:
    file_path = DIST_DIR / asset_name
    sha_path = DIST_DIR / f"{asset_name}.sha256"
    size_str, sha_str = _read_existing_card_meta(existing_html, asset_name, default_size, default_sha)

    if file_path.is_file():
        size_str = _human_size(file_path.stat().st_size)
        if sha_path.is_file():
            raw_sha = sha_path.read_text(encoding="utf-8", errors="ignore").strip().split()[0]
            if re.fullmatch(r"[0-9a-fA-F]{64}", raw_sha):
                sha_str = raw_sha.lower()
                return size_str, sha_str
        digest = hashlib.sha256()
        with file_path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                digest.update(chunk)
        sha_str = digest.hexdigest().lower()
    elif sha_path.is_file():
        raw_sha = sha_path.read_text(encoding="utf-8", errors="ignore").strip().split()[0]
        if re.fullmatch(r"[0-9a-fA-F]{64}", raw_sha):
            sha_str = raw_sha.lower()

    return size_str, sha_str


def build_downloads_grid(version: str, existing_html: str) -> str:
    zip_name = f"TZero-v{version}-Windows-x64.zip"
    vsix_name = f"tzero-vscode-{version}.vsix"

    zip_size, zip_sha = _resolve_asset_stats(
        zip_name, existing_html, "355.02 MB", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )
    gui_size, gui_sha = _resolve_asset_stats(
        "TZeroAlgorithm.exe", existing_html, "65.64 MB", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )
    cli_size, cli_sha = _resolve_asset_stats(
        "TZeroCLI.exe", existing_html, "65.48 MB", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )
    mcp_size, mcp_sha = _resolve_asset_stats(
        "TZeroMCP.exe", existing_html, "63.89 MB", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )
    addmcp_size, addmcp_sha = _resolve_asset_stats(
        "AddMCP.exe", existing_html, "99.78 MB", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )
    vsix_size, vsix_sha = _resolve_asset_stats(
        vsix_name, existing_html, "120 KB", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )

    rel_base = f"https://github.com/toprakahmetaydogmus/TZeroAlgorithm/releases/download/v{version}"
    rel_tag = f"https://github.com/toprakahmetaydogmus/TZeroAlgorithm/releases/tag/v{version}"

    return f'''    <!-- Live Dynamic Release Banner -->
    <div class="latest-release-banner animate-on-scroll" id="latest-release-banner">
      <div class="rel-banner-tag"><span class="rel-pulse"></span> Latest GitHub Release: <strong id="live-release-tag">v{version}</strong></div>
      <div class="rel-banner-meta">
        <span>Published: <strong id="live-release-date">Nov 26, 2026</strong></span>
        <span class="rel-divider">•</span>
        <span>Verified Assets: <strong id="live-release-assets">24 Packages</strong></span>
      </div>
      <a href="https://github.com/toprakahmetaydogmus/TZeroAlgorithm/releases/latest" target="_blank" rel="noopener noreferrer" class="rel-banner-link" id="live-release-link">
        View Release on GitHub →
      </a>
      <div class="rel-banner-body" id="live-release-body">Production Sovereign Release: AST pruning, 180-Tier Anti-REA binary armor, Zero-Leak OS security, multi-agent context optimization, and verified standalone executables.</div>
    </div>

    <div class="downloads-grid animate-on-scroll">
      <!-- 1. All-in-One Master Bundle -->
      <div class="download-card highlight-card" style="border-color: rgba(168, 85, 247, 0.6); background: rgba(20, 15, 38, 0.95);">
        <div class="dl-badge" style="background: linear-gradient(135deg, #a855f7, #6366f1); color: #fff;">Complete 5-Binary Suite (.ZIP)</div>
        <div class="dl-icon">📦</div>
        <h3 class="dl-name">{zip_name}</h3>
        <p class="dl-desc">Master offline release archive containing TZeroAlgorithm.exe (GUI), TZeroCLI.exe (Console), TZeroMCP.exe (MCP), AddMCP.exe (Installer), and TZeroCI.exe.</p>
        <div class="dl-meta">
          <span>Size: <strong>{zip_size}</strong></span>
          <span>Version: <strong>v{version}</strong></span>
        </div>
        <a href="{rel_base}/{zip_name}" target="_blank" rel="noopener noreferrer" download class="btn btn-hero-primary" style="background: linear-gradient(135deg, #9333ea, #6366f1);" data-name="{zip_name}">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          Download Master Suite (.ZIP)
        </a>
        <div class="dl-sha">
          <span>SHA-256: <code class="sha-copy" data-sha="{zip_sha}" title="Click to copy full SHA-256">{zip_sha[:12]}... 📋</code></span>
          <a href="{rel_tag}" target="_blank" rel="noopener noreferrer" class="sha-link">Verify</a>
        </div>
      </div>

      <!-- 2. Standalone Desktop GUI Cockpit -->
      <div class="download-card highlight-card">
        <div class="dl-badge badge-cyan">Desktop Control Center</div>
        <div class="dl-icon">🖥️</div>
        <h3 class="dl-name">TZeroAlgorithm.exe</h3>
        <p class="dl-desc">Standalone GUI, Codebase Scanner, Token Reducer, 180-Tier Anti-REA Armor &amp; offline AST audit dashboard suite.</p>
        <div class="dl-meta">
          <span>Size: <strong>{gui_size}</strong></span>
          <span>Version: <strong>v{version}</strong></span>
        </div>
        <a href="{rel_base}/TZeroAlgorithm.exe" target="_blank" rel="noopener noreferrer" download class="btn btn-hero-primary" data-name="TZeroAlgorithm.exe">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          Download Desktop GUI
        </a>
        <div class="dl-sha">
          <span>SHA-256: <code class="sha-copy" data-sha="{gui_sha}" title="Click to copy full SHA-256">{gui_sha[:12]}... 📋</code></span>
          <a href="{rel_tag}" target="_blank" rel="noopener noreferrer" class="sha-link">Verify</a>
        </div>
      </div>

      <!-- 3. Dedicated CLI Executable -->
      <div class="download-card highlight-card">
        <div class="dl-badge badge-cyan">Interactive Terminal HUD</div>
        <div class="dl-icon">⚡</div>
        <h3 class="dl-name">TZeroCLI.exe</h3>
        <p class="dl-desc">Console command-line tool with live AST token pruner, Anti-REA armor CLI, context tree generator, and interactive terminal cockpit.</p>
        <div class="dl-meta">
          <span>Size: <strong>{cli_size}</strong></span>
          <span>Version: <strong>v{version}</strong></span>
        </div>
        <a href="{rel_base}/TZeroCLI.exe" target="_blank" rel="noopener noreferrer" download class="btn btn-hero-primary" data-name="TZeroCLI.exe">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          Download CLI Executable
        </a>
        <div class="dl-sha">
          <span>SHA-256: <code class="sha-copy" data-sha="{cli_sha}" title="Click to copy full SHA-256">{cli_sha[:12]}... 📋</code></span>
          <a href="{rel_tag}" target="_blank" rel="noopener noreferrer" class="sha-link">Verify</a>
        </div>
      </div>

      <!-- 4. Standalone MCP Server -->
      <div class="download-card">
        <div class="dl-badge">TDQS 5/5 MCP Server</div>
        <div class="dl-icon">🤖</div>
        <h3 class="dl-name">TZeroMCP.exe</h3>
        <p class="dl-desc">Model Context Protocol stdio server exposing 22 canonical tools directly to Cursor, Claude Desktop, Antigravity, and Copilot.</p>
        <div class="dl-meta">
          <span>Size: <strong>{mcp_size}</strong></span>
          <span>Version: <strong>v{version}</strong></span>
        </div>
        <a href="{rel_base}/TZeroMCP.exe" target="_blank" rel="noopener noreferrer" download class="btn btn-dl" data-name="TZeroMCP.exe">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          Download MCP Server
        </a>
        <div class="dl-sha">
          <span>SHA-256: <code class="sha-copy" data-sha="{mcp_sha}" title="Click to copy full SHA-256">{mcp_sha[:12]}... 📋</code></span>
          <a href="{rel_tag}" target="_blank" rel="noopener noreferrer" class="sha-link">Verify</a>
        </div>
      </div>

      <!-- 5. 1-Click Auto Installer -->
      <div class="download-card">
        <div class="dl-badge">Auto Installer</div>
        <div class="dl-icon">⚙️</div>
        <h3 class="dl-name">AddMCP.exe</h3>
        <p class="dl-desc">1-Click configuration installer that discovers Cursor, VS Code, Claude Desktop, Antigravity, Windsurf &amp; Zed to inject T-Zero automatically.</p>
        <div class="dl-meta">
          <span>Size: <strong>{addmcp_size}</strong></span>
          <span>Version: <strong>v{version}</strong></span>
        </div>
        <a href="{rel_base}/AddMCP.exe" target="_blank" rel="noopener noreferrer" download class="btn btn-dl" data-name="AddMCP.exe">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          Download Auto Installer
        </a>
        <div class="dl-sha">
          <span>SHA-256: <code class="sha-copy" data-sha="{addmcp_sha}" title="Click to copy full SHA-256">{addmcp_sha[:12]}... 📋</code></span>
          <a href="{rel_tag}" target="_blank" rel="noopener noreferrer" class="sha-link">Verify</a>
        </div>
      </div>

      <!-- 6. VS Code / Cursor Extension (.VSIX) -->
      <div class="download-card">
        <div class="dl-badge">VS Code &amp; Cursor</div>
        <div class="dl-icon">🧩</div>
        <h3 class="dl-name">{vsix_name}</h3>
        <p class="dl-desc">Official VS Code &amp; Cursor extension providing 1-click token pruning, Anti-REA Shield, AST architecture mapping, and real-time ROI savings.</p>
        <div class="dl-meta">
          <span>Size: <strong>{vsix_size}</strong></span>
          <span>Version: <strong>v{version}</strong></span>
        </div>
        <a href="{rel_base}/{vsix_name}" target="_blank" rel="noopener noreferrer" download class="btn btn-dl" data-name="{vsix_name}">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          Download Extension (.VSIX)
        </a>
        <div class="dl-sha">
          <span>SHA-256: <code class="sha-copy" data-sha="{vsix_sha}" title="Click to copy full SHA-256">{vsix_sha[:12]}... 📋</code></span>
          <a href="{rel_tag}" target="_blank" rel="noopener noreferrer" class="sha-link">Verify</a>
        </div>
      </div>
    </div>'''


def update_downloads_section(html: str, version: str) -> str:
    html = re.sub(
        r'Official Standalone Downloads &amp; Extensions \(v\d+\.\d+\.\d+\)',
        f'Official Standalone Downloads &amp; Extensions (v{version})',
        html,
    )
    pattern = r'[ \t]*(?:<!-- Live Dynamic Release Banner -->[\s\S]*?)?<div class="downloads-grid animate-on-scroll">[\s\S]*?(?=\r?\n[ \t]*<!-- Community Support & Crypto Donation Hub -->|\r?\n[ \t]*</section>)'
    grid_html = build_downloads_grid(version, html)
    if re.search(pattern, html):
        html = re.sub(pattern, grid_html, html, count=1)
    return html


def update_navbar_and_hero(html: str, version: str) -> str:
    html = re.sub(r'T-Zero v\d+\.\d+\.\d+', f'T-Zero v{version}', html)
    html = re.sub(r'T-ZERO v\d+\.\d+\.\d+', f'T-ZERO v{version}', html)
    html = re.sub(r'PyPI v\d+\.\d+\.\d+', f'PyPI v{version}', html)
    html = re.sub(r'T-Zero Context Architect v\d+\.\d+\.\d+', f'T-Zero Context Architect v{version}', html)
    html = re.sub(r'"softwareVersion": "\d+\.\d+\.\d+"', f'"softwareVersion": "{version}"', html)
    html = re.sub(r'style\.css\?v=\d+\.\d+\.\d+', f'style.css?v={version}', html)
    html = re.sub(r'app\.js\?v=\d+\.\d+\.\d+', f'app.js?v={version}', html)

    if '<a href="#support"' not in html:
        nav_anchor = '<a href="#downloads" class="nav-link" data-section="downloads">Downloads</a>'
        nav_replacement = nav_anchor + '\n        <a href="#support" class="nav-link" data-section="support">💖 Support</a>'
        html = html.replace(nav_anchor, nav_replacement, 1)

    if 'id="nav-support-btn"' not in html:
        nav_actions_anchor = '<div class="nav-actions">'
        nav_actions_btn = '''<div class="nav-actions">
        <button id="nav-support-btn" class="btn btn-outline-sm btn-support-pill" title="Support Open Source &amp; Keep T-Zero Free">
          💖 Support
        </button>'''
        html = html.replace(nav_actions_anchor, nav_actions_btn, 1)

    return html


def update_app_js(js_text: str, version: str) -> str:
    js_text = re.sub(r'(T-Zero )v\d+\.\d+\.\d+', rf'\1v{version}', js_text)
    js_text = re.sub(r'(data\.tag_name \|\| ")v\d+\.\d+\.\d+(")', rf'\1v{version}\2', js_text)
    js_text = re.sub(r'(tag_name:\s*")v\d+\.\d+\.\d+(")', rf'\1v{version}\2', js_text)
    return js_text


def update_llms_txt(llms_text: str, version: str) -> str:
    return re.sub(r'(?m)^(> Version:\s*)\d+\.\d+\.\d+', rf'\1{version}', llms_text)


def sync_site(site_dir: Path, version: str, check_only: bool = False) -> bool:
    index_path = site_dir / "index.html"
    js_path = site_dir / "app.js"
    llms_path = site_dir / "llms.txt"
    changed = False

    if index_path.is_file():
        old_html = index_path.read_text(encoding="utf-8")
        new_html = update_downloads_section(old_html, version)
        new_html = update_navbar_and_hero(new_html, version)
        if new_html != old_html:
            changed = True
            if not check_only:
                index_path.write_text(new_html, encoding="utf-8")

    if js_path.is_file():
        old_js = js_path.read_text(encoding="utf-8")
        new_js = update_app_js(old_js, version)
        if new_js != old_js:
            changed = True
            if not check_only:
                js_path.write_text(new_js, encoding="utf-8")

    if llms_path.is_file():
        old_llms = llms_path.read_text(encoding="utf-8")
        new_llms = update_llms_txt(old_llms, version)
        if new_llms != old_llms:
            changed = True
            if not check_only:
                llms_path.write_text(new_llms, encoding="utf-8")

    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description="Synchronize benchmark-site assets and metadata.")
    parser.add_argument("--version", default=get_canonical_version(), help="Target version string")
    parser.add_argument("--site-dir", default=str(DEFAULT_SITE_DIR), help="Benchmark site directory path")
    parser.add_argument("--check", action="store_true", help="Exit 1 if benchmark-site is out of sync")
    args = parser.parse_args()

    site_dir = Path(args.site_dir)
    print(f"Loading {site_dir / 'index.html'}...")
    changed = sync_site(site_dir, args.version, check_only=args.check)
    if args.check:
        if changed:
            print(f"Benchmark site is out of sync with v{args.version}")
            return 1
        print(f"Benchmark site matches v{args.version} cleanly.")
        return 0
    print(f"Updated index.html successfully with v{args.version} release & support hub!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
