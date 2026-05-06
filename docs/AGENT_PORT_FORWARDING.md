# LAN access, firewalls, and reverse proxies (MinerU / agents)

This note is for operators and **automation agents** that expose MinerU WebUI (`7860`) or API (`8000`) beyond `127.0.0.1`.

## Listen address

- **Gradio**: `mineru-gradio --server-name 0.0.0.0 --server-port 7860`
- **FastAPI**: `mineru-api --host 0.0.0.0 --port 8000`

Binding to `0.0.0.0` makes the service reachable on all interfaces (including LAN). Combine with host firewall rules so only intended networks can connect.

## Windows Firewall (example)

Open TCP **7860** and **8000** for private networks (adjust `-Profile` / remote IPs as needed):

```powershell
New-NetFirewallRule -DisplayName "MinerU Gradio 7860" -Direction Inbound `
  -Protocol TCP -LocalPort 7860 -Action Allow -Profile Private
New-NetFirewallRule -DisplayName "MinerU API 8000" -Direction Inbound `
  -Protocol TCP -LocalPort 8000 -Action Allow -Profile Private
```

Remove or disable rules when no longer required.

## macOS

There is no single standard like `ufw`. Options include **pf** (`pfctl`), host-based firewall in **System Settings**, or restricting bind address / using an SSH tunnel. Document your org’s standard; do not expose services on public Wi‑Fi without TLS and auth.

## Linux (`ufw` examples)

```bash
sudo ufw allow 7860/tcp comment 'MinerU Gradio'
sudo ufw allow 8000/tcp comment 'MinerU API'
sudo ufw reload
```

Prefer limiting source IPs (`ufw allow from <trusted-subnet> to any port 8000`) when possible.

## Reverse proxy environment variables (FastAPI)

Implemented in `mineru/mineru/cli/fast_api.py`:

| Variable | Purpose |
|----------|---------|
| `MINERU_API_ROOT_PATH` | Sub-path when mounted behind a proxy (FastAPI `root_path`). |
| `MINERU_API_CORS_ALLOW_ORIGINS` | Comma-separated origins for `CORSMiddleware` (only applied if non-empty). |
| `MINERU_API_TRUST_PROXY_HEADERS` | When enabled, Uvicorn uses `proxy_headers` and `forwarded_allow_ips` for client/scheme behind a proxy. |
| `MINERU_API_FORWARDED_ALLOW_IPS` | Comma-separated IPs trusted for `Forwarded`/`X-Forwarded-*` (default `127.0.0.1` in code). |

**Important:** enable `MINERU_API_TRUST_PROXY_HEADERS` **only** when MinerU sits **behind a trusted reverse proxy** you control. Misconfiguration can affect how client addresses and scheme are interpreted.

## SSRF and `--allow-public-http-client`

MinerU API documents a hardening stance around `--allow-public-http-client`. When the API is bound to all interfaces and this flag is enabled, `*-http-client` backends and `server_url` can become an **SSRF** risk against internal networks and metadata endpoints.

- Keep `--allow-public-http-client` **off** unless you explicitly need it and understand the exposure.
- Do not expose the API to untrusted networks without additional controls (auth, TLS, network policy).

## Docker Compose (this repo)

Root `compose.yaml` publishes `7860` (Gradio) and optionally `8000` (API profile). Ensure host firewall and cloud security groups match your intent; container `restart: unless-stopped` does not replace network policy.
