# Changelog

All notable changes to the `tzero-mcp` package are documented in this file.

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
