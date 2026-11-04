# 🚀 Hacker News Launch: "Show HN" Guide

### Where to Submit:
- **URL:** [https://news.ycombinator.com/submit](https://news.ycombinator.com/submit)
- **Best Times to Submit (EST):** Tuesday or Wednesday at 8:00 AM - 10:00 AM EST (15:00 - 17:00 Türkiye Saati).

---

### Title:
`Show HN: T-Zero – Cut LLM prompt token costs by 94.6% with local AST pruning`

### URL Field:
`https://tzero-indol.vercel.app`

### Text (First Comment or Text submission):
```text
Hey HN,

I built T-Zero (https://github.com/toprakahmetaydogmus/TZeroAlgorithm), an open-source deterministic AST context compression engine and Model Context Protocol (MCP) server for Cursor, VS Code, Claude Code, Google Antigravity, and Windsurf.

The Problem:
When developers feed entire codebases into LLMs (using @codebase or file concatenation tools like Repomix), 80% to 95% of prompt tokens are wasted on repetitive internal function logic, loops, local math, and implementation boilerplate. On frontier models like Claude 3.5 Sonnet ($3/M tokens), this wastes thousands of dollars and causes severe "Lost in the Middle" attention degradation.

How T-Zero Solves It:
Instead of treating code as flat text, T-Zero parses source code into an Abstract Syntax Tree (AST). It slices out function bodies while preserving 100% of classes, exported signatures, parameter types, return annotations, and docstrings.
When working on a focus file, it delivers that target file at 100% full implementation, while surrounding 1st-degree dependencies are reduced to lightweight AST skeletons.

Key Highlights:
- Up to -94.6% token reduction (empirically measured with tiktoken cl100k_base).
- Pre-Flight Reality-Lock: Statically catches hallucinated method calls and phantom imports before code execution.
- Shannon Entropy Secret Scrubber: Detects and masks API keys locally ($H >= 4.75$).
- 100% TDQS 5.0/5.0 Grade A Anchor Certified across all registered MCP tools.
- $0.00 Cost Guarantee: 100% local Python AST, zero external paid vector DB or embedding APIs.
- Official VS Code & Cursor Extension (.vsix) included.

Live Portal & Benchmarks: https://tzero-indol.vercel.app
GitHub Repository: https://github.com/toprakahmetaydogmus/TZeroAlgorithm
Interactive Space: https://huggingface.co/spaces/toprakke4/tzero-token-reducer

Feedback, bug reports, and architectural ideas are warmly welcome!
```
