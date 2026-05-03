#!/usr/bin/env node
/**
 * Fail fast if API_PORT (default 8000) is already bound.
 * Avoids uvicorn's opaque "Address already in use".
 */

const net = require("net");

const raw = process.env.API_PORT || "8000";
const port = Number(raw);

if (!Number.isInteger(port) || port < 1 || port > 65535) {
  console.error("[mineru-api] Invalid API_PORT:", raw);
  process.exit(1);
}

const server = net.createServer();
server.once("error", (err) => {
  if (err.code === "EADDRINUSE") {
    console.error(`[mineru-api] Port ${port} is already in use.`);
    console.error(`  Free it (macOS/Linux):  kill $(lsof -ti:${port})`);
    console.error(`  Or use another port in the same terminal:`);
    console.error(`    export API_PORT=8001`);
    console.error(`    export NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8001`);
    console.error(`    pnpm dev`);
    process.exit(1);
  }
  console.error(err);
  process.exit(1);
});

server.listen({ port, host: "127.0.0.1" }, () => {
  server.close(() => process.exit(0));
});
