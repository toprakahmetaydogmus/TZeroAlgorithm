# T-Zero v11 Phase 4 Implementation Plan: 2026 Ecosystem, MCP Streamable HTTP, Hooks, LSP, Rust Bridge, SCIP & CI Matrix

> **For agentic workers:** Execute strictly via TDD (`RED -> verify fail -> GREEN -> verify pass -> commit`), keeping 100% offline/free guarantees and 100% Zero-Leak security. Clean conditional guards must handle optional external toolchains (`cargo`, `ollama`) since this machine does not have `cargo` installed.

**Goal:** Elevate T-Zero into the 2026 autonomous engineering ecosystem: modern MCP 2026 transport/schema/discovery (`tzero_mcp.py`), Claude/Cursor/Gemini lifecycle hooks (`tzero_hooks.py`), stdio LSP daemon (`tzero_lsp.py`), Rust core FFI/PyO3 + WASM agent kernel bridge (`tzero_rust_bridge.py` + `crates/tzero_jarvis_core`), SCIP/LSIF index importer + real Ollama benchmark (`tzero_scip.py`, `tzero_task_benchmark.py`), cryptographic federation (`tzero_federation.py`), and multi-OS CI hardening (`.github/workflows/ci.yml`).

**Architecture:** Clean inward-only modular Python adapters (`tzero_hooks.py`, `tzero_lsp.py`, `tzero_rust_bridge.py`, `tzero_scip.py`, `tzero_federation.py`) reusing `tzero_security`, `tzero_polyglot`, `tzero_contracts`, `tzero_arch_test`, and `tzero_jarvis`; all added to `pyproject.toml` `py-modules` and synced to `installers/npm/src/`.

**Tech Stack:** Python 3.11–3.14, `mcp 2.3.0` (`MCPServer` / `Context` / `streamable_http_app`), stdlib `json`, `urllib`, `hashlib`, `ctypes`, `subprocess`, GitHub Actions.

---

### Task 1: MCP 2026 Spec Upgrades (`tzero_mcp.py`)

**Files:**
- Modify: `tzero_mcp.py` (`--http` / `--host` / `--port` CLI args for `streamable-http` + ASGI `create_http_app`, `ctx: Context = None` progress reporting in long-running scans/benchmarks, `@_canon_tool(..., structured_output=True)` / TypedDict/dict structured return on core scan/audit tools, dynamic resource template `tzero://file/{path}/skeleton`, `search_tools(query, category, limit)` progressive discovery registered across both canonical & all modes)
- Modify: `tests/test_mcp.py` (update expected tool counts deliberately + add tests for `create_http_app`, `search_tools`, URI resource template `tzero://file/{path}/skeleton`, `structured_output`, and `ctx.report_progress`)

---

### Task 2: Claude Code / Gemini CLI / Cursor Lifecycle Hook Runner (`tzero_hooks.py`, `tzero_v3.py`)

**Files:**
- Create: `tzero_hooks.py` (`evaluate_pre_tool_use(payload, workspace_dir)`, `evaluate_post_tool_use(payload, workspace_dir)`, `run_hook_cli(hook_type, stdin_stream=None)` — blocks hardcoded secrets on `Write`/`Edit`/`MultiEdit` via `ZeroLeakEngine`, auto-prunes oversized `Read` payloads cleanly via `PolyglotTokenReducer` / line bounds, emits hook JSON `{decision, reason, updatedInput/additionalContext}` with non-zero exit code 2 on block)
- Modify: `tzero_v3.py` (wire `tzero hook --event PreToolUse|PostToolUse` subcommand + `init_workspace` hook config export option)
- Create: `tests/test_hooks.py`

---

### Task 3: T-Zero Stdio LSP Daemon (`tzero_lsp.py`, `tzero_v3.py`)

**Files:**
- Create: `tzero_lsp.py` (`Content-Length` framed JSON-RPC stdio LSP server implementing `initialize`, `initialized`, `textDocument/didOpen`, `textDocument/didChange`, `textDocument/didSave`, `textDocument/codeLens`, `shutdown`, `exit`; publishes `textDocument/publishDiagnostics` combining `ZeroLeakEngine` secret leaks, `tzero.rules.json` architecture violations, and `tzero_contracts` breaking-change hints)
- Modify: `tzero_v3.py` (wire `tzero lsp` / `--lsp` CLI entrypoint)
- Create: `tests/test_lsp.py`

---

### Task 4: Rust Core FFI/PyO3 + WASM Agent Kernel Bridge (`tzero_rust_bridge.py` & `crates/tzero_jarvis_core`)

**Files:**
- Modify: `crates/tzero_jarvis_core/Cargo.toml` & `crates/tzero_jarvis_core/src/lib.rs` (add C-ABI / optional `pyo3` + `cdylib`/`rlib` + `wasm32` friendly exports for high-speed triplet/shingle LSH similarity without breaking `cargo test` when Rust is available)
- Create: `tzero_rust_bridge.py` (`RustCoreBridge` loading native shared library via `ctypes` or subprocess `tzero_jarvis_core` JSON CLI when present, falling back seamlessly to `tzero_jarvis` pure-Python engine when native binary/Cargo is absent; plus `AgentKernelSandbox` generating deterministic WebAssembly/policy manifest `tzero agent-kernel` dry-run checks)
- Modify: `tzero_v3.py` (wire `tzero agent-kernel` subcommand)
- Create: `tests/test_rust_bridge.py`

---

### Task 5: SCIP/LSIF Cross-Language Index Importer & Real Ollama Benchmark Mode (`tzero_scip.py`, `tzero_task_benchmark.py`, `tzero_v3.py`)

**Files:**
- Create: `tzero_scip.py` (`ScipIndexImporter`: imports SCIP/LSIF JSON & protobuf-like symbol/occurrence indexes into T-Zero cross-repo call graphs, computes precision call chains across polyglot modules)
- Modify: `tzero_task_benchmark.py` (add real local Ollama HTTP benchmark runner `--ollama-model` + 8-task adversarial multi-file patch accuracy benchmark alongside fast offline simulation, zero network calls during default offline suite)
- Modify: `tzero_v3.py` (wire `--scip-import` / `scip` + `--benchmark --ollama-model` options)
- Create: `tests/test_scip.py` and extend `tests/test_task_benchmark.py`

---

### Task 6: Cryptographic Federation Sync & Multi-OS CI Hardening (`tzero_federation.py`, `tzero_v3.py`, `.github/workflows/ci.yml`, Packaging Sync)

**Files:**
- Create: `tzero_federation.py` (`FederationSyncEngine`: exports sanitized AST interface manifests + SHA-256 integrity signatures + causal summaries without leaking raw proprietary function bodies, imports peer manifests for multi-repo `ChangeImpactAnalyzer` & contract checking; ZERO private source leak)
- Modify: `tzero_v3.py` (wire `tzero federation export|import|verify`)
- Modify: `.github/workflows/ci.yml` (add `macos-latest`, `ruff`/`flake8` lint step, `node --test installers/npm/test/package.test.js`, `node --test extensions/vscode/test/extension.test.js`, `python tests/audit_secrets.py`, `python scripts/sync_release_metadata.py --check`)
- Modify: `pyproject.toml`, `requirements.txt`, `scripts/sync_release_metadata.py`, `tests/test_federation.py`, `tests/test_ci_workflow.py`
- Final Sync: `python scripts/sync_release_metadata.py --sync-npm` + full verification suite!

