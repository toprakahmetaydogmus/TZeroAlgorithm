# Superdesign Modernization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate the 5 Superdesign MCP orchestrator tools into T-Zero natively, expand to 47 Anchor-5 certified tools, and completely eliminate "AI slop" across `README.md` and the application dashboard using clean modern design tokens.

**Architecture:** Implement `tzero_superdesign.py` as a zero-dependency orchestrator producing structured UI/component/system specifications and interactive HTML galleries. Expose these tools via `tzero_mcp.py` with Anchor-5 TDQS standards. Apply the resulting design tokens to transform `README.md` (clean typography, curated badges, accurate v7.1.0 metrics) and `tzero_dashboard.py` (slate-950 dark theme, Inter/Geist fonts, glassmorphism).

**Tech Stack:** Python 3.10+, Model Context Protocol (MCP) SDK, HTML5 / Vanilla CSS3 / SVG, unittest.

**Spec:** [docs/superpowers/specs/2026-10-24-superdesign-modernization-design.md](file:///C:/Users/topra_n3vq63d/.gemini/antigravity-ide/scratch/TZeroAlgorithm/docs/superpowers/specs/2026-10-24-superdesign-modernization-design.md)

## Global Constraints

- 100% Zero-Leak Guarantee: strictly zero hardcoded personal emails, API keys, or credentials.
- 100% Offline execution: zero external runtime npm or cloud requirements for the Superdesign orchestrator.
- TDQS 5.0/5.0 Anchor certification: all 5 new MCP tools must have typed fields, comprehensive docstrings with `Behavior:`, `Usage Guidelines:`, and `Returns:`.
- 100% Test pass rate: all existing 207 tests plus new Superdesign tests must pass.
- Version consistency: `v7.1.0` with 47 specialized tools everywhere.

## Review Focus

1. `superdesign_generate` invalid design type: must raise clear `ValueError` or return structured error guidance without crashing.
2. `superdesign_iterate` non-existent design file: gracefully report missing file and provide recovery suggestions.
3. `superdesign_extract_system` schema compliance: output JSON must validate against standard design tokens schema (colors, typography, spacing).
4. `superdesign_gallery` empty workspace directory: generate a clean empty-state gallery rather than throwing filesystem errors.
5. Windows file path handling: ensure all generated iteration and gallery paths use normalized paths safe across Windows and POSIX.

---

### Task 1: Superdesign Orchestrator Core Module (`tzero_superdesign.py`)

**Files:**
- Create: `tzero_superdesign.py`
- Create: `tests/test_superdesign.py`

**Interfaces:**
- Produces:
  - `superdesign_generate(prompt: str, design_type: str, variations: int = 3, framework: str = "html") -> Dict[str, Any]`
  - `superdesign_iterate(design_file: str, feedback: str, variations: int = 1) -> Dict[str, Any]`
  - `superdesign_extract_system(input_path_or_description: str, system_name: str = "custom", workspace_path: str = ".") -> Dict[str, Any]`
  - `superdesign_list(workspace_path: str = ".") -> Dict[str, Any]`
  - `superdesign_gallery(workspace_path: str = ".") -> Dict[str, Any]`

- [ ] **Step 1: Write failing unit tests in `tests/test_superdesign.py`**
  Cover generation specs for ui/component/logo, iteration instructions, design system extraction schema, listing, and gallery HTML generation.

- [ ] **Step 2: Run test to verify it fails**
  Run: `python -m unittest tests/test_superdesign.py -v`
  Expected: FAIL with `ModuleNotFoundError: No module named 'tzero_superdesign'`

- [ ] **Step 3: Implement `tzero_superdesign.py`**
  Implement the 5 orchestrator functions, Superdesign system prompts, file path generators, JSON schema validators, and interactive responsive gallery builder.

- [ ] **Step 4: Run test to verify it passes**
  Run: `python -m unittest tests/test_superdesign.py -v`
  Expected: PASS

- [ ] **Step 5: Commit**
  Run: `git add tzero_superdesign.py tests/test_superdesign.py; git commit -m "feat(superdesign): add native superdesign orchestrator module and tests"`

---

### Task 2: Register Superdesign Tools in T-Zero MCP Server (`tzero_mcp.py`)

**Files:**
- Modify: `tzero_mcp.py:40-120,3000-3137`
- Test: `tests/test_superdesign.py`

**Interfaces:**
- Consumes: `tzero_superdesign` functions from Task 1.
- Produces: 5 new `@server.tool` registrations with Anchor-5 TDQS formatting, raising total tools from 42 to 47.

- [ ] **Step 1: Add MCP tool tests for Superdesign tools in `tests/test_superdesign.py`**
  Verify tools can be called directly and return valid JSON structures conforming to Anchor-5 schema.

- [ ] **Step 2: Run test to verify failure**
  Run: `python -m unittest tests/test_superdesign.py -v`

- [ ] **Step 3: Register tools in `tzero_mcp.py`**
  Add `@server.tool` definitions for `superdesign_generate`, `superdesign_iterate`, `superdesign_extract_system`, `superdesign_list`, and `superdesign_gallery` with typed annotations and field descriptions.

- [ ] **Step 4: Run tests to verify pass**
  Run: `python -m unittest tests/test_superdesign.py -v`
  Expected: PASS

- [ ] **Step 5: Commit**
  Run: `git add tzero_mcp.py tests/test_superdesign.py; git commit -m "feat(mcp): register 5 superdesign orchestrator tools (47 total tools)"`

---

### Task 3: Modernize Web Dashboard & Visualizer (`tzero_dashboard.py`, `tzero_graph_hud.html`)

**Files:**
- Modify: `tzero_dashboard.py`
- Modify: `tzero_graph_hud.html`

**Interfaces:**
- Consumes: Superdesign design tokens (`tzero_design_system.json`).
- Produces: Slate-950 dark theme, Inter/Geist fonts, refined card elevations, crisp borders, zero neon glare.

- [ ] **Step 1: Write test for dashboard HTML asset rendering**
  Verify dashboard HTML serves clean CSS variables and valid HTML structure.

- [ ] **Step 2: Overhaul `tzero_dashboard.py` and `tzero_graph_hud.html`**
  Replace neon `#00ffd8` and `#ff2a85` with modern slate/zinc tokens (`#090d16`, `#0f172a`, `#1e293b`, `#38bdf8`, `#818cf8`), clean typography, and remove "AI slop" headers.

- [ ] **Step 3: Verify dashboard launches and serves without error**
  Run: `python -c "import tzero_dashboard; print('Dashboard syntax OK')"`
  Expected: PASS

- [ ] **Step 4: Commit**
  Run: `git add tzero_dashboard.py tzero_graph_hud.html; git commit -m "style(dashboard): modernize UI into slate dark theme with Superdesign tokens"`

---

### Task 4: Modernize GitHub Documentation (`README.md`, `benchmark-site/index.html`)

**Files:**
- Modify: `README.md`
- Modify: `benchmark-site/index.html`

**Interfaces:**
- Produces: Professional, developer-first documentation reflecting `v7.1.0`, 47 tools, 207+ tests, Superdesign orchestrator guide, zero badge spam, zero emoji walls.

- [ ] **Step 1: Rewrite `README.md`**
  - Sleek hero with concise value proposition (up to 95% token savings).
  - Clean badge line: PyPI v7.1.0, CI 207+ passing, License MIT, 47 MCP Tools.
  - Quickstart tabs: `uvx tzero-mcp`, `pip install tzero-mcp`.
  - Superdesign section: full usage guide for `superdesign_*` tools.
  - Complete tool table with all 47 tools categorized.
  - Eliminate repetitive marketing walls and emoji overload.

- [ ] **Step 2: Update `benchmark-site/index.html`**
  Update version references to `v7.1.0` and tool counts to 47 tools.

- [ ] **Step 3: Verify markdown formatting and anchor links**
  Ensure all links are valid and no formatting errors exist.

- [ ] **Step 4: Commit**
  Run: `git add README.md benchmark-site/index.html; git commit -m "docs: modernize README and benchmark site without AI slop"`

---

### Task 5: Zero-Leak Security Audit, Full Test Suite Verification & Push

**Files:**
- Verify: all repo files
- Test: all 207+ tests

- [ ] **Step 1: Run zero-leak security audit**
  Run: `python tzero_guard.py .`
  Expected: 100% PASS, 0 hardcoded secrets or credentials.

- [ ] **Step 2: Run complete test suite**
  Run: `python -m unittest discover tests -v`
  Expected: 100% PASS (212+ tests).

- [ ] **Step 3: Push commit and tag to origin main**
  Run: `git push origin main`
