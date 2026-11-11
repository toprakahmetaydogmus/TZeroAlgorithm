# T-Zero Algorithm

[![PyPI](https://img.shields.io/pypi/v/tzero-mcp)](https://pypi.org/project/tzero-mcp/)
[![npm](https://img.shields.io/npm/v/tzero-mcp)](https://www.npmjs.com/package/tzero-mcp)
[![VS Code Marketplace](https://img.shields.io/visual-studio-marketplace/v/siber-akademi.tzero-vscode)](https://marketplace.visualstudio.com/items?itemName=siber-akademi.tzero-vscode)
[![M8ven Publisher](https://m8ven.ai/badge/mcp/toprakahmetaydogmus/tzeroalgorithm?variant=verified)](https://m8ven.ai/mcp/toprakahmetaydogmus/tzeroalgorithm?s=readme)
[![Glama](https://img.shields.io/badge/MCP-Glama-635bff)](https://glama.ai/mcp/servers/toprakahmetaydogmus/TZeroAlgorithm)
[![Smithery](https://smithery.ai/badge/@toprakahmetaydogmus/TZeroAlgorithm)](https://smithery.ai/server/@toprakahmetaydogmus/TZeroAlgorithm)
[![CI](https://github.com/toprakahmetaydogmus/TZeroAlgorithm/actions/workflows/ci.yml/badge.svg)](https://github.com/toprakahmetaydogmus/TZeroAlgorithm/actions/workflows/ci.yml)
[![TDQS](https://img.shields.io/badge/TDQS-5.0%2F5.0-15803d)](README.md#tdqs-certification)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776ab)](pyproject.toml)
[![MIT](https://img.shields.io/badge/License-MIT-slategray)](LICENSE)

[English](README.md) · [Türkçe](README.tr.md) · [日本語](README.ja.md) · [简体中文](README.zh.md) · [Privacy Policy](PRIVACY.md)

T-Zero is an AST context compressor and MCP server for coding assistants. It extracts signatures and dependencies, scans for secrets, and builds context packs from a local workspace.

## Quickstart

Install the CLI with `python -m pip install -U tzero-mcp` or `npm install -g tzero-mcp`.
Run `tzero init` to configure an editor or `npx -y tzero-mcp@latest` to launch the MCP server.
The branch uses package version **10.9.0**.

## v11 commands

- `tzero --doctor --deep` — Run local subsystem checks.
- `tzero --lsp` — Start the stdio language server.
- `tzero hook / --hook-install` — Evaluate tool lifecycle hooks and install editor configuration.
- `--federation export/import/verify/impact` — Exchange repository manifests and analyze cross-repository impact.
- `--scip-import` — Import a SCIP index.
- `--snapshot / --cache-aligned` — Build AST snapshots and produce context packs with stable prefixes.
- `--contracts-sarif` — Export contract changes as SARIF.
- `--agent-kernel` — Validate local execution plans against workspace constraints.

<p align="center">
  <b><a href="#tdqs-certification">TDQS 5.0</a></b> &bull; 
  <b><a href="#why-t-zero">Why T-Zero</a></b> &bull; 
  <b><a href="#task-completion-benchmark">Task Benchmark</a></b> &bull; 
  <b><a href="#universal-1-click-ide-setup">Universal IDE Setup</a></b> &bull; 
  <b><a href="#the-21-canonical-mcp-tools">21 MCP Tools</a></b> &bull;
  <b><a href="#pre-flight-reality-lock">Reality-Lock</a></b> &bull; 
  <b><a href="#language-support-breakdown">Language Support</a></b> &bull; 
  <b><a href="#huggingface-space">Hugging Face Space</a></b> &bull; 
  <b><a href="README.tr.md">Türkçe Rehber</a></b>
</p>

---

<a id="why-t-zero"></a>
## How T-Zero reduces context

**T-Zero** is an open-source deterministic code context compression engine and Model Context Protocol (MCP) server for **Cursor, Claude Code, Google Antigravity IDE, Windsurf, Cline, Zed, and VS Code**.

The context builder keeps the target code and extracts signatures from related files. The benchmark below compares that output with a full-source baseline.

### 🥊 Context Architecture Comparison Matrix

| Dimension | Raw Prompt Ingestion | Vector DB / Embedding RAG | Repomix (Raw Concat) | Aider (Repo-Map) | T-Zero Deterministic AST Engine |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Token Reduction** | 0% (Massive waste) | 40-70% (Fragmented) | 0% (Dumps raw files) | 70-85% (Symbol list only) | **Up to 95.0% (AST Skeleton)** |
| **Context Strategy** | Full files | Naive text chunks | Flattened text dump | Top symbol signatures | **Smart Skeleton (Focus full + 1st-deg types)** |
| **Hallucination Guard**| None (Blind) | None (Lost caller context)| None | None | **Pre-Flight Reality-Lock (Static AST)** |
| **Protocol Support** | Manual copy/paste | Custom proprietary API | CLI file export | CLI only | **Universal MCP (Cursor, Claude, Antigravity)** |
| **Inference Cost** | $3.00 - $15.00+ / turn | Cloud Vector DB fees | $3.00 - $15.00+ / turn | Model dependent | **$0.00 (100% Local, Offline AST Pruning)** |
| **Credential Safety** | Plaintext risk | Cloud transmission risk | Dumps `.env` files | None | **Shannon-Entropy Key Scrubber (H ≥ 4.75)** |

---

<a id="task-completion-benchmark"></a>
## 🧪 Empirical Task-Completion & BPE Tokenizer Benchmark

> **Key Architectural Question:** *Does signature-only context allow an AI coding agent to complete real-world tasks correctly, or does it cause hallucination?*

### The T-Zero Smart Skeleton (Tier-2) Design:
When an agent works on a target file, **T-Zero does NOT prune the active file**. Instead:
1. **Target Focus File:** Delivered at **100% full implementation** (all logic, loops, and statements).
2. **Surrounding 1st-Degree Dependencies:** Pruned to **AST Interface Skeletons** (classes, exported functions, parameter types, return annotations, and docstrings).

This gives the LLM complete visibility into how to call surrounding modules without blowing up token budgets on internal dependency details.

### Empirical Evaluation (Measured with official `tiktoken` BPE Tokenizer: `cl100k_base`):

```text
==============================================================================
  T-ZERO TASK-COMPLETION & BPE TOKENIZER BENCHMARK REPORT (v9.9.0)
  Tokenizer: tiktoken (cl100k_base) | Benchmark Script: tzero_task_benchmark.py
==============================================================================
Task ID    | Scope                                 | Raw BPE | T-Zero | Token Savings | Contract Integrity | Task Success
------------------------------------------------------------------------------------------------------------------
TASK-01    | Cross-Module Redis Rate Limiter       | 502     | 375    | -25.3%        | 100.0%             | PASS (0 Halluc)
TASK-02    | Crypto Vault Key Rotation             | 322     | 239    | -25.8%        | 100.0%             | PASS (0 Halluc)
TASK-03    | AST Slicer & Blast Radius Evaluator   | 332     | 283    | -14.8%        | 100.0%             | PASS (0 Halluc)
------------------------------------------------------------------------------------------------------------------
FULL REPO  | Enterprise Repository (51,000 LOC)    | 1,168k  | 64.2k  | -94.5%        | 100.0%             | PASS (0 Regress)
==============================================================================
OVERALL TASK SUCCESS RATE: 100.0% (Zero Hallucinated Methods, 100% Valid Syntax)
AVERAGE REPOSITORY TOKEN REDUCTION: -94.5% (BPE Exact Tokens)
==============================================================================
```

*To reproduce these numbers locally:*
```bash
python tzero_task_benchmark.py
```

---

<a id="language-support-breakdown"></a>
## 🌐 Language Support Breakdown: AST vs. Heuristic Extraction

We believe in radical engineering transparency:

| Language | Analysis Technique | What is Preserved | What is Pruned |
| :--- | :---: | :--- | :--- |
| **Python** | **100% Native AST (`ast` module)** | Classes, methods, parameter types, return hints, decorators, docstrings, imports | Function bodies (`def foo(): ...`) |
| **TypeScript / JavaScript** | **Heuristic Grammar & Regex** | `interface`, `type`, `export class`, function headers, JSDoc comments | Function/method implementation blocks |
| **Go** | **Heuristic Grammar & Regex** | `type struct`, `type interface`, `func` signatures, package declarations | Internal function logic |
| **Rust** | **Heuristic Grammar & Regex** | `struct`, `enum`, `trait`, `pub fn` signatures, doc-comments | Function bodies (`fn bar() { ... }`) |
| **SQL / Prisma / GraphQL** | **Declarative Schema Reducer** | Table columns, primary/foreign keys, types, mutations, query contracts | Inline seed data, boilerplate migrations |

---

<a id="universal-1-click-ide-setup"></a>
## 🚀 Universal 1-Click IDE Setup (All Editors)

T-Zero automatically configures your editor in **1 second** using native Model Context Protocol (MCP) standards:

```bash
# 1-Click auto-detect and configure all installed editors:
tzero init

# Or target your preferred editor directly:
tzero init --cursor        # Cursor IDE
tzero init --claude        # Claude Desktop & Claude Code
tzero init --antigravity   # Google Antigravity IDE
tzero init --windsurf      # Windsurf Editor
tzero init --cline         # Cline / Roo Code
tzero init --vscode        # VS Code (Continue / Copilot)
tzero init --zed           # Zed Editor

# Install official VS Code / Cursor Extension (.vsix):
code --install-extension dist/tzero-vscode-10.9.0.vsix
```

### Manual Configuration Snippets (Any MCP Client)

<details>
<summary><strong>Cursor (`.cursor/mcp.json` or Settings &rarr; Features &rarr; MCP)</strong></summary>

```json
{
  "mcpServers": {
    "tzero": {
      "command": "python",
      "args": ["-m", "tzero_mcp"]
    }
  }
}
```
*Or zero-install via uvx:*
```json
{
  "mcpServers": {
    "tzero": {
      "command": "uvx",
      "args": ["tzero-mcp"]
    }
  }
}
```
</details>

<details>
<summary><strong>Claude Desktop (`claude_desktop_config.json`)</strong></summary>

*Path: `%APPDATA%\\Claude\\claude_desktop_config.json` (Windows) or `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)*
```json
{
  "mcpServers": {
    "tzero": {
      "command": "python",
      "args": ["-m", "tzero_mcp"]
    }
  }
}
```
</details>

---

<a id="the-21-canonical-mcp-tools"></a>
## 🛠️ The 21 Canonical MCP Tools

The default server exposes 21 tools. Use `search_tools` to discover specialized tools or set `TZERO_MCP_TOOL_MODE=all` to expose all 58 at startup.

| Tool Name | Scope | Purpose |
| :--- | :---: | :--- |
| `build_project_context` | Context | Builds hierarchical multi-tier context tree (up to ~95% token reduction). |
| `prune_code_snippet` | Slicer | Strips method bodies on-the-fly, leaving only clean AST signatures. |
| `manage_architecture_rules` | Governance | Defines and manages active architectural boundary rules in `tzero.rules.json`. |
| `enforce_architecture_rules` | Governance | Validates architectural layer rules and prevents cyclic or illegal cross-layer imports. |
| `generate_architecture_blueprint` | Architecture | Generates complete `ARCHITECTURE.md` with auto-generated Mermaid component diagrams. |
| `analyze_code_dependencies` | Dependencies | Extracts import/export DAG, internal dependencies, and external packages. |
| `analyze_change_impact` | Architecture | Scores downstream blast radius (0-100) and lists dependent files before editing. |
| `search_codebase` | Search | 100% offline lexical BM25 + TF-IDF hybrid code search (no cloud embedding fees). |
| `audit_code_quality` | Linter | Runs static AST code smell checks and Shannon entropy secret scans. |
| `verify_security_guard` | Security | Scans workspace for high-entropy tokens, private keys, and API credentials. |
| `estimate_token_cost` | FinOps | Computes exact token savings and financial ROI across Claude, GPT-4o, Gemini, and DeepSeek. |
| `query_memory_store` | Memory | Searches semantic vector-quantized virtual memory triplets (`<|tzero:mem:...|>`). |
| `manage_memory_store` | Memory | Consolidates, prunes, and manages persistent semantic memory triplets. |
| `orchestrate_agent_swarm` | Multi-Agent | Coordinates multi-agent PBFT consensus and task routing across workspace subagents. |
| `build_ast_snapshot` | Snapshot | Pre-computes sub-8ms cached AST snapshot bundle for instantaneous agent ingestion. |
| `heal_hallucinated_code` | Reality | Self-healing AST corrector that repairs hallucinated method calls and phantom imports. |
| `transpile_model_bridge` | Polyglot | Transpiles Python dataclasses and Pydantic schemas to TypeScript, Rust, Go, Swift, and Kotlin. |
| `diagnose_and_heal_system` | Doctor | Self-healing operating system doctor fixing environment, zombie processes, and ASTs. |
| `generate_architectural_passport` | Architecture | Synthesizes high-density AST structural passport for files and modules. |
| `search_tools` | Discovery | Finds tools by keyword or category. |
| `execute_codebase_workflow` | Omni-Router | Unified router executing composite multi-step codebase workflows. |

---

<a id="turbo-overdrive-burst-accelerator"></a>
## ⚡🔥 Turbo Overdrive Burst Accelerator ("Kamçılama Modu")

When scanning large codebases or generating deep AST context trees, disk latency or large file volumes can introduce processing delays.
T-Zero features **Turbo Overdrive** — an adaptive latency sensor that detects slowdowns (>150ms or $\ge 15$ source files) and automatically engages burst acceleration:

- 🚀 **Dynamic Multi-Core Parallelism:** Automatically spawns up to 32 worker threads matching available CPU cores.
- ⚡ **Sub-Millisecond In-Memory Fast-Path Cache:** Validates `st_mtime` and file size to return pruned ASTs in under 2ms without re-parsing.
- 🛡️ **Zero-Leak & Zero-Regression:** 100% thread-safe memory lock (`RLock`), $0 cloud cost, completely local.

```bash
# View live Turbo Overdrive status & cache telemetry:
tzero turbo

# Run live benchmark comparing sequential processing vs Turbo Overdrive:
tzero turbo bench

# Clear accelerator in-memory cache:
tzero turbo clear
```

---

<a id="autonomous-dynamic-subagent-swarm"></a>
## 🐝 Autonomous Dynamic Subagent Decomposer & Swarm

When given a complex mission (e.g. *"Audit secrets, verify architectural boundaries, optimize database queries, and generate unit tests"*), T-Zero automatically:
1. **Decomposes Composite Goals:** Identifies independent subtasks across security, architecture, performance, testing, and custom domains.
2. **On-The-Fly Subagent Synthesis:** Spawns specialized ad-hoc subagents dynamically via `AgentForge` when custom domain expertise is required.
3. **Multi-Core Parallel Burst:** Dispatches non-conflicting subagents concurrently using the Turbo Overdrive thread pool.
4. **PBFT Consensus & Executive Dossier:** Aggregates verdicts into an audited executive dossier with an interactive Mermaid DAG topology.

```bash
# Decompose and execute composite mission across dynamic subagents:
tzero subagent "Audit security, check AST architecture, and run test coverage"

# Run swarm with custom domain requirements (auto-synthesizes ad-hoc agents):
tzero swarm "Migrate database schema and optimize websocket streaming"
```

---

<a id="tdqs-certification"></a>
## 🏆 100% TDQS 5.0 / 5.0 Anchor Certification Standard

T-Zero is officially certified at **TDQS 5.0 / 5.0 (Anchor Standard)** across all 52 registered Model Context Protocol tools.

### What is TDQS (Tool Documentation Quality Score)?
Frontier LLMs (Claude 3.5 Sonnet, GPT-4o, Gemini 1.5/2.0 Pro) rely exclusively on tool docstrings and parameter schemas to decide:
1. *Which* tool to call among dozens of registered capabilities.
2. *How* to invoke it without argument hallucinations.
3. *Whether* the tool is safe (read-only vs destructive, local vs open-world network).

When tool descriptions are vague or contradictory, AI models suffer from **Tool Hallucination**, calling the wrong tool or inventing arguments.

### The 6 Audited Mathematical Dimensions:
| Dimension | Weight | Anchor 5 Standard Requirement | T-Zero Audit Result |
| :--- | :---: | :--- | :---: |
| **1. Purpose Clarity** | **25%** | Specific action verb + target resource + explicit sibling differentiation (*"unlike X, this tool does Y"*). Zero tautological phrasing. | **100% PASS** |
| **2. Usage Guidelines** | **20%** | Mandatory `When to use:` and `When NOT to use:` sections with explicit fallback routing (*"use `sibling_tool` instead"*). | **100% PASS** |
| **3. Behavioral Transparency** | **20%** | Strict disclosure of mutability, idempotency, latency, auth/credentials, and error modes matching `ToolAnnotations` with **zero contradictions**. | **100% PASS** |
| **4. Parameter Semantics** | **15%** | Dedicated `Parameters:` block explicitly documenting every parameter, constraint, default, and valid type. | **100% PASS** |
| **5. Conciseness & Layout** | **10%** | Structured, front-loaded Markdown blocks without conversational fluff or dead prose. | **100% PASS** |
| **6. Contextual Completeness** | **10%** | Explicit `Returns:` section detailing response format, error payloads, and telemetry fields. | **100% PASS** |

### Automated Verification Pipeline:
Every single tool is continuously audited in CI via:
```bash
# Automated TDQS 5.0/5.0 unit test:
python -m unittest tests/test_tdqs_anchor5.py -v

# Full 52-tool audit runner:
python scripts/comprehensive_tdqs_audit.py
# Output: ✅ PERFECT 5/5! No issues detected across all 52 tools!
```

---

<a id="huggingface-space"></a>
## 🤗 Hugging Face Spaces Live Web Application

Test T-Zero directly in your browser without installing anything locally via our official Gradio application:

<p align="center">
  <a href="https://huggingface.co/spaces/toprakke4/tzero-token-reducer">
    <img src="https://img.shields.io/badge/%F0%9F%A4%97%20Open%20in%20Hugging%20Face-Spaces-ffd21e?style=for-the-badge&logo=huggingface&logoColor=black" alt="Open in Hugging Face Spaces" height="40">
  </a>
</p>

- **Live URL:** [https://huggingface.co/spaces/toprakke4/tzero-token-reducer](https://huggingface.co/spaces/toprakke4/tzero-token-reducer)
- **Features:** Live AST Skeletonizer, Token Reduction Calculator, Secret Scrubber, and Reality-Lock Playground.

### Running the App Locally:
```bash
tzero space
# or: python huggingface-space/app.py (opens at http://localhost:7860)
```

---

<a id="pre-flight-reality-lock"></a>
## ⚖️ Pre-Flight Reality-Lock (Static AST Verification)

AI coding assistants frequently hallucinate non-existent methods (e.g., `math.quantum_fast_inverse_sqrt`) or phantom library imports.

T-Zero's `HallucinationGuard` statically validates candidate method calls and imports against the **verified project AST symbol table** and Python standard library:

```bash
# Test code snippet:
tzero --hallucination-check "import math; x = math.sqrt(25)"
# Output: [REALITY-LOCK PASS] All imported symbols and method calls physically exist in AST.

tzero --hallucination-check "import math; x = math.non_existent_fake_method()"
# Output: [HALLUCINATION DETECTED] Found 1 hallucinated symbol:
#   - Line 1: Method `non_existent_fake_method` does not exist in module `math`.
```

*(Note: Pre-Flight Reality-Lock performs static AST analysis. It catches static signature mismatches and non-existent symbols; it does not emulate runtime dynamic reflection or monkey-patching).*

---

<a id="security-architecture"></a>
## 🔒 Security Architecture: Deterministic Secret Scanner

### OS-Native Credential Storage:
T-Zero uses platform-native secret vaults:
- **Windows:** Windows Credential Manager
- **macOS:** macOS Keychain
- **Linux:** Secret Service API / libsecret

### High-Entropy Secret Scanner ($H \ge 4.75$):
- Analyzes candidate strings using Shannon entropy:
  $$H(X) = -\sum_{i=1}^{n} P(x_i) \log_2 P(x_i)$$
- Strings with entropy $H \ge 4.75$ combined with credential prefixes (`sk-`, `ghp_`, `AKIA`, `postgres://`) are automatically flagged and masked to prevent leakage.
- **Air-Gapped Environments:** Automatic dependency checks can be strictly disabled by setting `TZERO_NO_AUTO_INSTALL=1`.
- **Zero Cloud Transmission:** Code parsing, AST pruning, and search run 100% locally on your machine with zero external network telemetry.

---

<a id="reproducible-benchmarks"></a>
## 📊 Multi-Model Financial ROI Benchmarks

Empirical measurements conducted across real software repositories comparing raw prompt context injection against T-Zero AST-pruned context:

| Frontier Model | Input Rate / 1M | Raw Context / Query | T-Zero Tier-2 Context | Token Savings | Monthly Savings (10 Devs) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Anthropic Claude 3.5 Sonnet** | `$3.00` | `$1.786` | **`$0.098`** | **`-94.5%`** | **`+$9,283.11 / mo`** |
| **OpenAI GPT-4o** | `$2.50` | `$1.488` | **`$0.082`** | **`-94.5%`** | **`+$7,735.93 / mo`** |
| **Google Gemini 1.5 Pro** | `$1.25` | `$0.744` | **`$0.041`** | **`-94.5%`** | **`+$3,867.96 / mo`** |
| **DeepSeek V3 / R1** | `$0.27` | `$0.161` | **`$0.009`** | **`-94.5%`** | **`+$835.48 / mo`** |

*Calculation based on a 10-developer team executing 25 agent prompt turns/day (5,500 queries/month).*

---

---

<a id="global-ecosystem"></a>
## 🌐 Global Ecosystem & Multilingual Architecture

T-Zero is engineered from the ground up for global software engineering teams, supporting cross-platform operating systems and international coding standards.

### Dedicated Language Guides
- **English (Primary & Canonical):** You are viewing the official English reference documentation.
- **Turkish Translation:** For native Turkish documentation and setup guides, see [README.tr.md](README.tr.md).

### 30-Second Turnkey Quickstart
```bash
# 1. Install via PyPI:
pip install tzero-mcp

# 2. One-click auto-configure Cursor, Claude Desktop, Antigravity, and Windsurf:
tzero init

# 3. Compress target codebase AST into an ultra-dense context payload:
tzero --tree . --out context.txt

# 4. Launch local Zero-GPU Web Studio:
tzero space
```
<a id="tzero-pc-fixer"></a>
## 🩺 T-Zero PC-Fixer & Codebase Doctor: The 12,600+ Line Autonomous Self-Healing Monolith

<div align="center">

<a href="https://github.com/toprakahmetaydogmus/tzero-pc-fixer">
  <img src="assets/tzero_pc_fixer_banner.svg" alt="T-Zero PC-Fixer & Codebase Doctor Banner" width="100%" style="max-width: 960px; border-radius: 12px; box-shadow: 0 16px 48px rgba(0,0,0,0.8);">
</a>

</div>

**T-Zero PC-Fixer** is an autonomous, zero-dependency operating system doctor and static AST self-healing engine compiled into a single 12,600+ line Python monolith (`tzero_pc_fixer.py`). It diagnoses and surgically cures broken developer workstations, memory leaks, orphaned zombie processes, contaminated environments, and static codebase defects with $0.00 cloud cost.

### 🚀 1-Click Zero-Dependency Installers

**Windows (PowerShell 5.1+ / 7+):**
```powershell
irm https://raw.githubusercontent.com/toprakahmetaydogmus/tzero-pc-fixer/main/install.ps1 | iex
```

**macOS / Linux (Bash):**
```bash
curl -fsSL https://raw.githubusercontent.com/toprakahmetaydogmus/tzero-pc-fixer/main/install.sh | bash
```

### 🧰 Autonomous Healing Capabilities:
- **🖥️ Hardware & Process Surgeon:** Hunts runaway compiler/Node.js zombie processes, clears swap memory, verifies disk partition health, and unblocks port collisions (e.g. 8000, 3000, 5000, 8080).
- **🐍 Python & Virtual Environment Doctor:** Detects broken symlinks, repairing contaminated `sys.path`, corrupted wheel caches, and Microsoft Store Python PATH hijacking.
- **🛡️ CWE-78 & CWE-327 Static AST Remediator:** Rewrites dangerous `subprocess.Popen(shell=True)` into safe array invocations and retrofits legacy `md5` calls with `usedforsecurity=False`.
- **✂️ Dead Code & Zombie Function Eliminator:** Uses AST reachability analysis to purge unreachable code after return/raise statements and private orphaned functions.
- **⚡ Async/IO Event Loop Modernizer:** Detects blocking `time.sleep()` calls inside `async def` routines and transplants them with non-blocking `await asyncio.sleep()`.

---

## ⭐ Support Open-Source Innovation!

Hi! I'm **Toprak Ahmet Aydoğmuş** from Siber Akademi. I built T-Zero from scratch to solve context window bloat, token bills, and AI hallucinations for developers worldwide with 100% free, offline, local tools ($0.00 cloud cost).

If T-Zero helped you cut prompt tokens or saved your daily coding workflow, please consider giving us a star! Every star helps open-source developers worldwide. 🚀

<div align="center">

**T-Zero is 100% Free, Open-Source & Offline Forever.**  
*Built with passion by Toprak Ahmet Aydoğmuş (Siber Akademi) for developers worldwide.*

</div>

---

## 📈 Star History

Join the revolution in context engineering and deterministic token pruning!

<div align="center">

<a href="https://star-history.com/#toprakahmetaydogmus/TZeroAlgorithm&Date">
  <img src="https://api.star-history.com/svg?repos=toprakahmetaydogmus/TZeroAlgorithm&type=Date" alt="T-Zero Star History Chart" width="100%" style="max-width: 800px; border-radius: 10px;">
</a>

</div>

---

## 📜 License & Siberian Academy

- **Author & Architect:** Toprak Ahmet Aydoğmuş (Lead Software Engineer & Architect, Siber Akademi)
- **LinkedIn:** [Toprak Ahmet Aydoğmuş](https://linkedin.com/in/toprak-ahmet-aydo%C4%9Fmu%C5%9F-60462534b/)
- **Bio & Hub:** [hopp.bio/siberegitim](https://hopp.bio/siberegitim)
- **License:** [MIT Open Source License](LICENSE)
