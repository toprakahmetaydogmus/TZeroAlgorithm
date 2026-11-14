# -*- coding: utf-8 -*-
"""
T-ZERO $0.00 BUDGET VIRAL MARKETING & COMMUNITY GROWTH AUTOMATION ENGINE
------------------------------------------------------------------------
Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
License: MIT | Version: 11.11.0

Strictly $0.00 budget: Zero paid ads, zero paid APIs, zero cloud tokens.
Pure organic developer-to-developer growth engine engineered to drive 100+ GitHub stars.
Generates tailored, high-converting launch copy for Reddit, Hacker News, Product Hunt,
Twitter/X, LinkedIn, Dev.to, Turkish Tech Hubs, and Awesome-Lists.
"""

import sys
import os
import json
import urllib.request
from pathlib import Path
from typing import Dict, Any, List

REPO_URL = "https://github.com/toprakahmetaydogmus/TZeroAlgorithm"
WEB_URL = "https://tzero-indol.vercel.app"
AUTHOR = "Toprak Ahmet Aydoğmuş"
ORGANIZATION = "Siber Akademi"
VERSION = "v11.11.0"
PYPI_PKG = "tzero-mcp"
NPM_PKG = "tzero-mcp"

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent


def get_live_github_stars() -> int:
    """Fetch current GitHub stargazers count."""
    try:
        url = "https://api.github.com/repos/toprakahmetaydogmus/TZeroAlgorithm"
        req = urllib.request.Request(url, headers={"User-Agent": "T-Zero-Marketing-Engine"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return int(data.get("stargazers_count", 16))
    except Exception:
        return 16


def render_progress_bar(current: int, target: int = 100, length: int = 30) -> str:
    """Renders visual ASCII progress bar."""
    pct = min(1.0, current / target)
    filled = int(pct * length)
    bar = "█" * filled + "░" * (length - filled)
    return f"[{bar}] {current}/{target} Stars ({pct*100:.1f}%)"


def generate_reddit_posts() -> Dict[str, Dict[str, str]]:
    """Generates copy-paste ready Reddit launch posts."""
    return {
        "r/Cursor": {
            "title": "I built an open-source MCP server that cuts Cursor context tokens by 85-95% using AST pruning (100% local, no API keys, $0)",
            "body": f"""Hey Cursor developers!

Like many of you, I kept hitting Cursor Composer context degradation and rate limits on medium-to-large repositories (100+ files). When you ingest an entire project, 90% of the token payload consists of function execution bodies that the LLM does not need to understand your architecture.

To solve this, I spent the last several months engineering **T-Zero** ({VERSION}) — an open-source Model Context Protocol (MCP) server that deterministically prunes multi-language codebases down to their exact AST interfaces, type annotations, and docstrings before feeding them to Cursor.

### 📊 Real Benchmark on 481-File Repository:
- **Raw Codebase Context:** 10,998,573 tokens (causes instant truncation / extreme lag)
- **T-Zero 4-Tier AST Tree:** 1,319,828 tokens (**-88.0% token reduction**)
- **Focus File Skeleton (T-3):** **-94.6% token reduction**
- **AST Visitor Speed:** <400ms (100% offline via local Python AST parser)
- **Unit & E2E Tests:** 537 automated tests passing with 0 errors

### 🤖 New in {VERSION} — AI Godfather Auto-Corrector:
- Catches AI coding hallucinations before code is committed.
- Statically validates imported symbols against your project's AST and auto-heals misspelled or imaginary functions.
- Injects missing stdlib modules and typing imports automatically.

### ⚡ Add to Cursor in 30 Seconds:
Add this to your Cursor MCP settings (`~/.cursor/mcp.json`):

```json
{{
  "mcpServers": {{
    "tzero": {{
      "command": "python",
      "args": ["-m", "tzero.tzero_mcp"]
    }}
  }}
}}
```
*(Or install via pip: `pip install {PYPI_PKG}` or npm: `npx {NPM_PKG}`)*

### 🔒 100% Zero-Leak Security & Privacy:
- Zero external LLM calls or cloud telemetry.
- Built-in Shannon Entropy scanner (H >= 4.75) detects and redacts hardcoded API keys and credentials locally.

I'm 15 years old and building this as a solo open-source engineer at {ORGANIZATION}. Everything is 100% free under MIT.

If this saves your Cursor context budget, **I'd genuinely appreciate a star on GitHub ⭐** — we are on the road to our first 100 stars!

👉 **GitHub:** {REPO_URL}  
👉 **Live Benchmark:** {WEB_URL}  
👉 **PyPI:** https://pypi.org/project/{PYPI_PKG}/  
"""
        },
        "r/ClaudeAI": {
            "title": "Stop hitting Claude Desktop & Claude Code 200K token limits: Open-source local AST context pruning (-88% to -95%)",
            "body": f"""If you use Claude Desktop or Claude Code with complex multi-module codebases, you know how fast the 200K token window fills up. Once context fills up, Claude begins suffering from "lost-in-the-middle" attention degradation or hits expensive per-prompt costs.

**T-Zero** ({VERSION}) is a 100% local, offline MCP server that parses your codebase into an AST and strips implementation bodies while keeping 100% of the type signatures, classes, docstrings, and imports across 12+ programming languages.

### 💡 Why AST Beats Naive File Dumping:
When Claude writes a new endpoint or fixes a bug, it doesn't need 200 lines of SQL query builder boilerplate from your database driver. It just needs:
1. Class inheritance structures
2. Typed function signatures & return types
3. Docstrings & interface contracts

Claude gets 100% of the architectural context needed to produce zero-defect code, while consuming **up to 95% fewer tokens**.

### ⚡ 1-Click Setup for Claude Desktop:
Add to your `claude_desktop_config.json`:
```json
{{
  "mcpServers": {{
    "tzero": {{
      "command": "python",
      "args": ["-m", "tzero.tzero_mcp"]
    }}
  }}
}}
```

- **Cost:** $0.00 (Zero paid APIs, runs 100% offline)
- **Security:** In-memory Shannon entropy scanner redacts API keys
- **License:** MIT Open Source

Check it out and drop a star if you find it useful! ⭐  
👉 **GitHub:** {REPO_URL}  
👉 **Web Playground:** {WEB_URL}
"""
        },
        "r/LocalLLaMA": {
            "title": "T-Zero: 100% offline, zero-cloud AST codebase context pruner for local models (Ollama, LM Studio, Qwen 2.5 Coder, DeepSeek)",
            "body": f"""When running local coding models (Qwen 2.5 Coder 7B/14B/32B, DeepSeek-Coder, Llama 3.1) on consumer GPUs, VRAM context window limits (8K–32K) make it impossible to feed full multi-file codebases into prompts.

**T-Zero** ({VERSION}) is a zero-cloud AST token reducer that fits whole multi-tier codebases into compact local context windows:
1. **Deterministic AST pruning:** Collapses function bodies to `...` while retaining full signatures and type annotations.
2. **PageRank Module Centrality:** Graph-theory ranking automatically prioritizes architectural backbone files when strict token caps are enforced.
3. **Shannon Entropy Zero-Leak:** Ensures no private keys or tokens leak into model prompts.
4. **Local BM25 Hybrid Search:** Instant semantic symbol lookup with 0 cloud embeddings.

- **Zero Cloud Calls:** 100% air-gapped stdio server.
- **Install:** `pip install {PYPI_PKG}`
- **GitHub:** {REPO_URL} (Stars welcome! ⭐)
"""
        },
        "r/Turkey": {
            "title": f"15 yaşındayım, Cursor ve Claude için geliştirdiğim açık kaynaklı context motoru {VERSION} ile yayında! 🇹🇷",
            "body": f"""Merhaba Türk yazılımcı topluluğu!

Ben Toprak Ahmet Aydoğmuş, 15 yaşındayım ve {ORGANIZATION} bünyesinde bağımsız açık kaynaklı yazılımlar geliştiriyorum.

Yapay zeka kodlama araçlarıyla (Cursor, Claude Desktop, Antigravity, Windsurf) büyük projelerde çalışırken en büyük darboğaz **token sınırları ve yüksek context maliyetleri**. Tüm dosyaları yapay zekaya yüklediğinizde binlerce satır gereksiz gövde kodu yapay zekanın dikkatini dağıtıyor ve pencereyi tüketiyor.

Bu problemi çözmek için geliştirdiğim **T-Zero (Token Zero)** projesini {VERSION} sürümüyle tamamen ücretsiz ve açık kaynak olarak yayınladım!

### 🌟 Temel Yetenekleri:
- Python, TypeScript, Go, Rust, Java vb. dillerde kodları AST (Abstract Syntax Tree) ile inceleyip fonksiyon gövdelerini buduyor ve token tüketimini **%85-%95 oranında azaltıyor**.
- Model Context Protocol (MCP) standardında çalıştığı için Cursor ve Claude Desktop'a tek tıkla ekleniyor.
- %100 yerel ve çevrimdışı çalışıyor; hiçbir harici ücretli API veya sunucuya bağlanmıyor ($0 maliyet).
- Yeni {VERSION} sürümünde eklenen **AI Godfather Süpervizörü** sayesinde yapay zekanın uydurduğu (hallucinated) sahte fonksiyon çağrılarını ve eksik importları otomatik düzeltiyor.
- 537 otomatik testten %100 başarıyla geçmektedir.

Projeyi GitHub'da yıldızlayarak (Star ⭐) ilk 100 yıldız hedefimize ulaşmamıza destek olursanız çok sevinirim!

🔗 **GitHub:** {REPO_URL}  
🔗 **Web Benchmark:** {WEB_URL}  
🔗 **PyPI:** https://pypi.org/project/{PYPI_PKG}/  
"""
        }
    }


def generate_show_hn() -> Dict[str, str]:
    """Generates Hacker News Show HN submission."""
    return {
        "title": f"Show HN: T-Zero – Local AST context pruning for LLMs with 88-95% token reduction",
        "url": REPO_URL,
        "first_comment": f"""Hi HN! I'm Toprak ({AUTHOR}), a 15-year-old software engineer from Turkey. I built T-Zero to solve a fundamental efficiency problem in AI-assisted software engineering: prompt context bloat.

### The Problem:
When developers feed large repositories into Cursor, Claude Desktop, or Claude Code, they either:
1. Rely on vector embeddings (RAG), which frequently misses cross-file caller/callee contracts and exact type signatures, or
2. Dump entire source files into the context window, burning hundreds of thousands of tokens, triggering rate limits, and degrading model attention ("lost in the middle").

### The AST Pruning Approach:
T-Zero parses multi-language source trees into Abstract Syntax Trees (AST) and deterministically extracts interface contracts (class hierarchies, method signatures, argument types, return types, docstrings, imports) while pruning execution bodies.

On our benchmark repository of 481 files (~86,000 lines of code):
- Raw Codebase: 10,998,573 tokens ($32.99 per single Claude 3.5 Sonnet context fill)
- T-Zero 4-Tier AST Tree: 1,319,828 tokens (-88.0% reduction)
- Focus Skeleton (T-3): -94.6% reduction
- Processing Latency: <400ms locally

### Security & Privacy:
- **100% Zero-Leak:** Calculates in-memory Shannon entropy (H >= 4.75) alongside regex patterns to detect and redact API keys, JWTs, and private keys locally before any context is emitted.
- **Zero Cloud Telemetry:** Operates 100% offline via local stdio MCP protocol.

The codebase is open source under MIT: {REPO_URL}
Web Playground: {WEB_URL}

I would love to hear thoughts, critique, and feedback on our AST pruning heuristics and MCP server architecture!
"""
    }


def generate_twitter_thread() -> List[str]:
    """Generates 7-tweet viral X/Twitter thread."""
    return [
        f"""1/7 🚨 We ran a 481-file codebase through Claude 3.5 Sonnet:

🔴 Raw codebase: 10.9M tokens ($32.99 / prompt fill)
🟢 With T-Zero AST pruning: 1.3M tokens (-88% reduction)

Meet T-Zero {VERSION}: an open-source local MCP server that eliminates context window bloat for Cursor, Claude & local LLMs.

🧵 A thread on how it works: 👇""",
        """2/7 💡 The Problem with Raw Code Context:

When your AI coding assistant writes an API endpoint or fixes a bug, it doesn't need the 150-line implementation body of your database connection pool.

It only needs the class structure, method signatures, parameter types, and docstrings.

T-Zero extracts that exact skeleton in <400ms.""",
        """3/7 🌐 True Polyglot Support:

🐍 Python (native ast parser)
🟨 TypeScript & JavaScript
🐹 Go
🦀 Rust
☕ Java & Kotlin
🔷 C# & C++
🍎 Swift & Ruby

All parsed deterministically on your local CPU with 0 cloud dependencies.""",
        """4/7 🔒 100% Zero-Leak Security Guarantee:

Accidentally leaking API keys into LLM prompts is an enterprise nightmare.

T-Zero includes an in-memory Shannon Entropy scanner (H >= 4.75) that detects high-entropy secrets and redacts them *before* any text leaves your computer.

100% private, 100% offline.""",
        f"""5/7 🤖 New in {VERSION}: AI Godfather Hallucination Healer:

T-Zero now statically inspects AI-generated code against your workspace AST.

If the AI invents a nonexistent method or misspells an import, T-Zero catches it and auto-rewrites it to the real local symbol with 0 human intervention.""",
        f"""6/7 ⚡ 30-Second Setup:

Option A (pip):
$ pip install {PYPI_PKG}

Option B (npx zero-install):
$ npx {NPM_PKG}

Option C (Standalone .exe):
Download precompiled Windows 64-bit binaries from our GitHub Releases!""",
        f"""7/7 🌟 We are on a mission to reach our first 100 stars on GitHub!

Built by Toprak Ahmet Aydoğmuş (15-year-old solo engineer at Siber Akademi). 100% free under MIT.

If you care about AI efficiency and open source tooling, please drop a star ⭐:

👉 {REPO_URL}
👉 {WEB_URL}

RTs appreciated! 🔁 #CursorAI #ClaudeAI #Python #OpenSource"""
    ]


def generate_product_hunt() -> Dict[str, str]:
    """Generates Product Hunt launch kit."""
    return {
        "name": "T-Zero Context Architect",
        "tagline": "Cut AI coding context tokens by up to 95% using AST pruning",
        "topics": "Developer Tools, Artificial Intelligence, Open Source, Productivity, Python",
        "description": "T-Zero is a local Model Context Protocol (MCP) server for Cursor, Claude Desktop, Antigravity IDE, and Windsurf that deterministically prunes codebase bodies to typed AST skeletons, reducing LLM token consumption by 85–95% with 100% Zero-Leak security.",
        "maker_comment": f"""Hey Product Hunt community! 👋

I'm Toprak ({AUTHOR}), 15 years old, and I've spent the past few months building **T-Zero** at {ORGANIZATION}.

### The Problem We Solved:
AI coding assistants like Cursor and Claude are transformative, but as soon as you open a repository with 50+ files, you run into:
1. Massive context window consumption (millions of tokens)
2. Cost spikes ($20–$50 per developer daily)
3. Model degradation ("lost in the middle" hallucinations)

### The Solution:
Instead of dumping raw source code, T-Zero parses your project using Abstract Syntax Trees (AST). It removes function implementation bodies while retaining 100% of the class hierarchies, signatures, types, and docstrings.

The result? **Up to 95% token savings** while providing the LLM with pristine architectural context.

### Highlights:
- ⚡ 1-Click setup for Cursor, Claude, Antigravity & Windsurf
- 🔒 100% Zero-Leak: Local Shannon entropy scanner stops credential leaks
- 🤖 AI Godfather Supervisor: Auto-corrects hallucinated method names
- 💸 100% Free & Open Source under MIT

I'd love your feedback, reviews, and feature ideas! Check out the repo and give us a star if you find it valuable:
{REPO_URL}
"""
    }


def generate_awesome_lists_prs() -> Dict[str, str]:
    """Generates Markdown entries ready to submit as PRs to curated awesome lists."""
    return {
        "awesome-mcp-servers": f"""### Add T-Zero Context Architect

- **Name:** [T-Zero Context Architect]({REPO_URL})
- **Description:** Deterministic AST codebase context compressor & MCP server reducing prompt tokens by 80–95% for Cursor, Claude, and local LLMs. Includes Zero-Leak credential protection and AI hallucination auto-corrector.
- **Category:** Code Intelligence / Developer Tools
- **License:** MIT
""",
        "awesome-cursorrules": f"""### Add T-Zero Context Engine for Cursor

- **Name:** [T-Zero for Cursor]({REPO_URL})
- **Description:** Dynamic AST context optimizer and boundary enforcement MCP server for Cursor Composer. Cuts context token bloat by up to 94.6% on large codebases.
"""
    }


def export_all_marketing_materials(output_dir: Path) -> None:
    """Exports all marketing copy to markdown files organized by platform."""
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Reddit
    reddit_path = output_dir / "REDDIT_POSTS.md"
    reddit_content = ["# 📢 Ready-To-Post Reddit Launch Materials\n"]
    for sub, post in generate_reddit_posts().items():
        reddit_content.append(f"## Subreddit: `{sub}`\n")
        reddit_content.append(f"**Title:**\n> {post['title']}\n")
        reddit_content.append("**Body:**\n```markdown\n" + post["body"] + "\n```\n---\n")
    reddit_path.write_text("\n".join(reddit_content), encoding="utf-8")

    # 2. Hacker News
    hn_path = output_dir / "HACKER_NEWS_SHOW_HN.md"
    hn_data = generate_show_hn()
    hn_content = f"""# 📢 Hacker News Show HN Launch

**Submission Title:**
> {hn_data['title']}

**Target URL:**
`{hn_data['url']}`

**First Comment (by Author):**
```markdown
{hn_data['first_comment']}
```
"""
    hn_path.write_text(hn_content, encoding="utf-8")

    # 3. Twitter / X Thread
    x_path = output_dir / "TWITTER_THREAD.md"
    x_tweets = generate_twitter_thread()
    x_content = ["# 📢 Twitter / X 7-Tweet Viral Thread\n"]
    for i, tweet in enumerate(x_tweets, 1):
        x_content.append(f"### Tweet {i}:\n```text\n{tweet}\n```\n")
    x_path.write_text("\n".join(x_content), encoding="utf-8")

    # 4. Product Hunt
    ph_path = output_dir / "PRODUCT_HUNT_LAUNCH.md"
    ph_data = generate_product_hunt()
    ph_content = f"""# 📢 Product Hunt Launch Kit

**Product Name:** {ph_data['name']}
**Tagline:** {ph_data['tagline']}
**Topics:** {ph_data['topics']}

**Description:**
{ph_data['description']}

**First Maker Comment:**
```markdown
{ph_data['maker_comment']}
```
"""
    ph_path.write_text(ph_content, encoding="utf-8")

    # 5. Awesome Lists PRs
    awesome_path = output_dir / "AWESOME_LISTS_PRS.md"
    awesome_data = generate_awesome_lists_prs()
    awesome_content = ["# 📢 Curated Awesome-Lists PR Submissions\n"]
    for list_name, snippet in awesome_data.items():
        awesome_content.append(f"## Repository: `{list_name}`\n```markdown\n{snippet}\n```\n")
    awesome_path.write_text("\n".join(awesome_content), encoding="utf-8")

    print(f"✔ Exported all marketing materials to: {output_dir}")


def main():
    stars = get_live_github_stars()
    print("=" * 70)
    print("⚡ T-ZERO $0.00 BUDGET VIRAL MARKETING & GROWTH AUTOMATION ENGINE")
    print(f"🎯 Milestone Progress: {render_progress_bar(stars, 100)}")
    print(f"📦 Active Release    : {VERSION} (PyPI: {PYPI_PKG} | npm: {NPM_PKG})")
    print(f"🌐 Web Benchmark     : {WEB_URL}")
    print(f"⭐ Repository        : {REPO_URL}")
    print("=" * 70)

    export_dir = WORKSPACE_ROOT / "docs" / "marketing_pack"
    export_all_marketing_materials(export_dir)

    print("\n🚀 All campaign materials are 100% copy-paste ready in 'docs/marketing_pack/'!")


if __name__ == "__main__":
    main()
