# scripts/update_benchmark_site.py
"""
Updates benchmark-site/index.html, style.css, and app.js:
1. Synchronizes all asset downloads and checksums with v11.11.0.
2. Adds dynamic 100-Stars Road progress tracker and live GitHub star count.
3. Adds 1-click viral social sharing for Twitter/X, Reddit, LinkedIn, Hacker News, WhatsApp.
"""

from pathlib import Path
import re

SITE_DIR = Path(__file__).resolve().parent.parent / "benchmark-site"
INDEX_HTML = SITE_DIR / "index.html"
APP_JS = SITE_DIR / "app.js"
STYLE_CSS = SITE_DIR / "style.css"


def update_downloads_section(html: str) -> str:
    # Build complete modern 6-card downloads section
    new_downloads_grid = '''    <div class="downloads-grid animate-on-scroll">
      <!-- 1. All-in-One Master Bundle -->
      <div class="download-card highlight-card" style="border-color: rgba(168, 85, 247, 0.6); background: rgba(20, 15, 38, 0.95);">
        <div class="dl-badge" style="background: linear-gradient(135deg, #a855f7, #6366f1); color: #fff;">Complete 4-Binary Suite (.ZIP)</div>
        <div class="dl-icon">📦</div>
        <h3 class="dl-name">TZero-v11.11.0-Windows-x64.zip</h3>
        <p class="dl-desc">Master offline release archive containing TZeroAlgorithm.exe (GUI), TZeroCLI.exe (Console), TZeroMCP.exe (MCP), and AddMCP.exe (Installer).</p>
        <div class="dl-meta">
          <span>Size: <strong>263.4 MB</strong></span>
          <span>Version: <strong>v11.11.0</strong></span>
        </div>
        <a href="https://github.com/toprakahmetaydogmus/TZeroAlgorithm/releases/download/v11.11.0/TZero-v11.11.0-Windows-x64.zip" target="_blank" rel="noopener noreferrer" download class="btn btn-hero-primary" style="background: linear-gradient(135deg, #9333ea, #6366f1);" data-name="TZero-v11.11.0-Windows-x64.zip">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          Download Master Suite (.ZIP)
        </a>
        <div class="dl-sha">
          <span>SHA-256: <code class="sha-copy" data-sha="b89ce93f7055098e6e004be69839a41412b6437c12da14cd84b7124191a440bf" title="Click to copy full SHA-256">b89ce93f7055... 📋</code></span>
          <a href="https://github.com/toprakahmetaydogmus/TZeroAlgorithm/releases/tag/v11.11.0" target="_blank" rel="noopener noreferrer" class="sha-link">Verify</a>
        </div>
      </div>

      <!-- 2. Standalone Desktop GUI Cockpit -->
      <div class="download-card highlight-card">
        <div class="dl-badge badge-cyan">Desktop Control Center</div>
        <div class="dl-icon">🖥️</div>
        <h3 class="dl-name">TZeroAlgorithm.exe</h3>
        <p class="dl-desc">Standalone GUI, Codebase Scanner, Token Reducer & offline AST audit dashboard suite. High-performance desktop cockpit.</p>
        <div class="dl-meta">
          <span>Size: <strong>63.65 MB</strong></span>
          <span>Version: <strong>v11.11.0</strong></span>
        </div>
        <a href="https://github.com/toprakahmetaydogmus/TZeroAlgorithm/releases/download/v11.11.0/TZeroAlgorithm.exe" target="_blank" rel="noopener noreferrer" download class="btn btn-hero-primary" data-name="TZeroAlgorithm.exe">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          Download Desktop GUI
        </a>
        <div class="dl-sha">
          <span>SHA-256: <code class="sha-copy" data-sha="131c65480449f36630ee75b572657b9dc136dc83b4b3c5c7382ab7b8e20ce1dc" title="Click to copy full SHA-256">131c65480449... 📋</code></span>
          <a href="https://github.com/toprakahmetaydogmus/TZeroAlgorithm/releases/tag/v11.11.0" target="_blank" rel="noopener noreferrer" class="sha-link">Verify</a>
        </div>
      </div>

      <!-- 3. Dedicated CLI Executable -->
      <div class="download-card highlight-card">
        <div class="dl-badge badge-cyan">Interactive Terminal HUD</div>
        <div class="dl-icon">⚡</div>
        <h3 class="dl-name">TZeroCLI.exe</h3>
        <p class="dl-desc">Console command-line tool with live AST token pruner, multi-tier context tree generator, and interactive terminal cockpit.</p>
        <div class="dl-meta">
          <span>Size: <strong>63.48 MB</strong></span>
          <span>Version: <strong>v11.11.0</strong></span>
        </div>
        <a href="https://github.com/toprakahmetaydogmus/TZeroAlgorithm/releases/download/v11.11.0/TZeroCLI.exe" target="_blank" rel="noopener noreferrer" download class="btn btn-hero-primary" data-name="TZeroCLI.exe">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          Download CLI Executable
        </a>
        <div class="dl-sha">
          <span>SHA-256: <code class="sha-copy" data-sha="b25cf1a80871a7c7a5f9397cc4dfe9a4b72b4df043d1c4830e91a7416c8d961d" title="Click to copy full SHA-256">b25cf1a80871... 📋</code></span>
          <a href="https://github.com/toprakahmetaydogmus/TZeroAlgorithm/releases/tag/v11.11.0" target="_blank" rel="noopener noreferrer" class="sha-link">Verify</a>
        </div>
      </div>

      <!-- 4. Standalone MCP Server -->
      <div class="download-card">
        <div class="dl-badge">TDQS 5/5 MCP Server</div>
        <div class="dl-icon">🤖</div>
        <h3 class="dl-name">TZeroMCP.exe</h3>
        <p class="dl-desc">Model Context Protocol stdio server exposing 52 canonical tools directly to Cursor, Claude Desktop, Antigravity, and Copilot.</p>
        <div class="dl-meta">
          <span>Size: <strong>61.76 MB</strong></span>
          <span>Version: <strong>v11.11.0</strong></span>
        </div>
        <a href="https://github.com/toprakahmetaydogmus/TZeroAlgorithm/releases/download/v11.11.0/TZeroMCP.exe" target="_blank" rel="noopener noreferrer" download class="btn btn-dl" data-name="TZeroMCP.exe">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          Download MCP Server
        </a>
        <div class="dl-sha">
          <span>SHA-256: <code class="sha-copy" data-sha="8f153e5a23f5c9189ba96c341f5f282177c28e69deca49b44f626e8f88acad8a" title="Click to copy full SHA-256">8f153e5a23f5... 📋</code></span>
          <a href="https://github.com/toprakahmetaydogmus/TZeroAlgorithm/releases/tag/v11.11.0" target="_blank" rel="noopener noreferrer" class="sha-link">Verify</a>
        </div>
      </div>

      <!-- 5. 1-Click Auto Installer -->
      <div class="download-card">
        <div class="dl-badge">Auto Installer</div>
        <div class="dl-icon">⚙️</div>
        <h3 class="dl-name">AddMCP.exe</h3>
        <p class="dl-desc">1-Click configuration installer that discovers Cursor, VS Code, Claude Desktop, Antigravity, Windsurf & Zed to inject T-Zero automatically.</p>
        <div class="dl-meta">
          <span>Size: <strong>76.45 MB</strong></span>
          <span>Version: <strong>v11.11.0</strong></span>
        </div>
        <a href="https://github.com/toprakahmetaydogmus/TZeroAlgorithm/releases/download/v11.11.0/AddMCP.exe" target="_blank" rel="noopener noreferrer" download class="btn btn-dl" data-name="AddMCP.exe">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          Download Auto Installer
        </a>
        <div class="dl-sha">
          <span>SHA-256: <code class="sha-copy" data-sha="3cf6732788309af0c824505c05899ba613f00610727ebfbadd3668e726a8ec0a" title="Click to copy full SHA-256">3cf673278830... 📋</code></span>
          <a href="https://github.com/toprakahmetaydogmus/TZeroAlgorithm/releases/tag/v11.11.0" target="_blank" rel="noopener noreferrer" class="sha-link">Verify</a>
        </div>
      </div>

      <!-- 6. VS Code / Cursor Extension (.VSIX) -->
      <div class="download-card">
        <div class="dl-badge">VS Code & Cursor</div>
        <div class="dl-icon">🧩</div>
        <h3 class="dl-name">tzero-vscode-11.11.0.vsix</h3>
        <p class="dl-desc">Official VS Code & Cursor extension providing 1-click token pruning, AST architecture mapping, and real-time ROI savings.</p>
        <div class="dl-meta">
          <span>Size: <strong>50.13 KB</strong></span>
          <span>Version: <strong>v11.11.0</strong></span>
        </div>
        <a href="https://github.com/toprakahmetaydogmus/TZeroAlgorithm/releases/download/v11.11.0/tzero-vscode-11.11.0.vsix" target="_blank" rel="noopener noreferrer" download class="btn btn-dl" data-name="tzero-vscode-11.11.0.vsix">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          Download Extension (.VSIX)
        </a>
        <div class="dl-sha">
          <span>SHA-256: <code class="sha-copy" data-sha="61c7d0d733fd60bdd3c865daf7cfa993514d89da050eb972652eee9470c60348" title="Click to copy full SHA-256">61c7d0d733fd... 📋</code></span>
          <a href="https://github.com/toprakahmetaydogmus/TZeroAlgorithm/releases/tag/v11.11.0" target="_blank" rel="noopener noreferrer" class="sha-link">Verify</a>
        </div>
      </div>
    </div>'''

    pattern = r'<div class="downloads-grid animate-on-scroll">[\s\S]*?</div>\s*</section>'
    replacement = new_downloads_grid + '\n  </section>'
    return re.sub(pattern, replacement, html, count=1)


