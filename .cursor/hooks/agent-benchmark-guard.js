/**
 * Optional developer hook: run agent benchmark guards after relevant edits.
 *
 * This is intentionally lightweight and stdlib-only on the Python side:
 * - routing parity check
 * - benchmark case schema validation
 *
 * Enable by adding a hook in `.cursor/settings.json`, for example:
 * {
 *   "hooks": {
 *     "FileSave": [
 *       { "hooks": [{ "type": "command", "command": "node .cursor/hooks/agent-benchmark-guard.js" }] }
 *     ]
 *   }
 * }
 *
 * If your Cursor build doesn't support FileSave hooks, you can run this manually.
 */

const { spawnSync } = require("node:child_process");

function run(cmd, args) {
  const r = spawnSync(cmd, args, { stdio: "inherit", shell: process.platform === "win32" });
  if (r.status !== 0) process.exit(r.status ?? 1);
}

// Fast checks only (no benchmark run).
run("python", [".cursor/agents/benchmarks/scripts/check_routing_parity.py"]);
run("python", [".cursor/agents/benchmarks/scripts/validate_cases.py"]);

