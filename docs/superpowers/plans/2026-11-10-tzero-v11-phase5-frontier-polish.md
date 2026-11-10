# T-Zero v11 Phase 5 Frontier Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `/subagent-driven-development` to implement this plan task-by-task cleanly, one sequential implementer per task followed by a fresh spec+quality reviewer and a final `pro` whole-branch review.

**Goal:** Elevate T-Zero's v11 frontier modules (LSP, Polyglot Contracts/SARIF, SCIP + Multi-Repo Federation, Lifecycle Hooks, Dashboard/VS Code/MCP HTTP surfaces, and `--doctor --deep` E2E verification) to cohesive, production-grade interoperability with 100% free/offline execution and zero regressions.

**Architecture:** All enhancements live strictly inside existing modular boundaries (`tzero_lsp.py`, `tzero_contracts.py`, `tzero_scip.py`, `tzero_federation.py`, `tzero_hooks.py`, `tzero_dashboard.py`, `tzero_mcp.py`, `tzero_deps.py`, `extensions/vscode/`, and thin CLI routing in `tzero_v3.py`). `core` layers (`tzero_v3.py`, `tzero_jarvis/**`) never statically import `api` (`tzero_mcp.py`, `app.py`) or `cli` (`addmcp.py`, `tzero_dashboard.py`) modules.

**Tech Stack:** Python 3.11+ stdlib (`ast`, `sqlite3`, `json`, `urllib`, `subprocess`, `struct`), `tiktoken` BPE, `mcp`/`starlette` Streamable HTTP, vanilla Node/VS Code Extension API (zero runtime npm deps).

---

### Task 1: LSP Interactive Intelligence (`textDocument/hover`, `textDocument/codeAction`, Nested Class CodeLens & Live Subprocess Roundtrip)

**Files:**
- Modify: `tzero_lsp.py`
- Test: `tests/test_lsp.py`

**Specification:**
1. Refactor `TZeroLSPServer.compute_code_lenses(self, uri: str, text: str)` in `tzero_lsp.py` so Python files emit CodeLenses for BOTH top-level declarations AND methods defined inside `ClassDef` bodies (sorted cleanly by `lineno`; do not emit lenses for inner helper closures inside function bodies).
2. Add `TZeroLSPServer.compute_hover(self, uri: str, text: str, line: int, character: int = 0) -> Optional[Dict[str, Any]]`:
   - Resolves the enclosing symbol (`ClassDef`, `FunctionDef`, `AsyncFunctionDef`, or polyglot decl line) covering 0-indexed `line`.
   - Returns LSP Hover dict `{"contents": {"kind": "markdown", "value": ...}, "range": ...}` containing: symbol name, raw BPE tokens (`count_bpe_tokens(block)`), signature BPE tokens, savings percentage, AST statement count / complexity estimate, and workspace caller/reference count across buffer + `.py`/code files in `self.workspace_dir` (bounded safely for speed). Returns `None` when `line` is not inside any symbol.
3. Add `TZeroLSPServer.compute_code_actions(self, uri: str, text: str, diagnostics: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]`:
   - Evaluates `diagnostics` (or `self.analyze_document(uri, text)` if `diagnostics` is `None`).
   - For each diagnostic whose `code == "zero-leak"`, computes a quick-fix replacement on that line replacing the leaked literal with an `os.environ.get("TZERO_REDACTED_SECRET", "")` lookup (for Python assignment `KEY = "..."`) or `ZeroLeakEngine.sanitize_text(line)` fallback, returning valid LSP `CodeAction` (`title`, `kind: "quickfix"`, `diagnostics`, `isPreferred: True`, `edit: {"changes": {uri: [{"range": ..., "newText": ...}]}}`).
4. Update `TZeroLSPServer.handle_message`:
   - Declare `"hoverProvider": True` and `"codeActionProvider": True` inside `initialize` -> `result.capabilities`.
   - Route `"textDocument/hover"` to `compute_hover` (respecting `params["position"]["line"]` / `character`, falling back to `self.documents.get(uri, "")`).
   - Route `"textDocument/codeAction"` to `compute_code_actions` (using `(params.get("context") or {}).get("diagnostics")`).