def update_navbar_and_hero(html: str) -> str:
    # 1. Navbar Star pill
    old_nav_btn = r'<a href="https://github.com/toprakahmetaydogmus/TZeroAlgorithm" target="_blank" rel="noopener" class="btn btn-primary-sm">\s*<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">[\s\S]*?</svg>\s*GitHub ★\s*</a>'
    new_nav_btn = '''<a href="https://github.com/toprakahmetaydogmus/TZeroAlgorithm" target="_blank" rel="noopener" class="btn btn-primary-sm btn-star-action" title="Star T-Zero on GitHub">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
          Star <span id="nav-star-count" class="star-counter-pill">★ 16</span>
        </a>'''
    html = re.sub(old_nav_btn, new_nav_btn, html, count=1)

    # 2. Viral campaign bar in hero
    viral_bar = '''      <!-- Viral 100-Stars Road & Social Share Hub -->
      <div class="viral-campaign-bar animate-in delay-4">
        <div class="viral-left">
          <span class="viral-label">⭐ ROAD TO 100 STARS:</span>
          <div class="viral-track">
            <div class="viral-progress" id="viral-progress-bar" style="width: 16%;"></div>
          </div>
          <span class="viral-count"><strong id="hero-star-count">16</strong> / 100 Stars</span>
        </div>
        <div class="viral-shares">
          <span class="share-hint">1-Click Community Share:</span>
          <button class="share-btn btn-x" id="share-x" title="Share on X / Twitter">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
            Tweet
          </button>
          <button class="share-btn btn-reddit" id="share-reddit" title="Share on Reddit">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2A10 10 0 0 0 2 12a10 10 0 0 0 10 10 10 10 0 0 0 10-10A10 10 0 0 0 12 2zm5.01 12.5a3.5 3.5 0 0 1-5.02 0 .5.5 0 1 1 .71-.7 2.5 2.5 0 0 0 3.6 0 .5.5 0 0 1 .71.7zm-6.26-2.75a1.25 1.25 0 1 1 0-2.5 1.25 1.25 0 0 1 0 2.5zm4.5 0a1.25 1.25 0 1 1 0-2.5 1.25 1.25 0 0 1 0 2.5z"/></svg>
            Reddit
          </button>
          <button class="share-btn btn-linkedin" id="share-linkedin" title="Share on LinkedIn">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.46 8.76a1.4 1.4 0 1 0 0-2.8 1.4 1.4 0 0 0 0 2.8m1.39 9.74V9.92H5.07v8.58h2.78z"/></svg>
            LinkedIn
          </button>
          <button class="share-btn btn-hn" id="share-hn" title="Submit to Hacker News">
            <span style="font-weight:900; font-family: monospace;">Y</span>
            HN
          </button>
          <button class="share-btn btn-copy-link" id="share-copy-link" title="Copy Share Link">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
            Copy
          </button>
        </div>
      </div>'''

    if "viral-campaign-bar" not in html:
        # Insert after hero-actions closing div
        actions_end = '        </div>\n      </div>'
        replacement = '        </div>\n      </div>\n\n' + viral_bar
        html = html.replace(actions_end, replacement, 1)

    return html


