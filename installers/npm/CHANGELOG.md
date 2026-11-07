# Changelog

All notable changes to the `tzero-mcp` package are documented in this file.

## [10.9.0] - 2026-11-07

### Added
- Automated Architecture Guard Test Suite Generator (`tzero_arch_test.py` / `--generate-arch-tests` / `--check-arch`).
- Autonomous AST Mutation Testing & Test Quality Engine (`tzero_mutation.py` / `--mutate`).
- New MCP omni-tool workflow actions: `generate_architecture_tests`, `check_architecture`, `mutation_test`.
- Dashboard POST endpoint `/api/mutation/test`.

## [10.8.0] - 2026-11-07

### Added
- Dynamic Multi-Agent Swarm Coordinator & Shared Working Memory (`tzero_subagent_engine.py` / `tzero_blackboard.py`).
- Bidirectional Reverse Polyglot Type Transpiler (`tzero_bridge.py` / `--bridge-reverse`): TS/Rust/Go -> Python models.
- Semantic 3-Way AST Conflict Healer (`tzero_semantic_merge.py` / `--merge-heal`): Resolves git conflict markers on disjoint ASTs.
- Turbo Overdrive Burst Accelerator / Kamçılama Mode (`tzero_turbo.py` / `--turbo` / `--kamcilama`).
- VS Code & Cursor Extension official release (`tzero-vscode-10.8.0.vsix`).
- Sub-8ms multi-core AST response caching and adaptive latency sensing.

## [10.7.4] - 2026-11-07

### Added
- Multi-contributor transparency in package manifest.
- Comprehensive native test suite (`test/package.test.js`) verifying binary integrity and metadata.
- Full TypeScript definitions export (`index.d.ts`).
- Direct fallback detection for `PYTHON` environment variable in CLI launchers.

### Security & Supply Chain
- 100% Zero-Dependency architecture (0 production dependencies, 0 development dependencies).
- Zero lifecycle install scripts (removed postinstall hook for 100/100 Supply Chain score).
- Secure process spawning with explicit argument arrays and `{ shell: false }`.
- Complete bundled offline source code (`src/`).

## [10.7.3] - 2026-11-07
- Removed postinstall lifecycle script to eliminate supply chain flags.
- Switched launcher process execution from execSync to spawnSync with non-shell execution.
- Added native Node.js test suite.

## [10.7.2] - 2026-11-07
- Bundled full 98 Python source files in `src/`.
- Packaged all core T-Zero AST engines.

## [10.7.0] - 2026-11-07
- Initial release of T-Zero MCP Server on npm.