5. Add TDD tests in `tests/test_lsp.py`:
   - Nested class method CodeLens emission (`OuterClass` + `OuterClass.method`).
   - `textDocument/hover` response check (token metrics, percentage, caller count, markdown `contents`).
   - `textDocument/codeAction` `WorkspaceEdit` quick-fix eliminates `zero-leak` diagnostic when applied.
   - Real subprocess stdio roundtrip spawning `sys.executable tzero_v3.py lsp` via `subprocess.Popen` (`initialize` -> `didOpen` -> `hover` -> `codeAction` -> `shutdown` -> `exit`).

---

### Task 2: Polyglot SemVer Contract Diffing & SARIF 2.1.0 CI Security/Contract Gate

**Files:**
- Modify: `tzero_contracts.py`, `tzero_v3.py`
- Test: `tests/test_contracts.py`

**Specification:**
1. Extend `ASTContractExtractor` in `tzero_contracts.py` with `POLYGLOT_EXTENSIONS = {".ts", ".tsx", ".js", ".jsx", ".rs", ".go", ".java", ".cs"}` and `@classmethod def extract_polyglot_contracts(cls, code: str, file_path: str = "module.ts") -> Tuple[Dict[str, FunctionContract], Dict[str, ClassContract]]`:
   - Uses `PolyglotTokenReducer` / `_lexical_scan_lines` (from `tzero_polyglot.py`) to extract classes/interfaces/structs and functions/methods for TS/JS/Rust/Go/Java/C#, parsing parameter names, defaults (`=`), variadics (`...`), and return annotations into standard `FunctionContract` / `ClassContract` structures.
   - Ignore private/unexported helpers starting with `_` cleanly (while keeping TypeScript/Go/Rust exported/public declarations accurately; in Go lowercase leading identifier is unexported unless method/struct rule, handle idiomatic Go exported uppercase vs TS `function`/`export function` & class methods!).
2. Update `ASTContractComparator.compare_code(cls, old_code: str, new_code: str, file_path: str = "code.py") -> ContractDiffReport`:
   - Route `.py` through `ASTContractExtractor.extract_from_code` (100% backward compatible), and any suffix in `ASTContractExtractor.POLYGLOT_EXTENSIONS` through `extract_polyglot_contracts`.
   - Extend `compare_git_revision` to evaluate `.py` AND `POLYGLOT_EXTENSIONS` changed files via `subprocess.run(["git", "diff", "--name-only", base_ref], ...)` (safe list args, no shell injection).
3. Add `@classmethod def format_sarif_report(cls, reports: List[ContractDiffReport]) -> Dict[str, Any]` on `ASTContractComparator`:
   - Emits SARIF `2.1.0` schema (`$schema`, `version: "2.1.0"`, `runs: [{"tool": {"driver": {"name": "T-Zero Contract Guardian", "version": "10.9.0", "rules": ...}}, "results": [...]}]`), mapping `breaking_changes` to `level: "error"` and `modifications`/`non_breaking_additions` (or breaking + modifications) with valid `ruleId`, `message.text`, and `locations[].physicalLocation.artifactLocation.uri`.
4. Add `--contracts-sarif [OUT_PATH]` (with `nargs="?"`, `const="-"`, `default=None`) in `tzero_v3.py` under `--contracts` / `--breaking-changes` handling: when passed, writes SARIF JSON to `OUT_PATH` (or prints SARIF JSON directly to stdout when `OUT_PATH == "-"`).
5. Add unit tests in `tests/test_contracts.py` covering TypeScript & Go breaking/compatible contract diffs, SARIF 2.1.0 structure validation, and `--contracts-sarif -` CLI flag.

---

### Task 3: Binary SCIP Protobuf Wire Decoder & Cross-Repo Federation Impact Engine

**Files:**
- Modify: `tzero_scip.py`, `tzero_federation.py`, `tzero_v3.py`
- Test: `tests/test_scip.py`, `tests/test_federation.py`

**Specification:**
1. Add pure-Python stdlib protobuf wire parser in `tzero_scip.py` (`ScipIndexImporter.from_scip_protobuf_bytes(cls, raw: bytes) -> ScipIndexGraph`) with zero external dependencies:
   - Implements minimal varint + length-delimited/packed field wire walker for SCIP protobuf (`Index.documents` tag `2`, `Document.relative_path` tag `1`, `Document.occurrences` tag `2`, `Occurrence.range` tag `1` packed/repeated varint `[line, startChar, ...]`, `Occurrence.symbol` tag `2`, `Occurrence.symbol_roles` tag `3`).
   - Updates `ScipIndexImporter.load(cls, path: str)`: if `path.lower().endswith(".scip")` or raw bytes fail UTF-8 JSON/LSIF decoding cleanly (`\x00` or binary wire header), decode via `from_scip_protobuf_bytes(raw_bytes)`. Preserves `.json` SCIP & `.lsif`/NDJSON loading unchanged.
