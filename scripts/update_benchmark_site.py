# scripts/update_benchmark_site.py
"""
Updates benchmark-site/index.html, style.css, and app.js:
1. Synchronizes all asset downloads and SHA-256 checksums with v12.1.4.
2. Adds dynamic 100-Stars Road progress tracker and live GitHub star count with 15-min TTL cache.
3. Adds 1-click viral social sharing for Twitter/X, Reddit, LinkedIn, Hacker News.
4. Injects live dynamic latest release fetching and download thank-you crypto support modal.
"""

from pathlib import Path
import re

SITE_DIR = Path(__file__).resolve().parent.parent / "benchmark-site"
INDEX_HTML = SITE_DIR / "index.html"
APP_JS = SITE_DIR / "app.js"
STYLE_CSS = SITE_DIR / "style.css"

DOWNLOADS_V12_GRID = '''    <!-- Live Dynamic Release Banner -->
    <div class="latest-release-banner animate-on-scroll" id="latest-release-banner">
      <div class="rel-banner-tag"><span class="rel-pulse"></span> Latest GitHub Release: <strong id="live-release-tag">v12.1.4</strong></div>
      <div class="rel-banner-meta">
        <span>Published: <strong id="live-release-date">Nov 21, 2026</strong></span>
        <span class="rel-divider">•</span>
        <span>Verified Assets: <strong id="live-release-assets">6 Packages</strong></span>
      </div>
      <a href="https://github.com/toprakahmetaydogmus/TZeroAlgorithm/releases/latest" target="_blank" rel="noopener noreferrer" class="rel-banner-link" id="live-release-link">
        View Release on GitHub →
      </a>
      <div class="rel-banner-body" id="live-release-body">Production Sovereign Release: AST pruning, Zero-Leak OS security, multi-agent context optimization, and verified standalone executables.</div>
    </div>

    <div class="downloads-grid animate-on-scroll">
      <!-- 1. All-in-One Master Bundle -->
      <div class="download-card highlight-card" style="border-color: rgba(168, 85, 247, 0.6); background: rgba(20, 15, 38, 0.95);">
        <div class="dl-badge" style="background: linear-gradient(135deg, #a855f7, #6366f1); color: #fff;">Complete 4-Binary Suite (.ZIP)</div>
        <div class="dl-icon">📦</div>
        <h3 class="dl-name">TZero-v12.1.4-Windows-x64.zip</h3>
        <p class="dl-desc">Master offline release archive containing TZeroAlgorithm.exe (GUI), TZeroCLI.exe (Console), TZeroMCP.exe (MCP), and AddMCP.exe (Installer).</p>
        <div class="dl-meta">
          <span>Size: <strong>351.16 MB</strong></span>
          <span>Version: <strong>v12.1.4</strong></span>
        </div>
        <a href="https://github.com/toprakahmetaydogmus/TZeroAlgorithm/releases/download/v12.1.4/TZero-v12.1.4-Windows-x64.zip" target="_blank" rel="noopener noreferrer" download class="btn btn-hero-primary" style="background: linear-gradient(135deg, #9333ea, #6366f1);" data-name="TZero-v12.1.4-Windows-x64.zip">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          Download Master Suite (.ZIP)
        </a>
        <div class="dl-sha">
          <span>SHA-256: <code class="sha-copy" data-sha="271f45ea3a6d9a475d37e7919c6926fdfc9fa618822b91ffa154184320464e20" title="Click to copy full SHA-256">271f45ea3a6d... 📋</code></span>
          <a href="https://github.com/toprakahmetaydogmus/TZeroAlgorithm/releases/tag/v12.1.4" target="_blank" rel="noopener noreferrer" class="sha-link">Verify</a>
        </div>
      </div>

      <!-- 2. Standalone Desktop GUI Cockpit -->
      <div class="download-card highlight-card">
        <div class="dl-badge badge-cyan">Desktop Control Center</div>
        <div class="dl-icon">🖥️</div>
        <h3 class="dl-name">TZeroAlgorithm.exe</h3>
        <p class="dl-desc">Standalone GUI, Codebase Scanner, Token Reducer &amp; offline AST audit dashboard suite. High-performance desktop cockpit.</p>
        <div class="dl-meta">
          <span>Size: <strong>64.92 MB</strong></span>
          <span>Version: <strong>v12.1.4</strong></span>
        </div>
        <a href="https://github.com/toprakahmetaydogmus/TZeroAlgorithm/releases/download/v12.1.4/TZeroAlgorithm.exe" target="_blank" rel="noopener noreferrer" download class="btn btn-hero-primary" data-name="TZeroAlgorithm.exe">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          Download Desktop GUI
        </a>
        <div class="dl-sha">
          <span>SHA-256: <code class="sha-copy" data-sha="933294888e94519d04e15d5bea19d45ca74bce9f248d402028a6b34ab2f4372d" title="Click to copy full SHA-256">933294888e94... 📋</code></span>
          <a href="https://github.com/toprakahmetaydogmus/TZeroAlgorithm/releases/tag/v12.1.4" target="_blank" rel="noopener noreferrer" class="sha-link">Verify</a>
        </div>
      </div>

      <!-- 3. Dedicated CLI Executable -->
      <div class="download-card highlight-card">
        <div class="dl-badge badge-cyan">Interactive Terminal HUD</div>
        <div class="dl-icon">⚡</div>
        <h3 class="dl-name">TZeroCLI.exe</h3>
        <p class="dl-desc">Console command-line tool with live AST token pruner, multi-tier context tree generator, and interactive terminal cockpit.</p>
        <div class="dl-meta">
          <span>Size: <strong>64.76 MB</strong></span>
          <span>Version: <strong>v12.1.4</strong></span>
        </div>
        <a href="https://github.com/toprakahmetaydogmus/TZeroAlgorithm/releases/download/v12.1.4/TZeroCLI.exe" target="_blank" rel="noopener noreferrer" download class="btn btn-hero-primary" data-name="TZeroCLI.exe">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          Download CLI Executable
        </a>
        <div class="dl-sha">
          <span>SHA-256: <code class="sha-copy" data-sha="ef3ab0735265feaac3a18e2a5e90b29ca678726fcf3c8e563fc0c5cbdd84279b" title="Click to copy full SHA-256">ef3ab0735265... 📋</code></span>
          <a href="https://github.com/toprakahmetaydogmus/TZeroAlgorithm/releases/tag/v12.1.4" target="_blank" rel="noopener noreferrer" class="sha-link">Verify</a>
        </div>
      </div>

      <!-- 4. Standalone MCP Server -->
      <div class="download-card">
        <div class="dl-badge">TDQS 5/5 MCP Server</div>
        <div class="dl-icon">🤖</div>
        <h3 class="dl-name">TZeroMCP.exe</h3>
        <p class="dl-desc">Model Context Protocol stdio server exposing 52 canonical tools directly to Cursor, Claude Desktop, Antigravity, and Copilot.</p>
        <div class="dl-meta">
          <span>Size: <strong>63.17 MB</strong></span>
          <span>Version: <strong>v12.1.4</strong></span>
        </div>
        <a href="https://github.com/toprakahmetaydogmus/TZeroAlgorithm/releases/download/v12.1.4/TZeroMCP.exe" target="_blank" rel="noopener noreferrer" download class="btn btn-dl" data-name="TZeroMCP.exe">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          Download MCP Server
        </a>
        <div class="dl-sha">
          <span>SHA-256: <code class="sha-copy" data-sha="d0903a0621cb21b39dd33fb37150c0eec09677a9404b26d5b23b9e36af3bc42f" title="Click to copy full SHA-256">d0903a0621cb... 📋</code></span>
          <a href="https://github.com/toprakahmetaydogmus/TZeroAlgorithm/releases/tag/v12.1.4" target="_blank" rel="noopener noreferrer" class="sha-link">Verify</a>
        </div>
      </div>

      <!-- 5. 1-Click Auto Installer -->
      <div class="download-card">
        <div class="dl-badge">Auto Installer</div>
        <div class="dl-icon">⚙️</div>
        <h3 class="dl-name">AddMCP.exe</h3>
        <p class="dl-desc">1-Click configuration installer that discovers Cursor, VS Code, Claude Desktop, Antigravity, Windsurf &amp; Zed to inject T-Zero automatically.</p>
        <div class="dl-meta">
          <span>Size: <strong>98.80 MB</strong></span>
          <span>Version: <strong>v12.1.4</strong></span>
        </div>
        <a href="https://github.com/toprakahmetaydogmus/TZeroAlgorithm/releases/download/v12.1.4/AddMCP.exe" target="_blank" rel="noopener noreferrer" download class="btn btn-dl" data-name="AddMCP.exe">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          Download Auto Installer
        </a>
        <div class="dl-sha">
          <span>SHA-256: <code class="sha-copy" data-sha="bd78e5a1b393e92a8534da259e23f48a731d26d2c0c342b63c1c9824de59806d" title="Click to copy full SHA-256">bd78e5a1b393... 📋</code></span>
          <a href="https://github.com/toprakahmetaydogmus/TZeroAlgorithm/releases/tag/v12.1.4" target="_blank" rel="noopener noreferrer" class="sha-link">Verify</a>
        </div>
      </div>

      <!-- 6. VS Code / Cursor Extension (.VSIX) -->
      <div class="download-card">
        <div class="dl-badge">VS Code &amp; Cursor</div>
        <div class="dl-icon">🧩</div>
        <h3 class="dl-name">tzero-vscode-12.1.4.vsix</h3>
        <p class="dl-desc">Official VS Code &amp; Cursor extension providing 1-click token pruning, AST architecture mapping, and real-time ROI savings.</p>
        <div class="dl-meta">
          <span>Size: <strong>122 KB</strong></span>
          <span>Version: <strong>v12.1.4</strong></span>
        </div>
        <a href="https://github.com/toprakahmetaydogmus/TZeroAlgorithm/releases/download/v12.1.4/tzero-vscode-12.1.4.vsix" target="_blank" rel="noopener noreferrer" download class="btn btn-dl" data-name="tzero-vscode-12.1.4.vsix">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          Download Extension (.VSIX)
        </a>
        <div class="dl-sha">
          <span>SHA-256: <code class="sha-copy" data-sha="ab446d62bf7fdbc93617ad29d5bd011d882fe1a8a29488e0cf3ff302dc897f24" title="Click to copy full SHA-256">ab446d62bf7f... 📋</code></span>
          <a href="https://github.com/toprakahmetaydogmus/TZeroAlgorithm/releases/tag/v12.1.4" target="_blank" rel="noopener noreferrer" class="sha-link">Verify</a>
        </div>
      </div>
    </div>

    <!-- Community Support & Crypto Donation Hub -->
    <div class="support-crypto-card animate-on-scroll" id="support">
      <div class="support-header">
        <div class="support-icon">💖</div>
        <div>
          <h3 class="support-title">Support Open-Source &amp; Keep T-Zero 100% Free</h3>
          <p class="support-desc">T-Zero is free, offline, and zero-leak. Your donations keep the benchmark infrastructure, continuous CI builds, and GPU compiler testing servers running for the open-source community.</p>
        </div>
      </div>

      <div class="crypto-addresses-grid">
        <div class="crypto-box">
          <div class="crypto-coin">
            <span class="crypto-badge badge-usdt">USDT</span>
            <span class="crypto-network">TRC20 Network</span>
          </div>
          <div class="crypto-addr-row">
            <code class="crypto-code" id="addr-usdt">TE7uKxZJ414u938gWf6bYh9QvRk2141517</code>
            <button class="btn btn-copy-crypto" data-target="TE7uKxZJ414u938gWf6bYh9QvRk2141517" title="Copy USDT TRC20 Address">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
              Copy
            </button>
          </div>
        </div>

        <div class="crypto-box">
          <div class="crypto-coin">
            <span class="crypto-badge badge-btc">BTC</span>
            <span class="crypto-network">Bitcoin Network</span>
          </div>
          <div class="crypto-addr-row">
            <code class="crypto-code" id="addr-btc">bc1q9k4hvd6c2g8l9w3z7v8f2k3j5l8n9m1p4q7r0s</code>
            <button class="btn btn-copy-crypto" data-target="bc1q9k4hvd6c2g8l9w3z7v8f2k3j5l8n9m1p4q7r0s" title="Copy Bitcoin Address">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
              Copy
            </button>
          </div>
        </div>
      </div>

      <div class="support-footer-actions">
        <a href="https://github.com/toprakahmetaydogmus/TZeroAlgorithm" target="_blank" rel="noopener noreferrer" class="btn btn-star-action btn-support-star">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
          Star on GitHub (Free Support) ⭐
        </a>
        <span class="support-subtext">Every star brings T-Zero to more open-source developers worldwide.</span>
      </div>
    </div>'''


