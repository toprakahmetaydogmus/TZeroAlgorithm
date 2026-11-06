---
title: "I'm 15 and I Built an Open-Source Tool That Cuts AI Token Costs by 95% Using AST Compression"
published: true
tags: ai, python, opensource, webdev
cover_image: https://raw.githubusercontent.com/toprakahmetaydogmus/TZeroAlgorithm/main/assets/tzero_terminal_benchmark.svg
canonical_url: https://github.com/toprakahmetaydogmus/TZeroAlgorithm
---

# I'm 15 and I Built an Open-Source Tool That Cuts AI Token Costs by 95% Using AST Compression

Hi everyone! I’m **Toprak Ahmet Aydoğmuş**, a 15-year-old solo developer from Siber Akademi in Turkey.

Over the past six months, like millions of other developers, I fell in love with AI coding tools like **Cursor, Claude Code, Windsurf, and Copilot**. But as my projects grew from simple scripts to multi-thousand-line architectures, I hit a massive brick wall that every AI developer faces:

> **The Context Token Crisis:** When you dump an entire repository into Claude 3.5 Sonnet or GPT-4o, **80% to 95% of prompt tokens are completely wasted on routine function internals, local math, logging statements, and boilerplate.**

Not only does this burn through API credits at an alarming speed ($15–$50/day for active developers), but it also degrades reasoning quality — causing LLMs to "forget" earlier context and hallucinate phantom imports.

I decided to solve this problem deterministically. No expensive cloud embeddings, no paid API keys. **100% offline, pure Abstract Syntax Tree (AST) surgery.**

Today, I’m releasing **[T-Zero v10.6.0](https://github.com/toprakahmetaydogmus/TZeroAlgorithm)** as an open-source MCP Server & VS Code Extension.

---

## 💡 The Core Idea: What AI Actually Needs to See

When an AI assistant writes a new feature or debugs a function, it **rarely needs to see every line of existing implementations**. What it truly needs is:

1. **Type signatures and contracts** (`def process_order(user_id: int, items: list[Item]) -> Receipt:`)
2. **Class hierarchies and docstrings**
3. **Module export interfaces**
4. **Call graphs and dependencies**

Everything else inside existing functions — loops, local variables, helper math — is noise that clutters the attention window.

### The 4-Tier Compression Engine:
- **T-1 (File Map):** Token-optimized directory topology (~95% reduction).
- **T-2 (Symbol Tree):** Classes and callable definitions without bodies (~90% reduction).
- **T-3 (Interface Skeletons):** Full docstrings, type annotations, and method signatures with body statements replaced by `...` ellipsis (~85% reduction).
- **T-4 (Focus Implementation):** Surgical full source code for active target files while surrounding modules stay at T-3.

```python
# BEFORE (Raw Source - 148 tokens):
class DatabaseCluster:
    def connect(self, host: str, port: int = 5432) -> Connection:
        """Establish pool connection with retries."""
        logger.info(f"Connecting to {host}:{port}")
        pool = create_pool(min_size=5, max_size=20)
        conn = pool.acquire(timeout=30.0)
        self.health_check(conn)
        return conn

# AFTER T-ZERO AST PRUNING (T-3 - 28 tokens, -81.1% savings):
class DatabaseCluster:
    def connect(self, host: str, port: int = 5432) -> Connection:
        """Establish pool connection with retries."""
        ...
```

The LLM receives the exact contract it needs to write perfect code, while token usage drops by **up to 95%**.

---

## 🛡️ Pre-Flight Reality-Lock: Killing AI Hallucinations

Beyond token savings, we encountered another nightmare: **Hallucinations**. Models frequently invent functions or import libraries that don't exist in your environment.

T-Zero includes a **Static Pre-Flight Reality-Lock**:
Before AI-proposed code touches your workspace, T-Zero parses its AST and cross-references every imported module against:
1. Python standard library modules
2. Declared dependencies (`requirements.txt`, `pyproject.toml`)
3. Live AST symbols in your local workspace

If an AI assistant attempts to import a hallucinated module like `from helpers.utils import secret_magic_parser`, T-Zero intercepts it immediately, flags the exact line, and forces the model to self-heal.

---

## 🔐 1-Click Auto-Vault: Secret Security Guard

Developers frequently paste code containing API keys into AI prompts. 

T-Zero includes a built-in **Shannon Entropy scanner ($H \ge 4.75$)** detecting credentials across 13 major providers (OpenAI, Anthropic, AWS, Stripe, GitHub). 

With one command:
```bash
tzero --vault --migrate
```
It extracts detected secrets, appends them to `.env`, ensures `.env` is inside `.gitignore`, and surgically rewrites the Python source code to use `os.environ.get(...)`.

---

## 🚀 How to Try It in 30 Seconds

T-Zero is **100% free, MIT licensed, and runs entirely on your local machine**:

### 1. Official VS Code Marketplace
Search for **`siber-akademi`** in VS Code Extensions, or install via terminal:
```bash
code --install-extension siber-akademi.tzero-vscode
```

### 2. PyPI & Turnkey IDE MCP Init
```bash
pip install tzero-mcp --upgrade
tzero init
```
This automatically configures **Cursor, Claude Desktop, Windsurf, and Antigravity IDE** in under 1 second.

### 3. macOS & Linux (Homebrew)
```bash
brew tap toprakahmetaydogmus/tzero && brew install tzero
```

### 4. Interactive Live Web Studio (No Install)
Test the compression live on NVIDIA GPUs:
👉 **[Hugging Face Space](https://huggingface.co/spaces/toprakke4/tzero-token-reducer)** | **[Live Web Hub](https://tzero-indol.vercel.app)**

---

## 🌟 Support a 15-Year-Old Open Source Creator!

Building this project taught me more about compilers, AST analysis, and security than any textbook ever could. Seeing over **17,000+ PyPI downloads** and **320+ software teams** clone the repo has been the thrill of a lifetime.

If you believe in open-source tools that empower developers without paywalls or subscription traps, please consider **leaving a star (⭐) on our repository**:

👉 **[https://github.com/toprakahmetaydogmus/TZeroAlgorithm](https://github.com/toprakahmetaydogmus/TZeroAlgorithm)**

Thank you for your support, and happy coding! 🚀

