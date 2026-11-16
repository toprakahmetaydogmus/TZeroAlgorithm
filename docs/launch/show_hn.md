# Show HN: T-Zero – Local AST context pruning for LLMs with 88-95% token reduction

**URL:** `https://github.com/toprakahmetaydogmus/TZeroAlgorithm`

**First Comment:**

Hi HN! I'm Toprak (Toprak Ahmet Aydoğmuş) from Siber Akademi. I've spent the past several months building **T-Zero**, an open-source tool and Model Context Protocol (MCP) server that deterministically prunes codebase context for coding models.

### The Problem
When developers feed a medium-to-large repository (50+ files) into Cursor, Claude Desktop, or local models, they usually encounter two pain points:
1. **Naive RAG / Vector search:** Misses cross-file caller/callee contracts, type hierarchies, and import dependencies because semantic chunks lack global topological awareness.
2. **Raw file dumps:** Consumes hundreds of thousands or millions of tokens on repetitive function implementation bodies, resulting in "lost-in-the-middle" attention degradation and expensive per-prompt fills.

### The Deterministic AST Pruning Approach
Instead of stripping files arbitrarily or relying on heuristic summaries, T-Zero parses source files directly into Abstract Syntax Trees (AST):
- Retains 100% of class hierarchies, method signatures, parameter types, return annotations, and docstrings.
- Replaces function execution bodies with concise AST stubs (`...`).
- Uses graph-theory PageRank over import topologies to rank architectural backbone modules when enforcing hard token budgets.

### Concrete Benchmark on 465-File Repository (~89,000 LOC):
- **Raw Codebase Context:** 10,910,525 tokens ($32.73 per prompt fill on standard cloud models)
- **T-Zero 4-Tier Hierarchical AST Tree:** 1,309,263 tokens (**-88.0% token reduction**)
- **Target File Skeleton (Tier-3):** **-94.6% token reduction**
- **AST Visitor Latency:** <400ms locally on standard CPU without GPU requirements
- **Test Coverage:** Comprehensive suite with 100% green test passes

### Security & Privacy (100% Zero-Leak):
- Computes in-memory Shannon entropy (H >= 4.75) alongside regex guards to identify and redact API keys, private certificates, and credentials before context is emitted.
- Operates 100% offline via local stdio MCP. Zero external network telemetry or third-party cloud calls.

### Installation & Integrations:
- **Windows (WinGet):** `winget install SiberAkademi.TZero`
- **macOS / Linux (Homebrew):** `brew install toprakahmetaydogmus/tap/tzero`
- **Python (PyPI):** `pip install tzero-mcp`
- **Node.js (npx):** `npx tzero-mcp`
- **VS Code Extension:** Marketplace / Open VSX verified publisher

The project is completely open source under MIT:
- Repository: https://github.com/toprakahmetaydogmus/TZeroAlgorithm
- Live Interactive Benchmark: https://tzero-indol.vercel.app

*Disclosure: I am the author and lead maintainer of T-Zero at Siber Akademi.*

I'd appreciate technical critique on our AST extraction heuristics, type bridging across languages, and MCP protocol integration!

