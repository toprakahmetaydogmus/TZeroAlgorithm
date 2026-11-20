# T-Zero Context Architect (v11.15.5)

### 🚀 Server Showcase: T-Zero Context Architect (v11.15.5)

**Category:** Code Intelligence & Developer Tools  
**License:** MIT (100% Free & Open Source)  
**Repository:** <https://github.com/toprakahmetaydogmus/TZeroAlgorithm>  
**Interactive Benchmark:** <https://tzero-indol.vercel.app>  

#### 📋 What It Does:
T-Zero is a high-performance Model Context Protocol (MCP) server that compresses entire codebases into compact, typed AST interfaces. It cuts context token consumption by **85% to 95%** before sending prompt payloads to Claude Desktop, Cursor, Windsurf, or local LLMs.

#### 🛠 Exposed MCP Tools:
1. `get_project_context_tree` — Generates a 4-tier hierarchical AST context tree of the repository.
2. `get_smart_skeleton_context` — Focus-aware dynamic skeletonizer delivering target implementation + surrounding 1st-degree AST interface skeletons.
3. `prune_code_snippet` — In-memory AST signature compressor for arbitrary code snippets.
4. `verify_hallucination_guard` — Verifies AI-generated imports and function signatures against the workspace AST symbol table.
5. `audit_codebase_quality` — Static AST code smell audit and local secret scanner for likely hardcoded credentials.
6. `estimate_token_cost` — Real-time token and financial cost estimation across OpenAI, Anthropic, Gemini, and DeepSeek.

#### ⚙ Quick Configuration:

**Claude Desktop (`claude_desktop_config.json`):**
```json
{
  "mcpServers": {
    "tzero": {
      "command": "python",
      "args": ["-m", "tzero.tzero_mcp"]
    }
  }
}
```

**Cursor (`~/.cursor/mcp.json`):**
```json
{
  "mcpServers": {
    "tzero": {
      "command": "tzero-mcp",
      "args": ["--stdio"]
    }
  }
}
```

**Air-Gapped / Precompiled Binary (Windows x64):**
```bash
winget install SiberAkademi.TZero
```

*Local mode uses no telemetry or cloud tokens.*

