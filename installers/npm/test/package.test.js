const test = require("node:test");
const assert = require("node:assert");
const path = require("node:path");
const fs = require("node:fs");
const tzero = require("../index.js");

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
});