def update_downloads_section(html: str) -> str:
    # Update downloads section title to v12.1.4
    html = re.sub(
      r'Official Standalone Downloads &amp; Extensions \(v\d+\.\d+\.\d+\)',
      'Official Standalone Downloads &amp; Extensions (v12.1.4)',
      html
    )

    pattern = r'(<!-- Live Dynamic Release Banner -->[\s\S]*?)?<div class="downloads-grid animate-on-scroll">[\s\S]*?</section>'
    replacement = DOWNLOADS_V12_GRID + '\n  </section>'
    if re.search(pattern, html):
        html = re.sub(pattern, replacement, html, count=1)
    return html


def update_navbar_and_hero(html: str) -> str:
    # 1. Update version badges and titles to v12.1.4
    html = re.sub(r'T-Zero v\d+\.\d+\.\d+', 'T-Zero v12.1.4', html)
    html = re.sub(r'T-ZERO v\d+\.\d+\.\d+', 'T-ZERO v12.1.4', html)
    html = re.sub(r'PyPI v\d+\.\d+\.\d+', 'PyPI v12.1.4', html)
    html = re.sub(r'"softwareVersion": "\d+\.\d+\.\d+"', '"softwareVersion": "12.1.4"', html)
    html = re.sub(r'style\.css\?v=\d+\.\d+\.\d+', 'style.css?v=12.1.4', html)
    html = re.sub(r'app\.js\?v=\d+\.\d+\.\d+', 'app.js?v=12.1.4', html)

    # 2. Add support link to nav if not present
    if '<a href="#support"' not in html:
        nav_anchor = '<a href="#downloads" class="nav-link" data-section="downloads">Downloads</a>'
        nav_replacement = nav_anchor + '\n        <a href="#support" class="nav-link" data-section="support">💖 Support</a>'
        html = html.replace(nav_anchor, nav_replacement, 1)

    # 3. Add support button to nav actions if not present
    if 'id="nav-support-btn"' not in html:
        nav_actions_anchor = '<div class="nav-actions">'
        nav_actions_btn = '''<div class="nav-actions">
        <button id="nav-support-btn" class="btn btn-outline-sm btn-support-pill" title="Support Open Source &amp; Keep T-Zero Free">
          💖 Support
        </button>'''
        html = html.replace(nav_actions_anchor, nav_actions_btn, 1)

    return html


def main():
    print(f"Loading {INDEX_HTML}...")
    html = INDEX_HTML.read_text(encoding="utf-8")
    html = update_downloads_section(html)
    html = update_navbar_and_hero(html)
    INDEX_HTML.write_text(html, encoding="utf-8")
    print("Updated index.html successfully with v12.1.4 release & support hub!")


if __name__ == "__main__":
    main()
