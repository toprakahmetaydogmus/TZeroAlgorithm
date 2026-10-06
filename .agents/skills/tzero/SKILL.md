---
name: tzero
description: >-
  Enterprise-Grade Codebase Context Architect, AST Signatures Analyzer, & Token Reducer.
  Activate when the user types "/tzero", asks to reduce tokens, scan codebase architecture,
  audit code smells, analyze change impact, enforce architectural boundaries, or optimize prompt context for LLMs.
---

# /tzero — Siber Akademi T-Zero Context Engine

Enterprise-Grade Codebase Context Architect, AST Signatures Analyzer, and Token Reducer.
Cuts LLM context ingestion overhead by up to 95% while preserving structural fidelity for AI agents.

Developer: Toprak Ahmet Aydoğmuş (Siber Akademi)
Repository: https://github.com/toprakahmetaydogmus/TZeroAlgorithm

## Slash Command Modes

When the user enters `/tzero [subcommand]` or asks for T-Zero assistance, dispatch to the matching capability:

| Subcommand | Description | Action / Tool |
|:---|:---|:---|
| `/tzero` or `/tzero tree` | Builds full multi-tier hierarchical context tree (T-1 to T-4) with ultra token pruning. | Call `get_project_context_tree` MCP tool |
| `/tzero audit` | Runs AST static code smell check and checks for 100% Zero-Leak security (hardcoded secrets). | Call `audit_codebase_quality` MCP tool |
| `/tzero arch` | Generates system architecture specification (`ARCHITECTURE.md`) with live Mermaid diagrams. | Call `generate_architecture_blueprint` MCP tool |
| `/tzero deps [file]` | Traces internal & external module import topology and dependency graphs. | Call `query_module_dependencies` MCP tool |
| `/tzero impact <symbol>` | Analyzes change impact and blast radius (0-100 score) before modifying a class/function. | Call `analyze_change_impact` MCP tool |
| `/tzero rules` | Generates AI agent instruction files (`.cursorrules`, `.cursor/rules/*.mdc`, `.clinerules`). | Call `export_agent_rules` MCP tool |
| `/tzero search <query>` | Performs 100% private local BM25 hybrid semantic code search without cloud embedding APIs. | Call `search_codebase_semantic` MCP tool |
| `/tzero savings` | Computes quantitative token reduction metrics and team financial ROI savings (USD/month). | Call `get_token_savings_metrics` MCP tool |
| `/tzero boundaries` | Enforces T-4 architectural boundaries defined in `tzero.rules.json` to prevent architectural erosion. | Call `enforce_architecture_boundaries` MCP tool |
| `/tzero repomap` | Generates ultra-compact AST symbol token map for chat context windows. | Call `generate_repo_map` MCP tool |
| `/tzero duplicity` | Scans workspace for duplicate or copy-pasted code blocks (6+ lines) across modules. | Call `find_code_duplicity` MCP tool |
| `/tzero doctor` | Inspects environment, Python runtime, and dependencies. | Run `python -m tzero_deps` or CLI `--doctor` |

## Execution Guidelines

1. **Prefer Native MCP Tools:** When the `tzero` MCP server is registered, invoke the corresponding MCP tool directly (`get_project_context_tree`, `audit_codebase_quality`, etc.).
2. **Fallback to CLI/Engine:** If MCP is temporarily unavailable, use the local CLI `tzero_v3.py` or `TZeroAlgorithm.exe` with matching flags (`--scan`, `--audit`, `--export-arch`, etc.).
3. **100% Zero-Leak Guarantee:** Never output, log, or commit sensitive API keys or user credentials.
4. **Summary & Presentation:** Format the output with clear GitHub-style Markdown, tables, and alerts (`> [!TIP]`, `> [!IMPORTANT]`).
