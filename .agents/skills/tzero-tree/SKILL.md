---
name: tzero-tree
description: >-
  Generate multi-tier hierarchical AST context tree with up to 95% token reduction for AI context ingestion.
  Activate when the user types "/tzero-tree" or asks to build a code tree.
---

# /tzero-tree — AST Hierarchical Context Tree Generator

Generate a multi-tier pruned AST context tree to provide AI agents with full architectural understanding at up to 95% lower token cost.

## Modes & Tiers
- **Tier 1 (T-1):** High-level architectural map & entry points.
- **Tier 2 (T-2):** Public API & class/function signatures with types.
- **Tier 3 (T-3):** Full signatures, method contracts, and docstrings.
- **Tier 4 (T-4):** Full AST graph with import dependencies.

## Execution
Call the `get_project_context_tree` MCP tool with the target path (default: current workspace) and desired tier (default: `T-2`).
