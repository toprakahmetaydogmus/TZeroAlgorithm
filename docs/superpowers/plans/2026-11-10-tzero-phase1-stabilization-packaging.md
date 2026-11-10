# T-Zero Phase 1: Core Stabilization, Runtime Bugfixes & Packaging Sync Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate all verified runtime crashes/silent fallbacks across MCP/TUI/CLI/Polyglot, synchronize versions and module packaging across PyPI/npm/VS Code/registries, and fix broken CI/Action/Docker distribution configurations.

**Architecture:** Fix root-cause parameter/return contract mismatches in `tzero_mcp.py`, `tzero_tui.py`, `tzero_v3.py`, and `tzero_polyglot.py` under strict TDD, introduce a single-source release metadata synchronization script (`scripts/sync_release_metadata.py`) covering `pyproject.toml`, `server.json`, `smithery.json`, `glama.json`, `Formula/tzero.rb`, `installers/npm/package.json`, `extensions/vscode/package.json`, `tzero_mcp.py`, and `tzero_v3.py`, and align `action.yml`, `installers/npm/src/`, `.dockerignore`, and `scripts/publish_vscode.ps1`.

**Tech Stack:** Python 3.11+ (`unittest`, `ast`, `json`), Node.js (`node --test`), YAML/Docker/PowerShell.

**Spec:** [`docs/superpowers/plans/2026-11-10-tzero-v11-master-roadmap.md`](2026-11-10-tzero-v11-master-roadmap.md)

## Global Constraints
- **100% Free & Offline:** Zero external paid APIs or telemetry.
- **100% Zero-Leak Guard:** `python tests/audit_secrets.py` must report `0` findings.
- **TDD Strictly Enforced:** Every bugfix and script requires a failing regression test watched fail BEFORE implementing the fix.
- **Preserve Gitignored Private Files:** Do not stage or expose `tzero_gateway.py` or `enterprise_onprem/` to git.
- **Existing MCP Contract:** Maintain tool count assertions in `tests/test_mcp.py` (`57` in `all` mode, `20` in `canonical` mode).

## Review Focus
- `heal_hallucinated_code` called on valid Python code with 0 hallucinations must return a non-empty Markdown string (never `None`).
- `TZeroTerminalCockpit.gather_workspace_metrics` on a directory containing `.py` and `.ts` files must compute non-fallback token counts using real AST/polyglot reduction and real Zero-Leak status (`WARNING` when a secret exists, not hardcoded `SECURE`).
- `tzero_v3.py --vault <dir> --migrate` on a directory containing a mock hardcoded secret must migrate the file cleanly without `TypeError: 'int' object is not iterable`, and `tzero --export-repomap -` must write to `stdout` without creating a file named `-`.
- Building a wheel/sdist from `pyproject.toml` (`python -m build` / `pip install --no-deps .` in an isolated venv or module import check) must include all 10 `10.8.0`/`10.9.0` modules (`tzero_arch_test`, `tzero_blackboard`, `tzero_budget`, `tzero_contracts`, `tzero_debt`, `tzero_golden`, `tzero_mutation`, `tzero_semantic_merge`, `tzero_subagent_engine`, `tzero_turbo`).
- `action.yml` must invoke the installed `tzero` CLI (never relative `python tzero_v3.py`) so external repos running the GitHub Action do not crash with file-not-found.

---

### Task 1: Fix `tzero_mcp.py` Runtime Bugs (`heal_hallucinated_code`, `transpile_model_bridge`, `execute_codebase_workflow`)

**Files:**
- Modify: `tzero_mcp.py:4030-4108` and `tzero_mcp.py:4350-4358`
- Test: `tests/test_mcp.py`

**Interfaces:**
- Consumes: `ASTHallucinationAutoCorrector.heal_code`, `query_memory_store(query, query_mode, project_root)`, `manage_memory_store(operation, content, store_name, project_root)`
- Produces: Valid Markdown `str` return for `heal_hallucinated_code` when `rep.actions` is empty, and error-free routing for `execute_codebase_workflow(action="memory_query"|"memory")`.

- [ ] **Step 1: Write failing tests in `tests/test_mcp.py`**
  Add `test_heal_hallucinated_code_clean_returns_markdown` calling `heal_hallucinated_code` on `"def add(a: int, b: int) -> int:\n    return a + b\n"` and asserting `isinstance(text, str)` and `"Flawless Code"` in text; and `test_execute_workflow_memory_actions` calling `execute_codebase_workflow(action="memory_query", query="AST")` and `execute_codebase_workflow(action="memory", target="test fact", options='{"operation": "list"}')` and asserting no `"TypeError"` or `"unexpected keyword"` in output.
