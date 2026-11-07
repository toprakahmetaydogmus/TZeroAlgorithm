const path = require("path");

/**
 * T-Zero Context Architect & MCP Server
 * https://github.com/toprakahmetaydogmus/TZeroAlgorithm
 */

module.exports = {
  version: "10.7.2",
  author: "Toprak Ahmet Aydoğmuş (Siber Akademi)",
  repository: "https://github.com/toprakahmetaydogmus/TZeroAlgorithm",
  srcDir: path.resolve(__dirname, "src"),
  mcpServer: path.resolve(__dirname, "src", "tzero_mcp.py"),
  cli: path.resolve(__dirname, "src", "tzero_v3.py")
};
