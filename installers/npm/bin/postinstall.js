#!/usr/bin/env node

/**
 * T-Zero Post-Install Banner & Star Request
 * Author: Toprak Ahmet Aydoğmuş (15-Year-Old Solo Developer @ Siber Akademi)
 * Repository: https://github.com/toprakahmetaydogmus/TZeroAlgorithm
 */

const isCI = process.env.CI || process.env.CONTINUOUS_INTEGRATION;
if (!isCI) {
  const cyan = "\x1b[36m";
  const yellow = "\x1b[33m";
  const green = "\x1b[32m";
  const bold = "\x1b[1m";
  const reset = "\x1b[0m";

  console.log(`
${yellow}┌──────────────────────────────────────────────────────────────────────────────┐
│  ${bold}${green}⚡ T-ZERO CONTEXT ARCHITECT & MCP SERVER INSTALLED SUCCESSFULLY!${reset}${yellow}            │
│                                                                              │
│  Hi! I'm ${bold}Toprak Ahmet Aydoğmuş${reset}${yellow}, a 15-year-old solo developer from         │
│  ${bold}Siber Akademi${reset}${yellow}. I built T-Zero from scratch to eliminate token bloat and    │
│  AI coding hallucinations using deterministic AST analysis.                  │
│                                                                              │
│  ⭐ ${bold}If T-Zero saves you tokens or helps your AI workflows,${reset}${yellow}                 │
│     ${bold}${cyan}please give our repository a STAR on GitHub:${reset}${yellow}                            │
│                                                                              │
│  👉 ${bold}${cyan}https://github.com/toprakahmetaydogmus/TZeroAlgorithm${reset}${yellow}                    │
│                                                                              │
│  Every star means the world to a young open-source creator! 🚀 Thank you!    │
└──────────────────────────────────────────────────────────────────────────────┘${reset}
`);
}
process.exit(0);
