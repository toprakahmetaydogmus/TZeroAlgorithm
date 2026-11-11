#!/usr/bin/env node

/**
 * T-Zero Model Context Protocol (MCP) Server Launcher
 * Author: Toprak Ahmet Aydoğmuş (Siber Akademi)
 * Repository: https://github.com/toprakahmetaydogmus/TZeroAlgorithm
 */

const { spawn, spawnSync } = require("child_process");
const process = require("process");
const path = require("path");
const pkg = require("../package.json");

// In MCP mode, banner is printed to stderr to keep stdout strictly for JSON-RPC
const banner = `\x1b[36m
┌──────────────────────────────────────────────────────────────────────────────┐
│  ⚡ T-ZERO MCP SERVER v${pkg.version} (Model Context Protocol)                       │
│  Enterprise AST Context Compressor, Zero-Leak Guard & 20 Canonical Tools     │
│                                                                              │
│  ⭐ Star on GitHub: https://github.com/toprakahmetaydogmus/TZeroAlgorithm    │
│  🔌 Connected to:   Cursor, Claude Desktop, Antigravity, Windsurf & Cline    │
└──────────────────────────────────────────────────────────────────────────────┘
\x1b[0m`;

if (process.stderr.isTTY) {
  process.stderr.write(banner + "\n");
}

function findPython() {
  if (process.env.PYTHON) return process.env.PYTHON;
  const candidates = ["python3", "python", "py"];
  for (const cmd of candidates) {
    try {
      const res = spawnSync(cmd, ["--version"], { stdio: "ignore", shell: false });
      if (res.status === 0) return cmd;
    } catch (e) {
      // continue
    }
  }
  return null;
}

const py = findPython();
if (!py) {
  console.error("\x1b[31m[ERROR] Python 3.10+ is required to run T-Zero MCP Server.\x1b[0m");
  console.error("Please install Python from https://python.org or your package manager.");
  process.exit(1);
}

const srcDir = path.resolve(__dirname, "..", "src");
const scriptPath = path.join(srcDir, "tzero", "tzero_mcp.py");

const env = Object.assign({}, process.env, {
  PYTHONPATH: srcDir + (process.env.PYTHONPATH ? path.delimiter + process.env.PYTHONPATH : "")
});

const args = [scriptPath, ...process.argv.slice(2)];
const child = spawn(py, args, { stdio: "inherit", shell: false, env });

child.on("close", (code) => {
  process.exit(code ?? 0);
});
