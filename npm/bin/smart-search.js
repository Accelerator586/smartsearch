#!/usr/bin/env node

const { spawn } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");

const packageRoot = path.resolve(__dirname, "..", "..");
const venvDir = path.join(packageRoot, ".smart-search-python");
const pythonPath =
  process.platform === "win32"
    ? path.join(venvDir, "Scripts", "python.exe")
    : path.join(venvDir, "bin", "python");

if (!fs.existsSync(pythonPath)) {
  console.error("smart-search npm wrapper could not find its Python runtime.");
  console.error(`Expected: ${pythonPath}`);
  console.error("Repair it by reinstalling the package:");
  console.error("  npm install -g @konbakuyomu/smart-search@latest");
  process.exit(5);
}

const child = spawn(
  pythonPath,
  ["-m", "smart_search.cli", ...process.argv.slice(2)],
  {
    cwd: packageRoot,
    stdio: "inherit",
    windowsHide: true
  }
);

child.on("error", (error) => {
  console.error(`Failed to start smart-search: ${error.message}`);
  process.exit(5);
});

child.on("close", (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
    return;
  }
  process.exit(code ?? 5);
});
