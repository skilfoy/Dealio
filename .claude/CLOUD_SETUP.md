# Claude Code Cloud Setup for DealRadar

This guide explains how to test DealRadar in Claude Code on the web with public URL access.

## Automatic Setup

When you start a Claude Code cloud session, the session start hook (`.claude/hooks/session-start.sh`) automatically:

1. **Starts Docker services** — Launches all 6 services (Postgres, Redis, API, Worker, Beat, Frontend)
2. **Waits for health checks** — Ensures database and cache are ready
3. **Creates public tunnels** — Exposes localhost:5173 and localhost:8000 via Buddy Tunnels

## What You'll Get

After ~30-60 seconds, you'll see output like:

```
🎉 DealRadar is accessible from your browser:
   Frontend: https://abc123def456.tunnel.buddy.app
   API:      https://xyz789uvw012.tunnel.buddy.app
   Docs:     https://xyz789uvw012.tunnel.buddy.app/docs
```

Copy those URLs and paste them into your browser to test the full application.

## Prerequisites

The Buddy CLI (`bdy`) must be installed in your Claude Code cloud environment. The session hook checks for it automatically.

If the hook detects that Buddy is not installed:
- You can manually install it: `npm install -g @buddy.works/cli`
- Or configure it in your environment setup

## Manual Tunnel Creation (if needed)

If you want to create tunnels manually during a session:

```bash
# Terminal 1: Create frontend tunnel
bdy tunnel http localhost:5173 --auth public

# Terminal 2: Create API tunnel  
bdy tunnel http localhost:8000 --auth public
```

## Testing Without Tunnels

If Buddy CLI is unavailable, the services still run locally and you can test via:

**API Testing:**
```bash
curl http://localhost:8000/api/deals
curl http://localhost:8000/docs  # Swagger UI
```

**Frontend:**
- Cannot be accessed externally without tunnels
- But you can test all API endpoints directly

## Architecture

```
Your Browser
    ↓
Public Tunnel (Buddy)
    ↓
Claude Code Cloud VM
    ↓
Docker Compose (6 services)
    ├── Postgres (port 5432)
    ├── Redis (port 6379)
    ├── FastAPI (port 8000)
    ├── Celery Worker
    ├── Celery Beat
    └── React Vite (port 5173)
```

## Troubleshooting

**Tunnels not appearing:**
- Check if Buddy CLI is installed: `which bdy`
- Check tunnel status: `bdy tunnel list`
- Check Docker logs: `docker compose logs -f api`

**Services not starting:**
- Check Docker status: `docker compose ps`
- View logs: `docker compose logs postgres redis`
- Ensure .env file exists with proper DATABASE_URL and REDIS_URL

**Slow initial startup:**
- First build takes longer (~2 minutes) due to Python deps and Playwright
- Subsequent sessions reuse cached layers and start faster

## Security Notes

- Tunnels created with `--auth public` are publicly accessible
- For sensitive testing, use `--auth basic` instead (requires username/password)
- Tunnels auto-expire after 24 hours of inactivity
- URLs are single-session and regenerated each cloud session
