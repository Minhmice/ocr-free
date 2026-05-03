#!/usr/bin/env node
/**
 * Run web + API together. Ctrl+C (SIGINT) sends SIGINT to both children so ports release cleanly.
 */
import { spawn } from "child_process";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, "..");

const opts = {
  cwd: repoRoot,
  env: { ...process.env },
  stdio: "inherit",
  shell: true,
};

const web = spawn("npm", ["run", "dev:web"], opts);
const api = spawn("npm", ["run", "dev:api"], opts);

function shutdown(signal) {
  try {
    web.kill(signal);
  } catch {
    /* ignore */
  }
  try {
    api.kill(signal);
  } catch {
    /* ignore */
  }
  setTimeout(() => process.exit(0), 400).unref();
}

process.on("SIGINT", () => shutdown("SIGINT"));
process.on("SIGTERM", () => shutdown("SIGTERM"));
