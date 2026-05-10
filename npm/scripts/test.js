const { spawnSync } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");

const packageRoot = path.resolve(__dirname, "..", "..");
const venvDir = path.join(packageRoot, ".smart-search-python");
const pythonPath =
  process.platform === "win32"
    ? path.join(venvDir, "Scripts", "python.exe")
    : path.join(venvDir, "bin", "python");

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: packageRoot,
    stdio: "inherit",
    shell: options.shell || false,
    windowsHide: true
  });
  if (result.error) {
    console.error(result.error.message);
    process.exit(1);
  }
  if (result.status !== 0) {
    process.exit(result.status || 1);
  }
}

function runNpm(args) {
  if (process.env.npm_execpath) {
    run(process.execPath, [process.env.npm_execpath, ...args]);
    return;
  }
  run("npm", args, { shell: process.platform === "win32" });
}

if (!fs.existsSync(pythonPath)) {
  console.error("Missing .smart-search-python runtime. Run npm install first.");
  process.exit(1);
}

run(pythonPath, ["-m", "pip", "install", "--disable-pip-version-check", "-e", ".[dev]"]);
run(pythonPath, ["-m", "pytest"]);
run(process.execPath, ["npm/bin/smart-search.js", "--help"]);
runNpm(["pack", "--dry-run"]);
