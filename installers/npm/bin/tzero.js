#!/usr/bin/env node

/**
 * T-Zero Context Architect CLI Launcher
 * Author: Toprak Ahmet Aydoğmuş (15-Year-Old Solo Developer @ Siber Akademi)
 * Repository: https://github.com/toprakahmetaydogmus/TZeroAlgorithm
 */

const { spawn, execSync } = require("child_process");
const process = require("process");

const banner = `\x1b[33m
┌──────────────────────────────────────────────────────────────────────────────┐
│  ⭐ T-ZERO CONTEXT ARCHITECT & MCP ENGINE v10.7.0                            │
│                                                                              │
│  Hi! I'm Toprak Ahmet Aydoğmuş, a 15-year-old developer from Siber Akademi. │
│  I built T-Zero from scratch to eliminate token bloat and AI hallucinations. │
│                                                                              │
│  If this tool saves you tokens, please give us a ⭐ on GitHub:              │
│  👉 https://github.com/toprakahmetaydogmus/TZeroAlgorithm                    │
└──────────────────────────────────────────────────────────────────────────────┘
\x1b[0m`;

if (process.stdout.isTTY && !process.argv.includes("--json") && !process.argv.includes("--pipe")) {
  console.log(banner);
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

const path = require("path");
const py = findPython();
if (!py) {
  console.error("\x1b[31m[ERROR] Python 3.10+ is required to run T-Zero.\x1b[0m");
  console.error("Please install Python from https://python.org or your package manager.");
  process.exit(1);
}

const srcDir = path.resolve(__dirname, "..", "src");
const scriptPath = path.join(srcDir, "tzero_v3.py");

const env = Object.assign({}, process.env, {
  PYTHONPATH: srcDir + (process.env.PYTHONPATH ? path.delimiter + process.env.PYTHONPATH : "")
});

const args = [scriptPath, ...process.argv.slice(2)];
const child = spawn(py, args, { stdio: "inherit", env });

child.on("close", (code) => {
  process.exit(code ?? 0);
});