- [ ] **Step 2: Run tests to verify they fail**
  Run: `python -m unittest tests.test_mcp.TestMCPServer.test_heal_hallucinated_code_clean_returns_markdown tests.test_mcp.TestMCPServer.test_execute_workflow_memory_actions -v`
  Expected: FAIL (`None` returned or `TypeError` on unexpected keyword `store_name`/`payload`).
- [ ] **Step 3: Fix `tzero_mcp.py`**
  - Add `return "\n".join(lines)` at the end of `heal_hallucinated_code` (`~4062`) and remove the dead `return "\n".join(lines)` at line `4107` in `transpile_model_bridge`.
  - Update `execute_codebase_workflow` (`4351-4356`): call `query_memory_store(query=query or target, query_mode=opts.get("query_mode", "semantic"), project_root=opts.get("project_root", "."))` and `manage_memory_store(operation=op, content=query or target, store_name=opts.get("store_name", "default"), project_root=opts.get("project_root", "."))`.
- [ ] **Step 4: Run `tests/test_mcp.py` to verify pass**
  Run: `python -m unittest tests.test_mcp -v`
  Expected: PASS (all MCP tests green).
- [ ] **Step 5: Commit**
  ```bash
  git add tzero_mcp.py tests/test_mcp.py
  git commit -m "fix(mcp): return markdown on clean heal and fix workflow memory kwargs"
  ```

---

### Task 2: Fix `tzero_tui.py` Metrics, Zero-Leak Status & Interactive Dispatch

**Files:**
- Modify: `tzero_tui.py:45-235`
- Test: `tests/test_tui.py`

**Interfaces:**
- Consumes: `PolyglotTokenReducer.reduce_code(content: str, filename: str = "", mode: str = "ultra") -> str`, `ZeroLeakEngine.scan_workspace(workspace_dir: str) -> dict`
- Produces: Real measured `raw_tokens`, `pruned_tokens`, `savings_pct`, and real `zero_leak_status` in `TZeroTerminalCockpit.gather_workspace_metrics(workspace_dir: str) -> Dict[str, Any]`.

- [ ] **Step 1: Write failing tests in `tests/test_tui.py`**
  Add `test_gather_workspace_metrics_uses_real_reduction_not_fallback` creating a temporary directory with a multi-function `.py` file of known token count (e.g. 5 functions with 10-line bodies) and asserting `metrics["raw_tokens"] != metrics["total_files"] * 450` and `0 < metrics["pruned_tokens"] < metrics["raw_tokens"]`; add `test_gather_workspace_metrics_reports_real_zero_leak_violation` with a temp file containing a synthetic test token pattern and asserting `"SECURE"` is NOT in `metrics["zero_leak_status"]`.
- [ ] **Step 2: Run tests to verify they fail**
  Run: `python -m unittest tests.test_tui -v`
  Expected: FAIL (`raw_tokens` equals `450` fallback and `zero_leak_status` is hardcoded `"100% SECURE (VERIFIED)"`).
- [ ] **Step 3: Fix `tzero_tui.py`**
  - Fix line `75`: call `pruned_code = reducer.reduce_code(raw_code, filename=full_p, mode="ultra")` (no `lang=` kwarg, no 2-tuple unpack).
  - Run `ZeroLeakEngine.scan_workspace(abs_ws)` (with safe fallback) to set `zero_leak_status` dynamically (e.g. `"100% SECURE (VERIFIED)"` only when `violation_count == 0`, else `f"WARNING: {violation_count} SECRET(S)"`).
  - Update prompt line `182` from `[0-7]` to `[0-11]`, replace hardcoded `version="v10.0.0"` on line `211` with current package version, and start `tzero_dashboard` background thread on choice `[6]` if port `8421` is not listening.
- [ ] **Step 4: Run `tests/test_tui.py` to verify pass**
  Run: `python -m unittest tests.test_tui -v`
  Expected: PASS.
- [ ] **Step 5: Commit**
  ```bash
  git add tzero_tui.py tests/test_tui.py
  git commit -m "fix(tui): compute real polyglot metrics, zero-leak status, and cockpit prompts"
  ```

---

### Task 3: Fix `tzero_v3.py` (`--vault --migrate`, `--export-repomap -`) and `tzero_polyglot.py` (Java `{Ellipsis}`)

