# Deploy for Free — Delhi Metro Digital Twin

Zero-cost deployment using Docker Compose + Cloudflare Tunnel (free tier,
no credit card, no domain purchase required).

## Prerequisites

- Docker + Docker Compose v2 (or Docker Desktop)
- [cloudflared](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/)
  (free)

## Quick Start (local-only)

```bash
cp .env.example .env
docker compose up -d --build
open http://localhost:8080
```

Backend auto-runs migrations and seeds the database on first boot
(~10–20 seconds). Give it up to 90 seconds on the very first run.

---

## Section A — Stable Named Tunnel (permanent URL, same across restarts)

**Requires a free Cloudflare account (no credit card, no domain).**

The tunnel gets a permanent hostname `<tunnel-uuid>.cfargotunnel.com`
that never changes. It runs as a container in your compose stack and
survives reboot, sleep, and docker compose restarts.

### A1 — One-time setup (run these yourself)

```bash
# 1. Login — opens a browser to authorize cloudflared with your free
#    Cloudflare account. Select any domain listed (or none — the
#    authentication step needs at least one domain in your account,
#    but the tunnel hostname does not use it).
#    If you have zero domains, create a free Cloudflare account and
#    this step still works (the page may show "No zones" but the
#    certificate is issued to your account, not to a domain).
cloudflared tunnel login
```

```bash
# 2. Create a named tunnel — generates a UUID + credentials file.
#    Saves a JSON file to ~/.cloudflared/<UUID>.json.
cloudflared tunnel create delhi-metro-twin
```

Expected output:
```
Created tunnel delhi-metro-twin with id <UUID>
Credentials file created at /Users/<you>/.cloudflared/<UUID>.json
Tunnel will be hosted at <UUID>.cfargotunnel.com
```

### A2 — Wire up the config

Edit `cloudflared/config.yml` in this repo and replace the two
`<TUNNEL_UUID>` placeholders with the UUID from step A1:

```yaml
tunnel: <UUID>                          # ← your actual UUID
credentials-file: /home/nonroot/.cloudflared/<UUID>.json
ingress:
  - hostname: <UUID>.cfargotunnel.com
    service: http://nginx:8080
  - service: http_status:404
```

Also edit `.env` and set the tunnel variables (optional but useful
for reference):

```
TUNNEL_NAME=delhi-metro-twin
TUNNEL_UUID=<UUID>
TUNNEL_HOSTNAME=<UUID>.cfargotunnel.com
```

### A3 — Start the stack (tunnel included)

```bash
docker compose up -d
```

The cloudflared container starts after nginx is healthy, loads the
config, and connects to Cloudflare's edge. Within a few seconds the
tunnel status becomes "Healthy" in the Cloudflare dashboard.

### A4 — Confirm it works

Your stable public URL is:

```
https://<UUID>.cfargotunnel.com
```

```bash
# REST API
curl -s https://<UUID>.cfargotunnel.com/api/v1/health

# Frontend
curl -s -o /dev/null -w "%{http_code}" https://<UUID>.cfargotunnel.com/

# WebSocket (requires wscat: npm install -g wscat)
wscat -c wss://<UUID>.cfargotunnel.com/api/v1/ws/simulation
```

WebSocket should stream live train position updates every ~2 seconds.

### A5 — Verify URL survives restarts

```bash
docker compose down
docker compose up -d
curl -s https://<UUID>.cfargotunnel.com/api/v1/health     # same URL, still works
```

The `.cfargotunnel.com` hostname is permanent because it is
registered at Cloudflare's edge (not on your machine). The tunnel
reconnects using the same credentials file.

### Rotating / revoking credentials

If a credentials file is ever compromised:

```bash
cloudflared tunnel delete delhi-metro-twin
rm ~/.cloudflared/<UUID>.json
# Then re-create from step A1 — you will get a new UUID + new URL.
```

To temporarily disconnect without deleting: `docker compose stop cloudflared`.

---

## Section B — Quick Tunnel (fallback, zero setup)

No Cloudflare account needed. URL changes every time — use for
testing only.

```bash
# Terminal 1 — start the stack
docker compose up -d --build

# Terminal 2 — expose to the internet (requires cloudflared installed)
cloudflared tunnel --url http://localhost:8080
```