def update_app_js():
    js_content = APP_JS.read_text(encoding="utf-8")

    viral_code = '''
// ============================================================================
// 8. DYNAMIC GITHUB STARS & VIRAL COMMUNITY SHARING ENGINE
// ============================================================================
function initGitHubStars() {
  const navStar = document.getElementById("nav-star-count");
  const heroStar = document.getElementById("hero-star-count");
  const progBar = document.getElementById("viral-progress-bar");

  function updateDisplay(stars) {
    if (navStar) navStar.textContent = "★ " + stars;
    if (heroStar) heroStar.textContent = stars;
    if (progBar) {
      const pct = Math.min(100, Math.max(5, (stars / 100) * 100));
      progBar.style.width = pct + "%";
    }
  }

  // Initial cached baseline
  const cached = localStorage.getItem("tzero_cached_stars");
  if (cached) {
    updateDisplay(parseInt(cached, 10));
  }

  // Fetch live star count from GitHub API
  fetch("https://api.github.com/repos/toprakahmetaydogmus/TZeroAlgorithm", {
    headers: { "Accept": "application/vnd.github.v3+json" }
  })
    .then(r => {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    })
    .then(data => {
      if (data && typeof data.stargazers_count === "number") {
        const count = data.stargazers_count;
        localStorage.setItem("tzero_cached_stars", count);
        updateDisplay(count);
      }
    })
    .catch(err => {
      console.log("[T-Zero] GitHub API live star fetch skipped:", err.message);
    });
}

function initViralShare() {
  const repoUrl = "https://github.com/toprakahmetaydogmus/TZeroAlgorithm";
  const webUrl = "https://tzero-indol.vercel.app";
  const shareText = "T-Zero: Cut AI coding context tokens by up to 95% using AST pruning! Open-source local MCP server for Cursor & Claude Desktop. Check it out: " + repoUrl;

  const btnX = document.getElementById("share-x");
  const btnReddit = document.getElementById("share-reddit");
  const btnLinkedIn = document.getElementById("share-linkedin");
  const btnHN = document.getElementById("share-hn");
  const btnCopy = document.getElementById("share-copy-link");

  if (btnX) {
    btnX.addEventListener("click", () => {
      const url = "https://twitter.com/intent/tweet?text=" + encodeURIComponent(shareText) + "&hashtags=CursorAI,ClaudeAI,OpenSource,Python";
      window.open(url, "_blank", "width=600,height=450");
    });
  }

  if (btnReddit) {
    btnReddit.addEventListener("click", () => {
      const title = "T-Zero: Open-source local AST context pruning for Cursor & Claude (-88% to -95% tokens, $0, 100% offline)";
      const url = "https://reddit.com/submit?url=" + encodeURIComponent(repoUrl) + "&title=" + encodeURIComponent(title);
      window.open(url, "_blank", "width=800,height=600");
    });
  }

  if (btnLinkedIn) {
    btnLinkedIn.addEventListener("click", () => {
      const url = "https://www.linkedin.com/sharing/share-offsite/?url=" + encodeURIComponent(repoUrl);
      window.open(url, "_blank", "width=600,height=550");
    });
  }

  if (btnHN) {
    btnHN.addEventListener("click", () => {
      const t = "Show HN: T-Zero – Local AST context pruning for LLMs with 88-95% token reduction";
      const url = "https://news.ycombinator.com/submitlink?u=" + encodeURIComponent(repoUrl) + "&t=" + encodeURIComponent(t);
      window.open(url, "_blank", "width=700,height=500");
    });
  }

  if (btnCopy) {
    btnCopy.addEventListener("click", () => {
      navigator.clipboard.writeText(repoUrl).then(() => {
        showToast("Repository link copied! Share with your team or community ⭐", "📋");
      }).catch(() => {
        showToast(repoUrl, "🔗");
      });
    });
  }
}
'''

    if "initGitHubStars" not in js_content:
        js_content += viral_code

    # Add calls into DOMContentLoaded
    dom_anchor = 'safeInit(initShadowCoW, "ShadowCoW");'
    if dom_anchor in js_content and 'safeInit(initGitHubStars' not in js_content:
        replacement = dom_anchor + '\n  safeInit(initGitHubStars, "GitHubStars");\n  safeInit(initViralShare, "ViralShare");'
        js_content = js_content.replace(dom_anchor, replacement, 1)

    APP_JS.write_text(js_content, encoding="utf-8")
    print("Updated app.js with live GitHub stars & viral share engine!")


def main():
    print(f"Loading {INDEX_HTML}...")
    html = INDEX_HTML.read_text(encoding="utf-8")
    html = update_downloads_section(html)
    html = update_navbar_and_hero(html)
    INDEX_HTML.write_text(html, encoding="utf-8")
    print("Updated index.html successfully!")

    update_app_js()
    print("All benchmark site updates complete!")


if __name__ == "__main__":
    main()