**Files:**
- Modify: `tzero_v3.py:8545-8556` and `tzero_v3.py:9634-9651`
- Modify: `tzero_polyglot.py:255`
- Test: `tests/test_auto_vault.py`, `tests/test_cli.py`, `tests/test_polyglot.py`

**Interfaces:**
- Consumes: `ZeroLeakEngine.scan_workspace`, `ZeroLeakEngine.auto_migrate_to_env`, `ContextExportManager.generate_repo_map`
- Produces: Error-free directory vault migration, stdout output when `out_file == "-"`, and valid `{ ... }` Java signature pruning.

- [ ] **Step 1: Write failing tests**
  - In `tests/test_auto_vault.py`: `test_cli_vault_migrate_directory` creates a temp directory with a `.py` file containing a concatenated synthetic key (`"sk" + "-proj-" + "99a8b7c6d5e4f3a2b1c099887766554433221100aa"`) and invokes `python tzero_v3.py --vault <tmpdir> --migrate`, asserting `returncode == 0` and `.env` created in `<tmpdir>`.
  - In `tests/test_cli.py`: `test_export_repomap_stdout_dash` runs `python tzero_v3.py --export-repomap - --dir .` and asserts `returncode == 0`, stdout contains module symbols, and no file named `"-"` is created on disk.
  - In `tests/test_polyglot.py`: `test_java_multiline_method_no_ellipsis_literal` calls `PolyglotTokenReducer.reduce_java("public class A {\n    public void run(\n        int x)\n    {\n        int y = 1;\n    }\n}", mode="ultra")` and asserts `"{Ellipsis}"` is NOT in output and `"{ ... }"` IS in output.
- [ ] **Step 2: Run tests to verify they fail**
  Run: `python -m unittest tests.test_auto_vault tests.test_cli.TestCLI.test_export_repomap_stdout_dash tests.test_polyglot -v`
  Expected: FAIL (`TypeError: 'int' object is not iterable`, file `"-"` created / missing stdout content, `"{Ellipsis}"` emitted).
- [ ] **Step 3: Implement fixes**
  - `tzero_v3.py:9636`: extract `violating_files = sorted({v["file"] for v in violations if v.get("file")})` and iterate over `violating_files`.
  - `tzero_v3.py:8552-8555`: if `out_file == "-"`, `print(content)` directly to stdout and return without writing a `"-"` file.
  - `tzero_polyglot.py:255`: change `f"{line} { ... }"` to `f"{line} {{ ... }}"`.
- [ ] **Step 4: Run tests to verify pass**
  Run: `python -m unittest tests.test_auto_vault tests.test_cli tests.test_polyglot -v`
  Expected: PASS.
- [ ] **Step 5: Commit**
  ```bash
  git add tzero_v3.py tzero_polyglot.py tests/test_auto_vault.py tests/test_cli.py tests/test_polyglot.py
  git commit -m "fix(core): fix vault directory migration, stdout repomap export, and java f-string brace"
  ```

---

### Task 4: Fix `pyproject.toml` Module Packaging & Unify Release Metadata Sync

**Files:**
- Modify: `pyproject.toml`
- Create: `scripts/sync_release_metadata.py`
- Modify (synced to unified version `10.9.0`): `server.json`, `smithery.json`, `glama.json`, `Formula/tzero.rb`, `installers/brew/tzero.rb`, `installers/npm/package.json`, `extensions/vscode/package.json`, `tzero_mcp.py:45`, `tzero_v3.py:8734`, `tzero_task_benchmark.py:57`
- Test: `tests/test_packaging_sync.py`

**Interfaces:**
- Consumes: Root `pyproject.toml` version and `tzero_*.py` module list
- Produces: `sync_release_metadata(target_version: str, check_only: bool = False) -> dict` verifying zero version drift and zero missing root modules in `pyproject.toml`.

- [ ] **Step 1: Write failing test `tests/test_packaging_sync.py`**
  Verify:
  1. Every non-private root `tzero_*.py` module (excluding gitignored `tzero_gateway.py`) is listed in `pyproject.toml` `[tool.setuptools] py-modules`.
  2. `pyproject.toml` does not require unused `typer` or ship `app` without optional extras.
  3. All release manifests (`pyproject.toml`, `server.json`, `smithery.json`, `glama.json`, `Formula/tzero.rb`, `installers/npm/package.json`, `extensions/vscode/package.json`, `tzero_mcp.SERVER_VERSION`) match the canonical release version.
- [ ] **Step 2: Run test to verify it fails**
  Run: `python -m unittest tests.test_packaging_sync -v`
  Expected: FAIL (10 missing `py-modules`, version mismatch across `10.7.0`/`10.8.0`/`10.9.0`).
