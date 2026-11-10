# T-Zero Phase 2: VS Code / Cursor Extension & Live Developer Dashboard Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans or superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Connect the VS Code / Cursor extension (`extensions/vscode/`) and local Web Developer Dashboard (`tzero_dashboard.py`) to live workspace AST telemetry, real settings, 10.9.0 commands, an Activity Bar Webview sidebar, and all 8 unexposed backend dashboard APIs.

**Architecture:** Extract pure JS helpers (`extensions/vscode/src/core.js`) testable under Node's built-in `node --test` runner without requiring an Electron VS Code host, add `--format json` support to `tzero --scan` and non-Python polyglot fallback to `tzero explain`, upgrade `extension.js` + `package.json` with a WebviewViewProvider sidebar and live status-bar updates, and replace static `tzero_dashboard.py` KPIs with cached live workspace metrics + interactive UI tabs for all 8 backend endpoints.

**Tech Stack:** Python 3.11+ (`unittest`, `http.server`, `json`), Node.js (`node --test`), VS Code Extension API (`vscode` v1.75+, WebviewViewProvider, CodeLensProvider).

**Spec:** [`docs/superpowers/plans/2026-11-10-tzero-v11-master-roadmap.md`](2026-11-10-tzero-v11-master-roadmap.md)

## Global Constraints
- **100% Free & Offline:** Zero external network calls in VS Code extension or Dashboard APIs.
- **100% Zero-Leak Guard:** `python tests/audit_secrets.py` must return `0` findings.
- **Zero Dependencies in VS Code Extension:** Keep `extensions/vscode` zero-npm-runtime-dependency so `vsce package --no-dependencies` continues succeeding.
- **TDD Enforced:** Failing Python/Node tests written and observed failing before implementation edits.

## Review Focus
- `tzero --scan <dir> --format json` on an empty directory or non-Python polyglot workspace must output valid JSON with `0` division-by-zero errors.
- `tzero explain <file.ts> --format json` on a non-Python file must return valid JSON using polyglot signatures rather than crashing inside `ast.parse`.
- `extensions/vscode/src/core.js` `computeCodeLensMetrics` must measure actual block/function span instead of `lineTokens * 6`, and `resolveExecutable` must honor custom `tzero.executablePath` with spaces.
- `extensions/vscode/src/extension.js` `autoInitOnOpen` must trigger at most once per workspace without prompting loops or throwing when `.mcp.json` already exists.
- `tzero_dashboard.py` `/api/stats` must dynamically reflect version `10.9.0` and real workspace token reduction while returning in <25ms on cached repeat hits.

---

### Task 1: JSON Telemetry Support for `tzero --scan` and Polyglot `tzero explain`

**Files:**
- Modify: `tzero_v3.py:8460-8525` (`run_scan_cli` + CLI dispatch) and `tzero_explain.py:89-160` (`ArchitecturalPassportGenerator.explain_file`)
- Test: `tests/test_explain.py`, `tests/test_cli.py`

**Interfaces:**
- Produces: `tzero --scan <dir> --format json` emitting JSON `{workspace_dir, total_files, raw_tokens, pruned_tokens, savings_pct, files}`; `ArchitecturalPassportGenerator.explain_file` supporting non-Python files cleanly via `PolyglotTokenReducer`.

- [ ] **Step 1: Write failing tests in `tests/test_explain.py` and `tests/test_cli.py`**
  - Test `ArchitecturalPassportGenerator.explain_file` on a temp `.ts` file asserting valid `ModulePassport` with `symbols` extracted and `token_savings_pct >= 0`.
  - Test `python tzero_v3.py --scan . --format json` asserting valid JSON output with `total_files`, `raw_tokens`, `pruned_tokens`, `savings_pct`.
- [ ] **Step 2: Run tests to verify failure (RED)**
  Run: `python -m unittest tests.test_explain tests.test_cli.TestCLI.test_scan_json -v`
  Expected: FAIL (`SyntaxError` in Python `ast.parse` on `.ts` file or non-JSON text output from `--scan`).
- [ ] **Step 3: Implement `--format json` in `run_scan_cli` and polyglot fallback in `tzero_explain.py`**
- [ ] **Step 4: Run tests to verify pass (GREEN)**
  Run: `python -m unittest tests.test_explain tests.test_cli -v`
  Expected: PASS.
