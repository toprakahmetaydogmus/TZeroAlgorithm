# T-Zero v11 Phase 3 Implementation Plan: Core AST Precision, `tiktoken` BPE, KV-Cache Alignment & Incremental SQLite/Git Snapshots

> **For agentic workers:** Execute via strict TDD (`RED -> verify fail -> GREEN -> verify pass -> commit`), keeping 100% offline/free guarantees and 100% Zero-Leak security. Run `python tests/audit_secrets.py` and targeted `unittest` checks after every task.

**Goal:** Eliminate heuristic approximations and stale-cache bottlenecks in T-Zero's core context engine by wiring real `tiktoken` BPE token counting, `--cache-aligned` KV-cache prefix-stable packing, a unified string/comment/brace-aware polyglot + optional `tree-sitter` + cAST chunking engine (differentiating `T-2` `light` vs `T-3` `ultra`), and multi-language incremental SQLite + `git diff` snapshots and file watching.

**Architecture:** All changes remain 100% local and zero-dependency-safe (`tiktoken` is used when installed with instant regex/char fallback; `tree-sitter` is cleanly optional via `try/except ImportError` atop a zero-dep structural parser; SQLite uses Python stdlib `sqlite3`). Layer boundaries remain inward-only.

**Tech Stack:** Python (`tiktoken`, stdlib `sqlite3`, `ast`, `subprocess`/`git`), optional `tree_sitter`.

---

### Task 1: Real `tiktoken` BPE Tokenization (`tzero_v3.count_tokens_precise` & `TokenBudgetPacker`)

**Files:**
- Modify: `tzero_v3.py` (`count_tokens_precise`, lines 2689+)
- Modify: `tzero_packer.py` (`TokenBudgetPacker.estimate_tokens`, lines 62-71)
- Modify: `tests/test_generator.py` (`test_count_tokens_precise`, lines 25-30)
- Modify: `tests/test_packer.py` (`test_estimate_tokens`, lines 59-64)

**TDD Plan:**
1. Update `tests/test_generator.py` and `tests/test_packer.py` first:
   - `test_count_tokens_precise`: verify `count_tokens_precise(text, "gpt-4o")` and `count_tokens_precise(text, "deepseek-ai/deepseek-v4.1-flash")` use `tiktoken` BPE counts (cached encoding) when available, AND test mocking `tiktoken = None` / unavailable encoding cleanly falls back to `max(1, len(text) // 4)`.
   - `test_estimate_tokens_uses_bpe_with_fallback`: verify `TokenBudgetPacker.estimate_tokens(text)` returns exact BPE token count matching `o200k_base` / `cl100k_base` when `tiktoken` is loaded, plus empty string -> `0`, non-empty -> `>= 1`.
2. Run `python -m unittest tests.test_generator tests.test_packer -v` and confirm **RED**.
3. Implement cached `_get_bpe_encoding(model_name)` in `tzero_v3.py` mapping `gpt-4o`/`o1`/`o3`/`o4`/`gpt-5`/`gemini`/`deepseek` -> `o200k_base` and `claude`/`gpt-3.5`/`gpt-4-turbo`/`llama` -> `cl100k_base`, and wire `TokenBudgetPacker.estimate_tokens` to reuse `count_tokens_precise` (with fast fallback if `tiktoken` missing).
4. Run `python -m unittest tests.test_generator tests.test_packer -v`, sync npm sources, run `tests/audit_secrets.py`, commit.

---

### Task 2: KV-Cache Prefix Alignment (`--cache-aligned`), `RepositoryPageRank` Budget Uncap & `T-2` vs `T-3` Differentiation

**Files:**
- Modify: `tzero_v3.py` (`generate_offline_context`, `--cache-aligned` CLI flag wiring)
- Modify: `tzero_packer.py` (`TokenBudgetPacker.scan_workspace`, `pack`, `render_bundle_markdown`, `pack_workspace`)
- Modify: `tests/test_packer.py` & `tests/test_generator.py`

**TDD Plan:**
1. Add failing tests:
   - `tests/test_packer.py`: `test_cache_aligned_prefix_stability`: packing the same workspace with two DIFFERENT `focus` / query strings and `cache_aligned=True` produces an IDENTICAL byte prefix up to `<!-- TZERO_DYNAMIC_SUFFIX -->` (static project tree, dependencies, rules, and PageRank-sorted cold modules first; volatile focus/query summary placed at the suffix for LLM prompt-cache hits!).
   - `tests/test_packer.py`: `test_scan_workspace_uncapped_prioritizes_important_files`: with >150 files (e.g., 170 small dummy `.py` files + a central imported `core_engine.py`), `scan_workspace(..., max_files=None)` / `pack_workspace` retains `core_engine.py` via `RepositoryPageRank` instead of dropping after 150 `os.walk` entries.
   - `tests/test_packer.py`: `test_t2_light_differs_from_t3_ultra`: verify `T-2` (`light`) retains docstrings/type metadata while `T-3` (`ultra`) strips comments/docstrings cleanly.
