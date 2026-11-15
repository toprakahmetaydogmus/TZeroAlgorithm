#!/usr/bin/env node

/**
 * T-Zero npm postinstall welcome & GitHub star prompt
 */

const isTest = process.env.TEST_POSTINSTALL === "1" || process.env.TZERO_FORCE_BANNER === "1";
const noBanner = !isTest && (process.env.TZERO_NO_BANNER === "1" || process.env.CI === "true" || process.env.npm_config_loglevel === "silent");

if (!noBanner) {
  console.log(`\x1b[36m
┌──────────────────────────────────────────────────────────────────────────────┐
│  ⚡ T-ZERO MCP INSTALLED SUCCESSFULLY!                                        │
├──────────────────────────────────────────────────────────────────────────────┤
│  ⭐ Star on GitHub: \x1b[33mhttps://github.com/toprakahmetaydogmus/TZeroAlgorithm\x1b[36m    │
│                                                                              │
│  💡 1-Click Setup:                                                           │
│     \x1b[37mnpx tzero-mcp --install\x1b[36m   Configure Cursor, Claude, Windsurf, VS Code    │
│     \x1b[37mnpx tzero --help\x1b[36m          View all CLI AST reduction commands           │
└──────────────────────────────────────────────────────────────────────────────┘
\x1b[0m`);
}
