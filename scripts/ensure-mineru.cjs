#!/usr/bin/env node
/**
 * If packages/mineru exists (git clone of opendatalab/MinerU), ensure the `mineru`
 * CLI is installed into apps/api/.venv. No-op if source is missing or CLI already present.
 */

const { spawnSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const apiDir = path.join(root, "apps", "api");

/** README path, or legacy path when MinerU was cloned under apps/api. */
function findMineruSrc() {
  const candidates = [
    path.join(root, "packages", "mineru"),
    path.join(apiDir, "packages", "mineru"),
  ];
  const markers = ["pyproject.toml", "setup.py", "setup.cfg"];
  for (const dir of candidates) {
    if (!fs.existsSync(dir) || !fs.statSync(dir).isDirectory()) continue;
    if (markers.some((f) => fs.existsSync(path.join(dir, f)))) return dir;
  }
  return null;
}

function venvPython() {
  const unix = path.join(apiDir, ".venv", "bin", "python");
  const win = path.join(apiDir, ".venv", "Scripts", "python.exe");
  if (fs.existsSync(unix)) return unix;
  if (fs.existsSync(win)) return win;
  return null;
}

function mineruCliInVenv() {
  const unix = path.join(apiDir, ".venv", "bin", "mineru");
  const win = path.join(apiDir, ".venv", "Scripts", "mineru.exe");
  if (fs.existsSync(unix)) return true;
  if (fs.existsSync(win)) return true;
  return false;
}

function main() {
  const py = venvPython();
  if (!py) {
    console.warn("[mineru-api] ensure-mineru: apps/api/.venv missing (run setup:api first).");
    process.exit(0);
  }

  const mineruSrc = findMineruSrc();
  if (!mineruSrc) {
    console.log(
      "[mineru-api] MinerU source not found at packages/mineru or apps/api/packages/mineru — clone https://github.com/opendatalab/MinerU.git into packages/mineru (see README).",
    );
    process.exit(0);
  }

  if (mineruCliInVenv()) {
    console.log("[mineru-api] mineru CLI OK:", mineruSrc);
    process.exit(0);
  }

  const relPosix = path.relative(root, mineruSrc).split(path.sep).join("/") || ".";
  const editableSpec = `${relPosix}[all]`;
  console.log("[mineru-api] Installing MinerU into API venv (pip install -e) …");
  const install = spawnSync(py, ["-m", "pip", "install", "-e", editableSpec], {
    stdio: "inherit",
    cwd: root,
  });
  process.exit(install.status ?? 1);
}

main();
