# tzero-mcp

> **Deterministic AST Context Compressor, 95% Token Reducer & 20-Tool MCP Server for Cursor, Claude Desktop, Antigravity & Copilot.**

[![npm version](https://img.shields.io/npm/v/tzero-mcp.svg?color=cb3837&logo=npm)](https://www.npmjs.com/package/tzero-mcp)
[![License: AGPL-3.0-only](https://img.shields.io/badge/License-AGPL--3.0--only-yellow.svg)](./LICENSE)
[![Socket Badge](https://socket.dev/api/badge/npm/package/tzero-mcp)](https://socket.dev/npm/package/tzero-mcp)
[![GitHub Stars](https://img.shields.io/github/stars/toprakahmetaydogmus/TZeroAlgorithm?style=social)](https://github.com/toprakahmetaydogmus/TZeroAlgorithm)

---

### Open-Source Engineering (Please Star Our Repo!)

Hi! I'm **Toprak Ahmet Aydoğmuş** from **Siber Akademi**. I created T-Zero from scratch to eliminate token limits, reduce prompt costs by up to 95%, and stop AI coding hallucinations using deterministic Abstract Syntax Tree (AST) analysis.

If this package helps your engineering team or AI workflows:  
⭐ **Please give our repository a STAR on GitHub:**  
👉 **[https://github.com/toprakahmetaydogmus/TZeroAlgorithm](https://github.com/toprakahmetaydogmus/TZeroAlgorithm)**  
*100% Free & Open-Source under AGPL-3.0-only. Thank you! 🚀*

---

## Security advisory

GitHub flags **`tzero-mcp@12.3.0`** in [GHSA-pm3r-rxg9-cj5j](https://github.com/advisories/GHSA-pm3r-rxg9-cj5j). If you installed or ran that version, follow the advisory's remediation guidance. GitHub lists no patched version.

This npm package uses a separate Python interpreter. It requires Python dependencies to be installed explicitly for that interpreter. See the [source repository](https://github.com/toprakahmetaydogmus/TZeroAlgorithm) for setup instructions and [network and system behavior](https://github.com/toprakahmetaydogmus/TZeroAlgorithm/blob/main/PRIVACY.md).

## Key Capabilities

- **95% Deterministic Token Reduction:** Compresses source code into AST skeletons preserving function signatures, type annotations, and docstrings while pruning redundant logic bodies.
- **Secret scanning:** Deep Shannon Entropy ($H \ge 4.75$) scanner for API keys and secrets before LLM context ingestion.
- **Reality-Lock Pre-Flight:** Catches hallucinations before code execution by validating imports and call hierarchies against real AST nodes.
- **20 Native Developer Tools:** AST PageRank, call-chain tracer, BM25 semantic hybrid search, change blast radius analyzer, and system doctor.
- **Local AST parsing and lexical search:** These operations run on the machine hosting T-Zero.

## License

AGPL-3.0-only © [Toprak Ahmet Aydoğmuş](https://github.com/toprakahmetaydogmus)
