# T-Zero v11.0.0 Master Sequential Roadmap (Phases 1–4)

> **Execution Strategy:** Sequential delivery across 4 independent subsystem plans. Each phase produces green tests, Zero-Leak verification, and runnable software before starting the next phase.

**Goal:** Resolve all verified runtime bugs and packaging/distribution gaps (Phase 1), upgrade the VS Code extension and Developer Dashboard to live AST telemetry (Phase 2), modernize the core compression/caching/tokenization engine (Phase 3), and ship 2026 ecosystem capabilities (`tzero hook`, `tzero lsp`, Streamable HTTP MCP, Rust/WASM bridge, SCIP/LSIF + real benchmarks, and `tzero federation`) (Phase 4).

## Global Constraints
- **100% Free & Offline Core:** Zero mandatory paid APIs or cloud telemetry in core CLI/MCP/AST workflows.
- **100% Zero-Leak Certified:** `python tests/audit_secrets.py` must return `0` findings after every phase.
- **Zero Regressions:** Full `python -m unittest discover -s tests -p "test_*.py"` (plus Node extension/npm tests) must stay green after every task.
- **Backward Compatibility:** Preserve existing CLI flags, canonical/legacy MCP tool behavior (and keep `tests/test_mcp.py` tool count assertions updated deliberately when tools change).
- **Private Files Respected:** Never commit or expose gitignored files (`tzero_gateway.py`, `enterprise_onprem/`, `.env*`, `.tzero/`).

---

## Sequential Phase Breakdown

### Phase 1: Core Stabilization, Runtime Bugfixes & Packaging Sync
- **Plan:** [`docs/superpowers/plans/2026-11-10-tzero-phase1-stabilization-packaging.md`](2026-11-10-tzero-phase1-stabilization-packaging.md)
- **Scope:**
  1. Fix verified runtime bugs in `tzero_mcp.py` (`heal_hallucinated_code`, `transpile_model_bridge`, `execute_codebase_workflow` memory kwargs), `tzero_tui.py` (`gather_workspace_metrics` `reduce_code` call + real security check + menu/dashboard wiring), `tzero_v3.py` (`--vault --migrate` directory iteration + `--export-repomap -` stdout support), and `tzero_polyglot.py` (Java `{Ellipsis}` f-string bug).
  2. Fix `pyproject.toml` missing 10 `py-modules`, console scripts (`tzero-tui`, `pc-fixer-mcp`), unused/missing dependency declarations, and build single-source version sync (`scripts/sync_release_metadata.py`).
  3. Synchronize `installers/npm/src/` with root `10.9.0+` modules and verify `node --test`.
  4. Repair `action.yml` (use `tzero` CLI, emit real `$GITHUB_OUTPUT` metrics, wire inputs), `.dockerignore`, `Dockerfile` / `Dockerfile.glama`, `scripts/publish_vscode.ps1`, and clean up stale/duplicated packages (`tzero/jarvis/`, `vscode-extension/`).
  5. Note local-only `enterprise_onprem/Dockerfile` fixes cleanly without committing gitignored paths.

### Phase 2: VS Code / Cursor Extension & Live Developer Dashboard
- **Plan File (to be authored at Phase 2 start):** `docs/superpowers/plans/2026-11-10-tzero-phase2-vscode-dashboard.md`
- **Scope:**
  1. Upgrade `extensions/vscode/` to honor `tzero.executablePath` and `tzero.autoInitOnOpen`, replace hardcoded `94.9% Saved` status bar and regex CodeLens with live workspace AST metrics via CLI `--json`, upgrade `tzero.copySymbolContract` to extract full AST contracts via `tzero explain` / `prune`, expose `10.9.0` commands (`golden`, `budget`, `contracts`, `debt`, `mutate`, `bridge`, `merge-heal`), and add an Activity Bar Webview Sidebar Panel.
  2. Upgrade `tzero_dashboard.py` so `/api/stats` returns live workspace metrics instead of hardcoded `10.0.0` / `94.9%`, and bind all 8 backend API endpoints (`/api/debt/analyze`, `/api/budget/optimize`, `/api/golden/verify`, `/api/contracts/compare`, `/api/mutation/test`, `/api/bridge/reverse`, `/api/merge/heal`, `/api/blackboard`) into interactive UI panels.

### Phase 3: Core AST, Tokenization, KV-Cache Alignment & Incremental Indexing
- **Plan File (to be authored at Phase 3 start):** `docs/superpowers/plans/2026-11-10-tzero-phase3-ast-cache-engine.md`
- **Scope:**
  1. Replace `len(text) // 4` in `count_tokens_precise` and `TokenBudgetPacker` with real `tiktoken` BPE counting (`o200k_base` / `cl100k_base`) + deterministic fallback.
  2. Implement KV-Cache / Prompt-Caching aligned context ordering (`--cache-aligned` mode in `generate_offline_context` and `TokenBudgetPacker`, placing stable T-4 rules & static AST contracts in deterministic prefix order and dynamic focus/diff metadata at the suffix).
  3. Unify `PolyglotSignatureExtractor` (`tzero_v3.py`) and `PolyglotTokenReducer` (`tzero_polyglot.py`), fix `light` vs `ultra` tier divergence, add string/comment-aware brace tracking + Python `ast` multi-line signature preservation, and add optional `tree-sitter` + cAST AST-boundary chunking with zero-dep fallback.
  4. Upgrade `tzero_snapshot.py` & `run_watch_mode` to multi-language SQLite + `git diff` incremental indexing (and `max_files` PageRank scaling in `tzero_packer.py`).

### Phase 4: 2026 Ecosystem, MCP HTTP/Hooks/LSP, Rust Bridge & Federation
- **Plan File (to be authored at Phase 4 start):** `docs/superpowers/plans/2026-11-10-tzero-phase4-ecosystem-frontier.md`
- **Scope:**
  1. **MCP 2026 Modernization (`tzero_mcp.py` & `server.json`):** Add `--http` Streamable HTTP transport (`uvicorn`/FastMCP ASGI), `ctx.report_progress` notifications, `structuredContent` / `outputSchema`, dynamic URI template resources (`tzero://file/{path}/skeleton`), and progressive `search_tools` meta-discovery.
  2. **Deterministic Agent Hooks (`tzero_hooks.py` / `tzero hook`):** `PreToolUse` / `PostToolUse` hook runner for Claude Code, Gemini CLI, and Cursor (auto-prune giant reads + deterministic `deny` on secret leaks).
  3. **Standalone LSP Daemon (`tzero_lsp.py` / `tzero lsp`):** JSON-RPC Language Server emitting Zero-Leak diagnostics, `tzero.rules.json` boundary errors, `tzero_contracts` breaking-change warnings, and live AST CodeLens for VS Code, Neovim, and Zed.
  4. **Rust Native & WASM Bridge (`crates/tzero_jarvis_core`):** Add `PyO3` module / optional FFI subprocess bridge + WASM sandbox target (`tzero agent-kernel`), guarded cleanly when `cargo` is unavailable.
  5. **SCIP/LSIF Ingestion & Real LLM Task Benchmarks (`tzero_task_benchmark.py`):** Support importing SCIP indexes for cross-repo call graphs and running real local Ollama / deterministic patch-accuracy benchmarks (`Raw vs T-Zero AST`).
  6. **`tzero federation` & CI Matrix Hardening:** Team snapshot/LSH cache export/import + add `flake8`/`ruff`, `mypy`, `npm test`, extension packaging check, and `macos-latest` to `.github/workflows/ci.yml`.

