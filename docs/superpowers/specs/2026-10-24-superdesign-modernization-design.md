# Design Document: Superdesign MCP Orchestrator & Modern Aesthetic Overhaul

**Date:** 2026-10-24  
**Status:** Under Review  
**Target Version:** v7.1.0 (with Superdesign Suite)  
**Author:** AI Agent (Antigravity) & Toprak Ahmet Aydoğmuş  

---

## 1. Intent & Context

The current repository presentation and web interfaces contain characteristics commonly perceived as "AI slop" — including an over-saturated neon cyberpunk color scheme (`#00ffd8`, `#ff2a85`), 12+ cluttered badge clusters in `README.md`, dense walls of emojis, outdated version tags (`v6.0/v6.1.0` instead of `v7.1.0`), and repetitive text.

The user has explicitly requested to:
1. Eliminate all "AI slop" across the GitHub documentation (`README.md`) and the application UI (`tzero_dashboard.py`, `benchmark-site`, HUD).
2. Integrate the **Superdesign MCP Server** specification natively into T-Zero, bringing 5 design orchestrator tools (`superdesign_generate`, `superdesign_iterate`, `superdesign_extract_system`, `superdesign_list`, `superdesign_gallery`).
3. Apply the Superdesign token-based system to overhaul the project's own interfaces into a clean, modern, enterprise-grade developer tool (Linear/Vercel/Stripe standard).
4. Maintain 100% test pass rate, TDQS 5.0/5.0 Anchor certification, 100% offline execution, and 100% Zero-Leak security.

---

## 2. Goals, Non-Goals & Anti-Goals

### Goals
- **Native Superdesign Tools**: Implement `tzero_superdesign.py` implementing all 5 Superdesign orchestrator tools.
- **MCP Server Registration**: Register all 5 tools on `tzero_mcp.py` with Anchor-5 TDQS formatting, expanding the server from 42 to 47 specialized tools.
- **GitHub Page Modernization**: Rewrite `README.md` to be crisp, modern, elegant, and accurately reflecting `v7.1.0`, 47 tools, 207+ tests, and 95% token savings without emoji walls.
- **Application UI Overhaul**: Re-theme `tzero_dashboard.py` and `tzero_graph_hud.html` with a modern slate/zinc dark aesthetic, refined typography (Geist/Inter/Fira Code), clean card structures, and responsive layouts.
- **Design System Extraction**: Seed `superdesign/design_system/tzero_design_system.json` representing T-Zero's new design tokens (color palette, typography, radii, elevation, spacing).
- **Automated Verification**: Add comprehensive unit tests in `tests/test_superdesign.py` ensuring 100% pass rate.

### Non-Goals
- Modifying core AST pruning algorithms or token reduction calculations in `tzero_v3.py` or `tzero_polyglot.py`.
- Breaking backward compatibility with any of the existing 42 MCP tools.
- Adding mandatory external cloud or npm dependencies (the Python-based Superdesign orchestrator runs zero-install locally).

### Anti-Goals
- Tacky, high-saturation neon cyberpunk aesthetics or generic generative AI templates.
- Any hardcoded API keys, personal credentials, or email leaks (strict Zero-Leak policy).
- Incomplete mock tools that fail when called by MCP clients.

---

## 3. Approaches Considered & Tradeoffs

### Approach 1: Native Superdesign Suite & Token-Driven Overhaul (Selected)
- **Description**: Implement `tzero_superdesign.py` directly in Python, expose the 5 tools in `tzero_mcp.py`, generate a formal design system in `superdesign/`, and modernize `README.md` and `tzero_dashboard.py` using these tokens.
- **Pros**:
  - Unifies context architecture and design orchestration under one zero-dependency MCP server.
  - Zero npm/node requirement for end-users — runs seamlessly with `uvx tzero-mcp` or `pip install tzero-mcp`.
  - T-Zero's own UI directly dogfoods its new Superdesign system.
