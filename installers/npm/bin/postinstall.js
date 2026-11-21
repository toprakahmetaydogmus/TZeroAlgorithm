#!/usr/bin/env node

/**
 * T-Zero npm postinstall welcome & GitHub star prompt
 */

const pkg = require("../package.json");
const isTest = process.env.TEST_POSTINSTALL === "1" || process.env.TZERO_FORCE_BANNER === "1";
const noBanner = !isTest && (process.env.TZERO_NO_BANNER === "1" || process.env.CI === "true" || process.env.npm_config_loglevel === "silent");

if (!noBanner) {
  console.log(`\x1b[36m
┌──────────────────────────────────────────────────────────────────────────────┐
│  ⚡ T-ZERO MCP INSTALLED SUCCESSFULLY! (v${pkg.version})                               │
├──────────────────────────────────────────────────────────────────────────────┤
│  ⭐ \x1b[1;33mHELP US REACH OUR 100 STARS GOAL (Current: 45 / 100):\x1b[0m\x1b[36m                   │
│     \x1b[1;32m► Run: npx tzero star  OR  visit: https://github.com/toprakahmetaydogmus/TZeroAlgorithm\x1b[0m\x1b[36m │
│                                                                              │
│  💖 \x1b[1;35mSPONSOR & KEEP T-ZERO 100% FREE:\x1b[0m\x1b[36m                                        │
│     \x1b[1;32m► https://github.com/sponsors/toprakahmetaydogmus\x1b[0m\x1b[36m                        │
│                                                                              │
│  🎉 20,880+ Downloads across PyPI & npm! 100% Free & Open Source (AGPL-3.0)  │
│                                                                              │
│  💡 1-Click Setup:                                                           │
│     \x1b[37mnpx tzero-mcp --install\x1b[36m   Configure Cursor, Claude, Windsurf, VS Code    │
│     \x1b[37mnpx tzero roi\x1b[36m             View live token & dollar ($) savings           │
│     \x1b[37mnpx tzero --help\x1b[36m          View all CLI AST reduction commands           │
└──────────────────────────────────────────────────────────────────────────────┘
\x1b[0m`);
}
