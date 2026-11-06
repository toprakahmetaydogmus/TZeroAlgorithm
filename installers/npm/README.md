# tzero-mcp

> **Deterministic AST Context Compressor, 95% Token Reducer & 20-Tool MCP Server for Cursor, Claude Desktop, Antigravity & Copilot.**

[![npm version](https://img.shields.io/npm/v/tzero-mcp.svg)](https://www.npmjs.com/package/tzero-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub Stars](https://img.shields.io/github/stars/toprakahmetaydogmus/TZeroAlgorithm?style=social)](https://github.com/toprakahmetaydogmus/TZeroAlgorithm)

---

### ⭐ Built by a 15-Year-Old Solo Developer
Hi! I'm **Toprak Ahmet Aydoğmuş**, a 15-year-old developer from Siber Akademi. I created T-Zero to solve LLM token limits and eliminate AI coding hallucinations using deterministic AST analysis. If you find this package useful, **please star our repository on GitHub!**

👉 **[https://github.com/toprakahmetaydogmus/TZeroAlgorithm](https://github.com/toprakahmetaydogmus/TZeroAlgorithm)**

---

## ⚡ Instant MCP Execution (No Install Needed)

Run directly via `npx` in your `claude_desktop_config.json` or Cursor MCP settings:

```json
{
  "mcpServers": {
    "tzero": {
      "command": "npx",
      "args": ["-y", "tzero-mcp"]
    }
  }
}
```

## 🚀 CLI Installation

```bash
# Global installation
npm install -g tzero-mcp

# Compress a directory into an AST Skeleton tree (95% token savings)
tzero --tree . --out tree.txt

# Launch MCP Server
tzero-mcp
```

## 🛠 Features

- **95% Token Reduction:** Compresses source code into AST skeletons with intact function signatures and docstrings.
- **Zero-Leak Security Guard:** Scans for hardcoded secrets before LLM context ingestion.
- **Reality-Lock Pre-Flight:** Prevents hallucinations by verifying imports and function calls against AST.
- **20 Native Tools:** Memory store, AST pagerank, call chain tracer, diff context, and more.

## 📄 License

MIT © [Toprak Ahmet Aydoğmuş](https://github.com/toprakahmetaydogmus)