- [ ] **Step 3: Update `pyproject.toml` and create `scripts/sync_release_metadata.py`**
  - Add missing 10 `py-modules` (`tzero_arch_test`, `tzero_blackboard`, `tzero_budget`, `tzero_contracts`, `tzero_debt`, `tzero_golden`, `tzero_mutation`, `tzero_semantic_merge`, `tzero_subagent_engine`, `tzero_turbo`) to `pyproject.toml`.
  - Add `tzero-tui = "tzero_tui:main"` and `pc-fixer-mcp = "pc_fixer_mcp:main"` to `[project.scripts]`; move `gradio` (`app.py`) to `[project.optional-dependencies] space = ["gradio>=4.0.0"]` and remove unused `typer` (keeping `requirements.txt` aligned).
  - Run `python scripts/sync_release_metadata.py --version 10.9.0` to align all manifests cleanly.
- [ ] **Step 4: Run `tests/test_packaging_sync.py` and `tests/test_cli.py` to verify pass**
  Run: `python -m unittest tests.test_packaging_sync tests.test_cli -v`
  Expected: PASS.
- [ ] **Step 5: Commit**
  ```bash
  git add pyproject.toml requirements.txt scripts/sync_release_metadata.py server.json smithery.json glama.json Formula/tzero.rb installers/brew/tzero.rb installers/npm/package.json extensions/vscode/package.json tzero_mcp.py tzero_v3.py tzero_task_benchmark.py tests/test_packaging_sync.py
  git commit -m "chore(release): sync all manifests to 10.9.0 and include missing py-modules in pyproject.toml"
  ```

---

### Task 5: Synchronize `installers/npm/src/` With Root Modules

**Files:**
- Modify/Create inside `installers/npm/src/` (copy updated root `tzero*.py`, `addmcp.py`, `main.py`, `tzero_jarvis/`, `tzero_fixer/`, including missing `10.9.0` modules `tzero_arch_test.py`, `tzero_budget.py`, `tzero_contracts.py`, `tzero_debt.py`, `tzero_golden.py`, `tzero_mutation.py`)
- Modify: `scripts/sync_release_metadata.py` (add `--sync-npm` helper)
- Modify: `installers/npm/test/package.test.js`

- [ ] **Step 1: Add failing assertions in `installers/npm/test/package.test.js`**
  Add `tzero_arch_test.py`, `tzero_budget.py`, `tzero_contracts.py`, `tzero_debt.py`, `tzero_golden.py`, `tzero_mutation.py` to `coreFiles` in `package.test.js`.
- [ ] **Step 2: Run `node --test` to verify it fails**
  Run: `node --test installers/npm/test/package.test.js`
  Expected: FAIL (`Expected tzero_golden.py to exist`, etc.).
- [ ] **Step 3: Sync `installers/npm/src/` via `scripts/sync_release_metadata.py --sync-npm`**
  Copy all non-gitignored root `.py` modules and packages cleanly into `installers/npm/src/`.
- [ ] **Step 4: Run `node --test` to verify pass**
  Run: `node --test installers/npm/test/package.test.js`
  Expected: PASS.
- [ ] **Step 5: Commit**
  ```bash
  git add installers/npm/ scripts/sync_release_metadata.py
  git commit -m "chore(npm): synchronize installers/npm/src with 10.9.0 modules"
  ```

---

### Task 6: Repair `action.yml` for External Repositories & Real `$GITHUB_OUTPUT`

**Files:**
- Modify: `action.yml:45-95`
- Test: `tests/test_action_yml.py`

**Interfaces:**
- Consumes: Installed `tzero` CLI entrypoint (`tzero review`, `tzero --audit`, `tzero --export-repomap`, `tzero --enforce-boundaries`, `tzero --export-agent-rules`)
- Produces: Valid `$GITHUB_OUTPUT` values for `token-savings-pct`, `secret-findings`, `blast-radius-score`.

- [ ] **Step 1: Write failing test `tests/test_action_yml.py`**
  Parse `action.yml` (via regex/YAML or PyYAML-free safe parser) and assert:
  - `runs.steps` does NOT invoke `python tzero_v3.py`.
  - `runs.steps` writes `token-savings-pct`, `secret-findings`, and `blast-radius-score` to `$GITHUB_OUTPUT`.
  - Inputs `audit-level`, `enforce-boundaries`, and `export-rules` are referenced in `runs.steps`, and `mode = tree` is handled.
- [ ] **Step 2: Run test to verify it fails**
  Run: `python -m unittest tests.test_action_yml -v`
  Expected: FAIL.