2. Add `FederationSyncEngine.analyze_cross_repo_impact(cls, workspace_dir: str, symbol_name: str, scip_path: Optional[str] = None) -> Dict[str, Any]` in `tzero_federation.py`:
   - Scans local workspace files via `should_skip_dir`/`should_skip_file` cleanly to find local symbol references (`local_hits`).
   - Inspects `.tzero/federation/*.json` peer manifests: **cryptographically verifies** each peer via `cls.verify_manifest`. Tampered/unverified manifests MUST be listed in `unverified_peers` and excluded from `impacted_peers`!
   - Matches whole-word regex `\b{re.escape(symbol_name)}\b` in verified peer `modules[].skeleton`, collecting `{repo_name, rel_path, lang, matches}`.
   - If `scip_path` is provided and exists, loads `ScipIndexImporter.load(scip_path).trace_symbol(symbol_name)` into `scip_trace`.
3. Update `run_federation_cli` in `tzero_federation.py` and `tzero_v3.py`:
   - Add `--federation-symbol` (falling back to `--scip-symbol`) and `--federation-scip` flags in `tzero_v3.py`.
   - Support `--federation impact` (`tzero federation impact --federation-symbol Foo`); exit code `1` with JSON stderr error if symbol is missing.
4. Add unit tests in `tests/test_scip.py` (hand-encoded protobuf wire bytes roundtrip into `ScipIndexImporter.load("...scip")`) and `tests/test_federation.py` (`analyze_cross_repo_impact` verified vs tampered peer + SCIP merge + CLI `impact`).

---

### Task 4: Enterprise AI Lifecycle Hook Guardrails & Automated Hook Installer (`tzero hook --install`)

**Files:**
- Modify: `tzero_hooks.py`, `tzero_v3.py`
- Test: `tests/test_hooks.py`

**Specification:**
1. Harden `evaluate_pre_tool_use(payload, workspace_dir=".")` in `tzero_hooks.py`:
   - **Sensitive Secret File Read Guard:** For `READ_TOOL_NAMES`, inspect target file basename/path (`file_path`, `path`, `AbsolutePath`). Block (exit code `2`) direct reads of `.env`, `.env.local`, `.env.production`, `.env.staging`, `id_rsa`, `id_ed25519`, `*.pem`, `*.key`, `.npmrc`, `.pypirc`, `credentials.json`, while explicitly ALLOWING harmless templates (`.env.example`, `.env.template`, `.env.sample`, `.env.schema`).
   - **Shell Exfiltration Guard:** For `SHELL_TOOL_NAMES`, block exit code `2` when command combines outbound transport (`curl`, `wget`, `invoke-webrequest`, `iwr`, `nc`, `ncat`) with secret env/file targets (`$API_KEY`, `$SECRET`, `$TOKEN`, `$AWS_SECRET`, `.env`, `id_rsa`) OR dumps raw env secrets to stdout/network (`printenv |`, `env | curl`). Also preserve existing `ZeroLeakEngine.scan_text(cmd)` check.
   - **Architecture Boundary Guard (`tzero.rules.json`):** For `WRITE_TOOL_NAMES`, load `os.path.join(workspace_dir, "tzero.rules.json")` if present; check extracted write blobs for `forbidden_imports` from the target file's layer to forbidden target layers using local lightweight AST/regex extraction (do NOT violate `tzero.rules.json` imports in `tzero_hooks.py`), blocking with exit code `2` and descriptive reason on violation.
2. Add `install_hooks(workspace_dir: str = ".", client: str = "all") -> Dict[str, Any]` in `tzero_hooks.py`:
   - Supported targets: `"claude"` -> `.claude/settings.local.json`, `"cursor"` -> `.cursor/hooks.json`, `"gemini"` -> `.gemini/settings.json` (`"all"` updates all three).
   - Non-destructively merges `build_claude_cursor_hook_config()["hooks"]` (`PreToolUse`, `PostToolUse`) into existing JSON files: preserves unrelated keys and existing hooks, and stays idempotent (running twice does not duplicate T-Zero hook commands!).
