#!/usr/bin/env node
/**
 * Ensures apps/api/.venv exists with Python 3.11–3.13 and editable API deps.
 * Python 3.14 breaks pydantic-core (PyO3) builds until wheels catch up.
 */

const { execFileSync, spawnSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const apiDir = path.join(root, "apps", "api");

function execQuiet(cmd, args) {
  try {
    execFileSync(cmd, args, { stdio: "pipe" });
    return true;
  } catch {
    return false;
  }
}

/** @returns {string|null} two-char version like "3.12" */
function pyMinorVersion(cmd) {
  try {
    const out = execFileSync(
      cmd,
      ["-c", "import sys; print('%d.%d' % sys.version_info[:2])"],
      { encoding: "utf8", stdio: ["pipe", "pipe", "pipe"] },
    );
    return out.trim();
  } catch {
    return null;
  }
}

function isSupportedMinor(ver) {
  if (!ver) return false;
  const [maj, min] = ver.split(".").map(Number);
  return maj === 3 && min >= 11 && min <= 13;
}

/**
 * Look for a usable interpreter (not 3.14+).
 */
function findPython() {
  const candidates = [
    process.env.PYTHON312,
    process.env.PYTHON,
    "/opt/homebrew/opt/python@3.12/bin/python3.12",
    "/opt/homebrew/opt/python@3.13/bin/python3.13",
    "/usr/local/opt/python@3.12/bin/python3.12",
    "python3.12",
    "python3.13",
    "python3.11",
    "python3",
  ].filter(Boolean);

  const seen = new Set();
  for (const cmd of candidates) {
    if (seen.has(cmd)) continue;
    seen.add(cmd);

    if (cmd.includes(path.sep) && !fs.existsSync(cmd)) continue;

    try {
      execFileSync(cmd, ["-c", "import sys"], { stdio: "pipe" });
    } catch {
      continue;
    }

    const ver = pyMinorVersion(cmd);
    if (!isSupportedMinor(ver)) continue;

    return { executable: cmd, version: ver };
  }

  return null;
}

function venvInterpreterPath() {
  const unix = path.join(apiDir, ".venv", "bin", "python");
  const win = path.join(apiDir, ".venv", "Scripts", "python.exe");
  if (fs.existsSync(unix)) return unix;
  if (fs.existsSync(win)) return win;
  return null;
}

function venvNeedsRecreate(venvPy, desiredVer) {
  const ver = pyMinorVersion(venvPy);
  if (!ver) return true;
  const [maj, min] = ver.split(".").map(Number);
  if (maj !== 3 || min < 11 || min > 13) {
    console.warn(
      `[mineru-api] Existing .venv uses Python ${ver} (need 3.11–3.13). Recreating with Python ${desiredVer} …`,
    );
    return true;
  }
  return false;
}

function depsOk(venvPy) {
  return execQuiet(venvPy, ["-c", "import uvicorn, pydantic"]);
}

function rimraf(dir) {
  fs.rmSync(dir, { recursive: true, force: true });
}

function runPipInstall(venvPy) {
  console.log("[mineru-api] Installing editable package (pip install -e .) …");
  const pipUpgrade = spawnSync(
    venvPy,
    ["-m", "pip", "install", "--upgrade", "pip"],
    { stdio: "inherit", cwd: apiDir },
  );
  if (pipUpgrade.status !== 0) process.exit(pipUpgrade.status ?? 1);

  const install = spawnSync(venvPy, ["-m", "pip", "install", "-e", "."], {
    stdio: "inherit",
    cwd: apiDir,
  });
  if (install.status !== 0) process.exit(install.status ?? 1);
}

function main() {
  const found = findPython();
  if (!found) {
    console.error(
      "[mineru-api] No Python 3.11–3.13 found. Python 3.14 cannot build pydantic-core yet.",
    );
    console.error(
      "  Install Python 3.12, e.g.  brew install python@3.12  then add to PATH:",
    );
    console.error(
      '  export PATH="/opt/homebrew/opt/python@3.12/bin:$PATH"',
    );
    process.exit(1);
  }

  const { executable: basePy, version: baseVer } = found;
  const venvDir = path.join(apiDir, ".venv");
  let venvPy = venvInterpreterPath();

  if (venvPy && venvNeedsRecreate(venvPy, baseVer)) {
    rimraf(venvDir);
    venvPy = null;
  }

  if (!venvPy || !fs.existsSync(venvPy)) {
    console.log(`[mineru-api] Creating venv with ${basePy} (Python ${baseVer}) …`);
    const venv = spawnSync(basePy, ["-m", "venv", ".venv"], {
      stdio: "inherit",
      cwd: apiDir,
    });
    if (venv.status !== 0) process.exit(venv.status ?? 1);
    venvPy = venvInterpreterPath();
    if (!venvPy) {
      console.error("[mineru-api] venv creation failed (python interpreter missing).");
      process.exit(1);
    }
    runPipInstall(venvPy);
    console.log("[mineru-api] Ready:", venvPy);
    return;
  }

  if (!depsOk(venvPy)) {
    console.log("[mineru-api] Dependencies missing or broken; reinstalling …");
    runPipInstall(venvPy);
  } else {
    console.log("[mineru-api] OK:", venvPy);
  }
}

main();
