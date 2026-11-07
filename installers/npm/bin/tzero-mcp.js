#!/usr/bin/env node

/**
 * T-Zero Model Context Protocol (MCP) Server Launcher
 * Author: Toprak Ahmet Aydoğmuş (15-Year-Old Solo Developer @ Siber Akademi)
 * Repository: https://github.com/toprakahmetaydogmus/TZeroAlgorithm
 */

const { spawn, execSync } = require("child_process");
const process = require("process");

// In MCP mode, banner is printed to stderr to keep stdout strictly for JSON-RPC
const banner = `\x1b[33m
┌──────────────────────────────────────────────────────────────────────────────┐
│  ⭐ T-ZERO MCP SERVER v10.7.0 (Model Context Protocol)                       │
│                                                                              │
│  Hi! I'm Toprak Ahmet Aydoğmuş, a 15-year-old developer from Siber Akademi. │
│  If this tool helps you, please star:                                        │
│  👉 https://github.com/toprakahmetaydogmus/TZeroAlgorithm                    │
└──────────────────────────────────────────────────────────────────────────────┘
\x1b[0m`;

if (process.stderr.isTTY) {
  process.stderr.write(banner + "\n");
}

function findPython() {
  const candidates = ["python3", "python", "py"];
  for (const cmd of candidates) {
    try {
      execSync(`${cmd} --version`, { stdio: "ignore" });
      return cmd;
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

// Ensure tzero_mcp module is installed in this python environment
try {
  execSync(`${py} -c "import tzero_mcp"`, { stdio: "ignore" });
} catch (e) {
  if (process.stderr.isTTY) {
    process.stderr.write("\x1b[36m[T-Zero] First-time setup: installing tzero-mcp from PyPI...\x1b[0m\n");
  }
  try {
    execSync(`${py} -m pip install -U tzero-mcp`, { stdio: "inherit" });
  } catch (err) {
    console.error("\x1b[31m[ERROR] Failed to auto-install tzero-mcp. Please run: pip install -U tzero-mcp\x1b[0m");
    process.exit(1);
  }
}

const args = ["-m", "tzero_mcp", ...process.argv.slice(2)];
const child = spawn(py, args, { stdio: "inherit" });

child.on("close", (code) => {
  process.exit(code ?? 0);
});