cloudflared prints a random URL like `https://xxxxx.trycloudflare.com`.
Share that URL. The tunnel lives as long as the cloudflared process runs.

**Limitations:**
- URL changes on every run
- Up to 100 Mbps, ~~200 concurrent requests~~
- No Server-Sent Events (SSE) support
- Tunnel dies if you close the terminal or the machine sleeps
- Can conflict with a `config.yml` in `~/.cloudflared` (rename it temporarily)

---

## Managing the Stack

### View logs

```bash
docker compose logs -f                  # all services
docker compose logs -f cloudflared      # tunnel only
docker compose logs -f backend          # backend only
```

### Update/redeploy after code changes

```bash
cd /Users/aryamansharma/delhi-metro-digital-twin
git pull
docker compose up -d --build
```

The tunnel reconnects automatically — same URL, no config changes.

### Back up the database

```bash
docker compose exec postgres pg_dump -U dmdt dmdt > backup_$(date +%Y%m%d).sql
```

Restore:

```bash
docker compose exec -T postgres psql -U dmdt dmdt < backup_20250708.sql
```

### Stop without losing data

```bash
docker compose down             # stops containers, preserves volumes
docker compose down -v         # ALSO destroys volumes (deletes DB data!)
```

---

## Important Caveats

**Uptime depends on your machine.**
This is a single-machine deployment. If your laptop sleeps, loses
internet, or reboots, the app goes down. This is the tradeoff for
$0 hosting. For production uptime, use a $5–10 VPS with the same
compose file.

**Named tunnel URL is permanent** as long as the tunnel object exists
in your Cloudflare account. Deleting and recreating the tunnel gives
a new UUID and a new URL.

**No backups are automatic.**
Use `pg_dump` regularly, or add a cron job.

---

## Architecture

```
                         Cloudflare Edge (<UUID>.cfargotunnel.com)
                                │
                     cloudflared container (outbound-only)
                                │
                         ┌──────┴──────┐
                         │   nginx:8080 │  ← single entry point
                         └──────┬──────┘
                                │
               ┌────────────────┼────────────────┐
               │                │                │
         /api/* + WS      everything else    static assets
               │                │                │
         backend:8000     frontend:3000     frontend:3000
         (FastAPI +        (Next.js
          simulation)       standalone)
               │
     ┌─────────┼─────────┐
     │         │         │
  postgres   redis   rabbitmq
```

## What each `docker compose` command does

| Command | Effect |
|---|---|
| `docker compose up -d` | Start all services (including tunnel) in background |
| `docker compose up -d --build` | Rebuild images then start |
| `docker compose down` | Stop and remove containers (preserves volumes) |
| `docker compose down -v` | Stop and **delete all data** |
| `docker compose logs -f` | Follow logs from all services |
| `docker compose ps` | Show service status |
| `docker compose exec backend ...` | Run a command inside the backend container |

## Verification Checklist

```bash
# 1. All services healthy
docker compose ps

# 2. REST API works (local)
curl -s http://localhost:8080/api/v1/health | head -c 200

# 3. REST API works (via tunnel)
curl -s https://<UUID>.cfargotunnel.com/api/v1/health | head -c 200

# 4. WebSocket connects
wscat -c wss://<UUID>.cfargotunnel.com/api/v1/ws/simulation

# 5. Frontend loads
curl -s -o /dev/null -w "%{http_code}" https://<UUID>.cfargotunnel.com/

# 6. URL survives restart
docker compose down && docker compose up -d
curl -s https://<UUID>.cfargotunnel.com/api/v1/health   # same URL
```

---

## Environment Variables

See `.env.example` for the full list. Key variables:

| Variable | Default | Description |
|---|---|---|
| `POSTGRES_DB` | `dmdt` | Database name |
| `POSTGRES_USER` | `dmdt` | Database user |
| `POSTGRES_PASSWORD` | `change-me-in-dev` | **Change this for public access** |
| `JWT_SECRET` | `change-this-to-...` | **Change this for public access** |
| `ADMIN_PASSWORD` | `change-me-in-dev` | **Change this for public access** |
| `TUNNEL_NAME` | `delhi-metro-twin` | Cloudflare tunnel name |
| `TUNNEL_UUID` | _(set after create)_ | Tunnel UUID from `cloudflared tunnel create` |

No step in this setup requires a credit card, paid hosting tier,
or domain purchase.