- [ ] **Step 3: Update `action.yml`**
  Invoke installed `tzero` CLI commands, handle `review` / `audit` / `tree` modes, enforce `enforce-boundaries` and `export-rules` conditionally, parse JSON/metrics via inline `python -c` to emit real `token-savings-pct`, `secret-findings`, `blast-radius-score` to `"$GITHUB_OUTPUT"` and dynamically populate `$GITHUB_STEP_SUMMARY`.
- [ ] **Step 4: Run `tests/test_action_yml.py` to verify pass**
  Run: `python -m unittest tests.test_action_yml -v`
  Expected: PASS.
- [ ] **Step 5: Commit**
  ```bash
  git add action.yml tests/test_action_yml.py
  git commit -m "fix(ci): make action.yml use installed tzero CLI and emit real outputs"
  ```

---

### Task 7: Fix Docker Context, PowerShell Publisher & Archive Dead Duplicates

**Files:**
- Modify: `.dockerignore`, `Dockerfile.glama` (delegate or note unified `Dockerfile`), `scripts/publish_vscode.ps1`
- Modify: `tzero_v3.py` / `addmcp.py` (`10.0.0` banner -> unified version), `README.md` / `pyproject.toml` cleanup if needed
- Remove dead/redundant legacy trees: `tzero/jarvis/` (empty duplicate superseded by `tzero_jarvis/`) and `vscode-extension/` (legacy v10.0.0 duplicate superseded by `extensions/vscode/`). (Note: `.vsix` files are gitignored; stale local `.vsix` binaries in `extensions/vscode/` and root can be cleaned or replaced when rebuilding `10.9.0.vsix`).
- Local-only (gitignored) fix: `enterprise_onprem/Dockerfile`, `enterprise_onprem/docker-compose.yml`, `tzero_gateway.py` (`TZERO_DATA_DIR=/app/data` support + full deps in `enterprise_onprem/Dockerfile`).

- [ ] **Step 1: Write test in `tests/test_packaging_sync.py`**
  Verify `.dockerignore` excludes `tzero-showcase/`, `extensions/`, `.tzero/`, `.tzero_cache.db`, and verify `tzero_jarvis.semantic_compressor` imports cleanly without relying on `tzero/`.
- [ ] **Step 2: Run test to verify it fails**
  Run: `python -m unittest tests.test_packaging_sync -v`
  Expected: FAIL on `.dockerignore` exclusions.
- [ ] **Step 3: Apply cleanup & fixes**
  - Update `.dockerignore` to exclude `tzero-showcase/`, `extensions/`, `.tzero/`, `.tzero_cache.db`, `scratch/`.
  - Fix `scripts/publish_vscode.ps1` to select `Sort-Object LastWriteTime -Descending | Select-Object -First 1`.
  - Remove dead `tzero/` and `vscode-extension/` (updating `pyproject.toml` `packages = ["tzero_jarvis", "tzero_fixer"]` and `MANIFEST.in` accordingly).
  - Fix local gitignored `enterprise_onprem/Dockerfile` + `tzero_gateway.py` (`TZERO_DATA_DIR`) so private gateway builds cleanly.
- [ ] **Step 4: Run full verification pipeline**
  Run:
  - `python -m unittest discover -s tests -p "test_*.py"`
  - `python tests/audit_secrets.py`
  - `node --test installers/npm/test/package.test.js`
  Expected: 100% PASS, `0` secret findings.
- [ ] **Step 5: Commit**
  ```bash
  git add -A
  git commit -m "chore(cleanup): tighten dockerignore, fix vsix publish sort, remove dead duplicates"
  ```

---

## Self-Review Check
- **Spec coverage:** Every Phase 1 runtime bug (`tzero_mcp.py`, `tzero_tui.py`, `tzero_v3.py`, `tzero_polyglot.py`), packaging gap (`pyproject.toml`, `installers/npm`, version drift), CI/Action/Docker defect (`action.yml`, `.dockerignore`, `enterprise_onprem/`, `publish_vscode.ps1`), and duplicate tree (`tzero/`, `vscode-extension/`) has an owning task.
- **Step scan:** Every task follows TDD (`RED -> verify fail -> GREEN -> verify pass -> commit`) with exact file paths, signatures, and commands.
- **Type consistency:** `PolyglotTokenReducer.reduce_code(raw_code, filename=full_p, mode="ultra")`, `query_memory_store(query, query_mode, project_root)`, and `manage_memory_store(operation, content, store_name, project_root)` match observed codebase signatures.