- **Cons**: Requires rewriting the dashboard CSS and refactoring `README.md`.

### Approach 2: Standalone npm Package / Surface Re-skin
- **Description**: Keep Superdesign as an external Node.js repository and only edit CSS in T-Zero.
- **Why Rejected**: Fails the user's explicit requirement ("bu projerdeki mcp yi kullanarak yap tasarımlarını vs. hepsini bu projedeki gibi yap adam gibi olsun").

---

## 4. Architectural & Implementation Details

### A. Superdesign Module (`tzero_superdesign.py`)
Provides the 5 orchestrator tools:
1. `superdesign_generate(prompt: str, design_type: str, variations: int = 3, framework: str = "html") -> Dict[str, Any]`
   - Formats comprehensive prompt specifications for UI, Wireframe, Component, Logo (SVG), or Icon (SVG).
   - Generates recommended output file paths in `superdesign/design_iterations/`.
2. `superdesign_iterate(design_file: str, feedback: str, variations: int = 1) -> Dict[str, Any]`
   - Reads the target file and produces structured feedback execution instructions preserving design coherence.
3. `superdesign_extract_system(input_path_or_description: str, system_name: str = "custom") -> Dict[str, Any]`
   - Extracts or initializes a design token schema (colors, typography, spacing, shadows, radius) and saves to `superdesign/design_system/<name>.json`.
4. `superdesign_list(workspace_path: str = ".") -> Dict[str, Any]`
   - Discovers all iterations (`.html`, `.svg`, `.tsx`, `.jsx`) in `superdesign/design_iterations/` and systems in `superdesign/design_system/`.
5. `superdesign_gallery(workspace_path: str = ".") -> Dict[str, Any]`
   - Builds an interactive, responsive HTML gallery (`superdesign/gallery.html`) showcasing all iterations with live preview cards, modal zoom, code copy, and theme switching.

### B. MCP Server Registration (`tzero_mcp.py`)
- Register all 5 tools using `@server.tool` with Anchor-5 TDQS standard.
- Update `_CANONICAL_DISPATCH` to support dynamic fallback and canonical execution.
- Update total tool count from 42 to 47.

### C. Modernized GitHub README (`README.md`)
- Clean, focused hero section: minimalist typography, curated status badges (PyPI, CI, License, MCP).
- Interactive quickstarts with copyable tabs (`uvx`, `pip`, `docker`).
- Clear visual proof table (reproducible token reduction: 166k -> 8.4k, -94.9%).
- Superdesign MCP section with complete tool descriptions, parameters, and workflow examples.
- Clean system architecture ASCII/Mermaid diagram.

### D. Modernized Application UI (`tzero_dashboard.py` & `tzero_graph_hud.html`)
- Palette:
  - Surface: Slate-950 (`#090d16`) / Slate-900 (`#0f172a`)
  - Border: Subtle Slate-800 (`#1e293b`) / Focus Indigo-500 (`#6366f1`)
  - Accent: Sky-400 (`#38bdf8`) / Emerald-400 (`#34d399`)
  - Typography: Inter & Fira Code monospace.
- Eliminate neon glows and noisy scanlines.
- Elevate data visualizations, memory inspector, and consensus radar into crisp, readable cards.

---

## 5. Verification Plan

1. **Unit Testing**:
   - Create `tests/test_superdesign.py` testing generation specs, iteration instructions, system extraction, workspace listing, and gallery HTML generation.
   - Run `python -m unittest discover tests -v` to ensure all 207+ tests pass.
2. **MCP Validation**:
   - Verify server initialization and tool registration (47 tools active).
   - Test `superdesign_generate` and `superdesign_gallery` output correctness.
3. **Security Audit**:
   - Scan modified files with `tzero_guard.py` ensuring zero leaked credentials or personal emails.
4. **Visual & Aesthetic Review**:
   - Inspect generated `superdesign/gallery.html` and updated `tzero_dashboard.py` in browser.