3. Update `tzero_hooks.run_hook_cli(..., install_client: Optional[str] = None)` and `tzero_v3.py` (`--hook-install` with `nargs="?"`, `const="all"`, `choices=["all", "claude", "cursor", "gemini"]`) to invoke `install_hooks` and emit structured JSON summary.
4. Expand `tests/test_hooks.py` covering `.env` read block vs `.env.example` allow, shell exfiltration block, `tzero.rules.json` boundary block on write, idempotent `install_hooks` preserving user hooks, and `--hook-install` CLI route.

---

### Task 5: Full-Stack Surface Unification (Dashboard v11 Workbench, VS Code v11 Commands & MCP HTTP Fallback/ASGI Test)

**Files:**
- Modify: `tzero_dashboard.py`, `tzero_mcp.py`, `extensions/vscode/package.json`, `extensions/vscode/src/core.js`, `extensions/vscode/src/extension.js`, `extensions/vscode/test/extension.test.js`, `tests/test_dashboard.py`, `tests/test_mcp.py`

**Specification:**
1. **`tzero_dashboard.py`:**
   - Add GET endpoints:
     - `/api/federation/peers`: returns `{"success": True, "peers": FederationSyncEngine.list_peers(".")}`.
     - `/api/hooks/preview`: returns `{"success": True, "config": build_claude_cursor_hook_config()}`.
   - Add POST endpoints:
     - `/api/federation/impact`: reads `{"symbol": ..., "scip_path": ...}`, returns `FederationSyncEngine.analyze_cross_repo_impact(".", symbol, scip_path)`.
     - `/api/scip/summary`: reads `{"path": ...}`; returns `404`/`{"success": False, "error": ...}` gracefully when missing, or `ScipIndexImporter.load(path).export_tzero_graph()` when valid.
   - Add 3 new UI tabs (`Federation`, `Hooks Guard`, `SCIP Graph`) to the Enterprise Engineering Suite in `HTML_PAGE` without breaking existing tabs or `/api/stats` `<50ms` performance. Update panel badge cleanly from `8 Live Endpoints` to `12 Live Endpoints`.
2. **`tzero_mcp.py`:**
   - In `main()`'s `--http` branch non-uvicorn fallback (lines ~5161-5164), configure `host`/`port` cleanly via `inspect.signature(server.run)` or `setattr(server.settings, ...)` before `server.run(transport="streamable-http", ...)` so custom `--host`/`--port` are respected even without uvicorn. Keep tool counts unchanged (`21` canonical, `58` all) so TDQS Anchor 5 invariants stay green.
   - In `tests/test_mcp.py`, add an integration test invoking `create_http_app(mode="canonical")` through `starlette.testclient.TestClient` sending `POST /mcp` (`initialize` JSON-RPC payload with `Accept: application/json, text/event-stream`) and verifying HTTP 200 JSON-RPC response containing `serverInfo` / capabilities!
3. **`extensions/vscode/`:**
   - Add commands `tzero.lspCheck` (`T-Zero: Validate LSP Diagnostics & Architecture (--check-arch)`), `tzero.hookInstall` (`T-Zero: Install AI Lifecycle Hooks (--hook-install all)`), and `tzero.federationImpact` (`T-Zero: Analyze Cross-Repo Federation Impact`) to `package.json`, QuickPick menu, `core.js` sidebar actions, and `extension.js` command registration (using safe array args + `getWorkspaceRoot()`, zero runtime npm deps).
   - Add tests in `extensions/vscode/test/extension.test.js` covering new manifest commands and sidebar rendering.
4. Update `tests/test_dashboard.py` to test `/api/federation/peers`, `/api/hooks/preview`, `/api/federation/impact`, `/api/scip/summary` + HTML tab presence.

---

### Task 6: `--doctor --deep` Offline Self-Diagnostic, Documentation Refresh & v11 E2E Integration Suite

**Files:**
- Modify: `tzero_deps.py`, `tzero_v3.py`, `README.md`
- Create: `tests/test_v11_e2e_integration.py`