- [ ] **Step 5: Commit**
  ```bash
  git add tzero_v3.py tzero_explain.py tests/test_explain.py tests/test_cli.py
  git commit -m "feat(cli): add JSON output to --scan and polyglot support to explain"
  ```

---

### Task 2: VS Code / Cursor Extension Pure Logic (`core.js`), Settings, 10.9.0 Commands & Activity Bar Sidebar

**Files:**
- Create: `extensions/vscode/src/core.js`
- Create: `extensions/vscode/test/extension.test.js`
- Modify: `extensions/vscode/package.json`
- Modify: `extensions/vscode/src/extension.js`
- Modify: `extensions/vscode/README.md`

**Interfaces:**
- Consumes: `tzero` CLI (`--scan --format json`, `explain`, `golden`, `budget`, `contracts`, `debt`, `mutate`, `bridge`, `merge-heal`)
- Produces: Node-tested `core.js` helpers (`resolveExecutable`, `formatStatusBar`, `computeCodeLensMetrics`, `buildSymbolContract`, `parseScanJson`), full `extension.js` wiring including `tzero.executablePath`, `tzero.autoInitOnOpen`, Activity Bar `tzeroSidebar` WebviewViewProvider, and `10.9.0` commands.

- [ ] **Step 1: Write failing Node tests in `extensions/vscode/test/extension.test.js`**
  Assert `resolveExecutable`, `formatStatusBar`, `computeCodeLensMetrics` (multi-line body token estimation vs 1-line stub), `buildSymbolContract`, `parseScanJson` behavior, and verify `extensions/vscode/package.json` contributes `viewsContainers`, `views`, and all `10.9.0` commands.
- [ ] **Step 2: Run `node --test extensions/vscode/test/extension.test.js` to verify RED**
  Expected: FAIL (`Cannot find module '../src/core.js'`).
- [ ] **Step 3: Implement `extensions/vscode/src/core.js`, update `package.json`, `extension.js`, and `README.md`**
- [ ] **Step 4: Run `node --test extensions/vscode/test/extension.test.js` and `node -c extensions/vscode/src/extension.js`**
  Expected: PASS.
- [ ] **Step 5: Commit**
  ```bash
  git add extensions/vscode/
  git commit -m "feat(vscode): wire live AST metrics, settings, 10.9.0 commands, and Webview sidebar"
  ```

---

### Task 3: Live `/api/stats` & Interactive 10.9.0 Suite UI in `tzero_dashboard.py`

**Files:**
- Modify: `tzero_dashboard.py`
- Modify: `tests/test_dashboard.py`

**Interfaces:**
- Produces: Dynamic `/api/stats` (`version`, `tools_count`, `canonical_tools_count`, `token_savings`, `raw_tokens`, `pruned_tokens`, `security`, `zero_leak_clean`) with short TTL cache, plus interactive frontend tabs in `HTML_PAGE` bound to `/api/debt/analyze`, `/api/budget/optimize`, `/api/golden/verify`, `/api/contracts/compare`, `/api/mutation/test`, `/api/bridge/reverse`, `/api/merge/heal`, and `/api/blackboard`.

- [ ] **Step 1: Update `tests/test_dashboard.py` with failing assertions (RED)**
  Assert `/api/stats` returns `version == "10.9.0"`, `tools_count >= 57` (or real registered count), numeric `raw_tokens` / `pruned_tokens`, and assert `GET /` HTML references all 8 API routes (`/api/debt/analyze`, `/api/budget/optimize`, `/api/golden/verify`, `/api/contracts/compare`, `/api/mutation/test`, `/api/bridge/reverse`, `/api/merge/heal`, `/api/blackboard`) and fetches `/api/stats` dynamically.
- [ ] **Step 2: Run `python -m unittest tests.test_dashboard -v` to verify RED**
  Expected: FAIL (`'10.0.0' != '10.9.0'` and missing UI fetch bindings).
- [ ] **Step 3: Implement live `/api/stats` caching and interactive UI tabs in `tzero_dashboard.py`**
- [ ] **Step 4: Run `python -m unittest tests.test_dashboard -v` and `python tests/audit_secrets.py`**
  Expected: PASS.
- [ ] **Step 5: Commit**
  ```bash
  git add tzero_dashboard.py tests/test_dashboard.py
  git commit -m "feat(dashboard): serve live workspace stats and expose 10.9.0 API suite in UI"
  ```

