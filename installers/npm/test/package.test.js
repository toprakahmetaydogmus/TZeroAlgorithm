const test = require("node:test");
const assert = require("node:assert");
const path = require("node:path");
const fs = require("node:fs");
const tzero = require("../index.js");
const pkg = require("../package.json");

test("package.json metadata integrity", () => {
  assert.strictEqual(pkg.name, "tzero-mcp");
  assert.strictEqual(pkg.license, "MIT");
  assert.strictEqual(typeof pkg.version, "string");
  assert.strictEqual(pkg.bin["tzero"], "bin/tzero.js");
  assert.strictEqual(pkg.bin["tzero-mcp"], "bin/tzero-mcp.js");
});

test("tzero package exports correct properties", () => {
  assert.strictEqual(typeof tzero.version, "string");
  assert.strictEqual(typeof tzero.author, "string");
  assert.strictEqual(typeof tzero.repository, "string");
  assert.strictEqual(typeof tzero.srcDir, "string");
  assert.strictEqual(typeof tzero.mcpServer, "string");
  assert.strictEqual(typeof tzero.cli, "string");
});

test("tzero core python files exist in srcDir", () => {
  assert.strictEqual(fs.existsSync(tzero.mcpServer), true);
  assert.strictEqual(fs.existsSync(tzero.cli), true);
  const coreFiles = [
    "tzero_v3.py",
    "tzero_mcp.py",
    "tzero_security.py",
    "tzero_deps.py",
    "tzero_polyglot.py",
    "tzero_arch_test.py",
    "tzero_budget.py",
    "tzero_contracts.py",
    "tzero_debt.py",
    "tzero_golden.py",
    "tzero_mutation.py"
  ];
  for (const f of coreFiles) {
    assert.strictEqual(fs.existsSync(path.join(tzero.srcDir, f)), true, `Expected ${f} to exist`);
  }
});

test("package documentation and binaries exist", () => {
  const root = path.resolve(__dirname, "..");
  assert.strictEqual(fs.existsSync(path.join(root, "README.md")), true);
  assert.strictEqual(fs.existsSync(path.join(root, "LICENSE")), true);
  assert.strictEqual(fs.existsSync(path.join(root, "CHANGELOG.md")), true);
  assert.strictEqual(fs.existsSync(path.join(root, "CONTRIBUTING.md")), true);
  assert.strictEqual(fs.existsSync(path.join(root, "index.d.ts")), true);
  assert.strictEqual(fs.existsSync(path.join(root, "bin", "tzero.js")), true);
  assert.strictEqual(fs.existsSync(path.join(root, "bin", "tzero-mcp.js")), true);
});