**Specification:**
1. Extend `tzero_deps.py` (`run_doctor(deep: bool = False) -> int`) and `tzero_v3.py` (`--deep` flag passed to `tzero_deps.run_doctor(deep=getattr(args, "deep", False))`):
   - When `deep=True`, executes a fast (`<2s`) offline self-check across core v11 subsystems in a `tempfile.TemporaryDirectory`:
     1) `count_bpe_tokens` (`tiktoken`)
     2) `PolyglotTokenReducer.reduce_code` (Python + TS)
     3) `ZeroLeakEngine.scan_text`
     4) `tzero_lsp.TZeroLSPServer` (`didOpen` + `hover` + `codeAction`)
     5) `tzero_hooks.evaluate_pre_tool_use` + `evaluate_post_tool_use`
     6) `tzero_federation.FederationSyncEngine` (`export_manifest` + `verify_manifest`)
     7) `tzero_scip.ScipIndexImporter` (`from_scip_dict`)
     8) `tzero_contracts.ASTContractComparator` (`compare_code` + `format_sarif_report`)
     9) `tzero_rust_bridge.AgentKernelSandbox` + `tzero_snapshot.ASTSnapshotManager`
   - Prints `[ OK ]` / `[FAIL]` summary lines per subsystem; never does network I/O; never imports `tzero_mcp` or `tzero_dashboard` statically at module top level in `tzero_deps.py`.
2. Update `README.md` cleanly:
   - Correct the MCP tool count heading (`21 Canonical MCP Tools` + `search_tools` discovery) and add a concise **v11 Frontier Architecture & Capabilities** section documenting `--lsp`, `--hook` / `--hook-install`, `--federation` (`export/import/verify/impact`), `--scip-import`, `--snapshot`, `--cache-aligned`, `--contracts-sarif`, `--agent-kernel`, and `--doctor --deep`.
3. Update `tzero_v3.py` help/quickstart epilog cleanly to surface `--lsp`, `--hook-install`, `--federation impact`, `--contracts-sarif`, and `--doctor --deep`.
4. Create `tests/test_v11_e2e_integration.py` verifying the complete offline v11 pipeline end-to-end (`scan --format json` -> `snapshot` incremental -> `pack --cache-aligned` KV prefix -> polyglot `contracts` + SARIF -> `hooks` block/prune/install -> `lsp` hover+codeAction -> `scip` protobuf + `federation` impact -> `doctor --deep` subprocess exit 0) and confirm `sync_release_metadata.py --version 10.9.0 --check` passes cleanly.

---

### Task 7: M8ven 100% Directory Compliance (All 4 Tool Hints, `PRIVACY.md`, 100% Tool Test Coverage) & Non-Slop Badge-First `README.md` / `README.tr.md` Overhaul

**Files:**
- Modify: `app.py` (`MCP_TOOLS_CATALOG` 4-hint annotations & accurate 21/58 tool counts)
- Modify: `tzero_fixer/mcp_server.py` (`PCFixerMcpServer.TOOLS` 4-hint annotations)
- Create: `PRIVACY.md`
- Create: `tests/test_m8ven_compliance.py`
- Modify: `README.md`, `README.tr.md`

**Specification:**
1. **`app.py`**: Add `"annotations": {"readOnlyHint": ..., "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}` (exact booleans: `True` for 9 read-only tools, `False` for `export_agent_rules`) to every dict in `MCP_TOOLS_CATALOG`, and update stale `"20-Tool"` / `"20 production-grade"` strings cleanly to match `21 Canonical / 58 Runtime MCP Tools`.
2. **`tzero_fixer/mcp_server.py`**: Add matching `"annotations"` dicts (`readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint`) across all 7 tools in `PCFixerMcpServer.TOOLS` matching `tzero_pc_fixer.py`.
3. **`PRIVACY.md`**: Author concise, transparent MCP Registry privacy policy detailing 100% local offline execution, zero remote telemetry, OS-native secret keyring storage, and optional user-initiated local benchmark variables.
4. **`tests/test_m8ven_compliance.py`**: Add AST + runtime validation asserting 100% of tools in `tzero_mcp.py`, `app.py`, `tzero_pc_fixer.py`, and `tzero_fixer/mcp_server.py` declare all 4 boolean hints, reference every single tool name in tests for 100% static coverage, verify `PRIVACY.md` exists, and confirm single M8ven Verified badge presence in `README.md`.
5. **`README.md` & `README.tr.md`**: Remove duplicated badges, contradictory numbers (`14 Canonical`, `20 MCP Tools`, `52 full tools`, `10.8.0`/`10.0.0`), broken double-escaped math, and AI-slop hype copy; establish a crisp, scannable badge strip (PyPI, npm, VS Code Marketplace, M8ven Verified Publisher, Glama, Smithery, GitHub Actions CI, TDQS 5.0/5.0, Python 3.11+, License, Privacy Policy link), clean v10.9.0 / v11 Frontier CLI & 21 Canonical MCP Tool documentation. (Replaces redundant `README.md` docs step in Task 6 so edits don't collide.)
