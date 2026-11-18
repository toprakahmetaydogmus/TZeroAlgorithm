// SPDX-License-Identifier: AGPL-3.0-only
// Copyright (c) 2026 Toprak Ahmet Aydoğmuş
// Additional terms under AGPL-3.0 section 7: see NOTICE in the distribution
// or https://github.com/toprakahmetaydogmus/TZeroAlgorithm/blob/main/NOTICE.

const path = require("path");

/**
 * T-Zero Context Architect & MCP Server
 * https://github.com/toprakahmetaydogmus/TZeroAlgorithm
 */

module.exports = {
  version: require("./package.json").version,
  author: "Toprak Ahmet Aydoğmuş (Siber Akademi)",
  repository: "https://github.com/toprakahmetaydogmus/TZeroAlgorithm",
  srcDir: path.resolve(__dirname, "src"),
  mcpServer: path.resolve(__dirname, "src", "tzero", "tzero_mcp.py"),
  cli: path.resolve(__dirname, "src", "tzero", "tzero_v3.py")
};
