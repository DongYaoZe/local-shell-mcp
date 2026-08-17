#!/usr/bin/env node
const { execFileSync } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");

const extensionRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(extensionRoot, "..");
const pkg = require(path.join(extensionRoot, "package.json"));
const out = path.join(repoRoot, "dist", `local-shell-mcp-${pkg.version}.vsix`);
const vsce = require.resolve("@vscode/vsce/vsce");
const args = [vsce, "package", "--no-dependencies", "--out", out];
if (process.argv.includes("--pre-release")) {
  args.push("--pre-release");
}

fs.mkdirSync(path.dirname(out), { recursive: true });
execFileSync(process.execPath, args, {
  cwd: extensionRoot,
  stdio: "inherit",
});
