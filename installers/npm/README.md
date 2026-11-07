# tzero-mcp

> **Deterministic AST Context Compressor, 95% Token Reducer & 20-Tool MCP Server for Cursor, Claude Desktop, Antigravity & Copilot.**

[![npm version](https://img.shields.io/npm/v/tzero-mcp.svg?color=cb3837&logo=npm)](https://www.npmjs.com/package/tzero-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Socket Badge](https://socket.dev/api/badge/npm/package/tzero-mcp)](https://socket.dev/npm/package/tzero-mcp)
[![GitHub Stars](https://img.shields.io/github/stars/toprakahmetaydogmus/TZeroAlgorithm?style=social)](https://github.com/toprakahmetaydogmus/TZeroAlgorithm)

---

### ⭐ Built by a 15-Year-Old Solo Developer (Please Star Our Repo!)

Hi! I'm **Toprak Ahmet Aydoğmuş**, a 15-year-old solo open-source developer from **Siber Akademi**. I created T-Zero from scratch to eliminate token limits, reduce prompt costs by up to 95%, and stop AI coding hallucinations using deterministic Abstract Syntax Tree (AST) analysis.

If this package helps your engineering team or AI workflows:  
⭐ **Please give our repository a STAR on GitHub:**  
👉 **[https://github.com/toprakahmetaydogmus/TZeroAlgorithm](https://github.com/toprakahmetaydogmus/TZeroAlgorithm)**  
*Every single star means the world to a young open-source creator! 🚀*

---

## ⚡ Instant MCP Execution (Zero Install Needed)

Run directly via `npx` in your `claude_desktop_config.json`, Cursor MCP settings, or Windsurf / Antigravity config:

```json
{
  "mcpServers": {
    "tzero": {
      "command": "npx",
      "args": ["-y", "tzero-mcp@latest"]
    }
  }
}
```

## 🚀 CLI Installation & Usage

```bash
# Global installation via npm
npm install -g tzero-mcp

# Compress any project directory into an AST Skeleton tree (95% token savings)
tzero --tree . --out tree.txt

# Launch interactive Model Context Protocol (MCP) Server
tzero-mcp

# 1-Click connect to Cursor, Claude Desktop, Antigravity & VS Code
tzero-add-mcp
```

## 🛠 Key Capabilities

- **95% Deterministic Token Reduction:** Compresses source code into AST skeletons preserving function signatures, type annotations, and docstrings while pruning redundant logic bodies.
- **100% Zero-Leak Security Guard:** Deep Shannon Entropy ($H \ge 4.75$) scanner for API keys and secrets before LLM context ingestion.
- **Reality-Lock Pre-Flight:** Catches hallucinations before code execution by validating imports and call hierarchies against real AST nodes.
- **20 Native Developer Tools:** AST PageRank, call-chain tracer, BM25 semantic hybrid search, change blast radius analyzer, and system doctor.
- **100% Private, Local & Free:** Pure offline operation — $0 API cost, zero cloud lock-in.

## 📄 License

MIT © [Toprak Ahmet Aydoğmuş](https://github.com/toprakahmetaydogmus)