2. Run tests -> confirm **RED**.
3. Implement `cache_aligned: bool = False` in `generate_offline_context` and `TokenBudgetPacker.pack` / `render_bundle_markdown` / `pack_workspace` + `--cache-aligned` CLI flag in `tzero_v3.py` + unlimited / PageRank-ranked discovery (`max_files: Optional[int] = None` with smart default priority sort).
4. Run `python -m unittest tests.test_packer tests.test_generator tests.test_cli -v`, verify **GREEN**, commit.

---

### Task 3: Unified Polyglot Engine, String/Comment/Brace cAST Chunker & Optional `tree-sitter` Adapter

**Files:**
- Modify: `tzero_polyglot.py` (stateful lexer/brace-depth signature extractor + `mode="light"` vs `mode="ultra"` differentiation + `try_tree_sitter_reduce` / `cast_chunk_code` semantic AST chunker)
- Modify: `tzero_v3.py` (`PolyglotSignatureExtractor` delegates cleanly to unified `PolyglotTokenReducer`, eliminating duplicated TS/Go/Rust/Java/C#/C++ logic)
- Modify: `tests/test_polyglot.py`, `tests/test_polyglot_engine.py`

**TDD Plan:**
1. Add failing tests in `tests/test_polyglot_engine.py` & `tests/test_polyglot.py`:
   - `test_multiline_signature_and_braces_in_strings`: TS/Rust/Go/Java methods whose bodies contain `{` or `}` inside string literals/comments (`const s = "{ not a close brace }";`) and multiline parameter lists preserve the full signature and prune ONLY the balanced body!
   - `test_light_vs_ultra_mode_difference`: non-Python files (`.ts`, `.rs`, `.go`) preserve doc-comments/docstrings in `mode="light"` and strip them cleanly in `mode="ultra"`.
   - `test_cast_chunk_code_boundaries`: `PolyglotTokenReducer.chunk_code(code, filename, max_chunk_tokens=120)` splits along AST declaration boundaries instead of cutting mid-function.
   - `test_optional_tree_sitter_hook`: mock/plug custom parser or verify clean fallback when `tree_sitter` is unavailable (`None`).
2. Run `python -m unittest tests.test_polyglot tests.test_polyglot_engine -v` -> confirm **RED**.
3. Implement unified lexer + balanced-brace/indent block reducer + `cast_chunk_code` + optional `tree_sitter` hook in `tzero_polyglot.py`, and delegate `PolyglotSignatureExtractor.extract` cleanly in `tzero_v3.py`.
4. Run `python -m unittest tests.test_polyglot tests.test_polyglot_engine -v` -> verify **GREEN**, commit.

---

### Task 4: Incremental Multi-Language SQLite Snapshot Engine & `git diff` Watcher (`tzero_snapshot.py`, `tzero_v3.py`)

**Files:**
- Modify: `tzero_snapshot.py` (`SnapshotEngine`: multi-language file discovery via `should_skip_dir`/`should_skip_file` + `PolyglotTokenReducer`, SQLite `.tzero/snapshot.db` backend alongside backward-compatible `.tzero/snapshot.json`, incremental `update_incremental(workspace_dir, changed_files=None)` using `git diff --name-only` + `mtime_ns`/SHA-256)
- Modify: `tzero_v3.py` (`run_watch_mode`: incremental single-file re-index on `mtime_ns` delta + SnapshotEngine SQLite sync)
- Modify: `tests/test_new_features.py` & create `tests/test_snapshot_incremental.py`

**TDD Plan:**
1. Write failing tests in `tests/test_snapshot_incremental.py`:
   - `test_multi_language_snapshot_and_sqlite_store`: workspace with `.py`, `.ts`, `.rs`, `.go` creates `.tzero/snapshot.db` (SQLite) + `SnapshotResult` indexing all 4 files (not just `.py`!).
   - `test_incremental_update_reuses_unchanged_files`: modify only 1 file (`mtime_ns` + content hash change) -> `update_incremental` re-parses ONLY that 1 file while keeping cached tokens for untouched files (verified via call counter / spy).
   - `test_is_valid_detects_change_beyond_first_15_files`: create 20 `.py` files and mutate the 20th file (`file_19.py`) -> `is_valid()` MUST return `False` (fixes the old spot-check of only `[:15]`!).
   - `test_incremental_deletion_removes_stale_entry`: deleting a tracked file prunes it cleanly on incremental update.
2. Run `python -m unittest tests.test_snapshot_incremental tests.test_new_features tests.test_cli.TestCLI.test_watch_mode -v` -> confirm **RED**.
3. Upgrade `tzero_snapshot.py` & `run_watch_mode` (`tzero_v3.py`).
4. Verify **GREEN**, sync npm sources, audit secrets, commit, and run Phase 3 `sdd-reviewer` gate.

