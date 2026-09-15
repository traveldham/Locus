# Deployment

A single VM: nginx in front, three systemd units, Postgres and Redis local.

Everything is in `deploy/` — five files, nothing hidden.

```
deploy/deploy.sh
deploy/nginx/locus.pawanpatra.com.conf
deploy/systemd/locus-backend.service
deploy/systemd/locus-celery.service
deploy/systemd/locus-frontend.service
```

## The units

| Unit | Runs | Notes |
| --- | --- | --- |
| `locus-backend` | `uv run uvicorn app.main:app --host 127.0.0.1 --port 8000` | `Requires=redis-server.service` |
| `locus-celery` | `uv run celery -A app.worker worker --loglevel=info --concurrency=6` | Runs Celery **directly**, not through `start.sh`, so no pid file in production |
| `locus-frontend` | `node_modules/.bin/next start -p 3000` | `NODE_ENV=production` |

All three run as an unprivileged user with `NoNewPrivileges=true`, `Restart=on-failure` and
`RestartSec=5`. No `EnvironmentFile` — pydantic-settings reads `.env` from the unit's
`WorkingDirectory`.

Both application units bind to **127.0.0.1**. Only nginx is exposed.

## nginx

Three locations, and the order matters:

```nginx
# 1. SSE — a regex location takes precedence over the /api/ prefix
location ~ ^/api/v1/agent/turns/[^/]+/stream$ {
    proxy_pass http://127.0.0.1:8000;
    proxy_buffering off;          # or the browser sees nothing until the turn ends
    proxy_cache off;
    proxy_read_timeout 600s;
    proxy_set_header Connection "";
}

# 2. the API — path unchanged, the app's own prefix is already /api/v1
location /api/ { proxy_pass http://127.0.0.1:8000; }

# 3. everything else — Next.js, with websocket upgrade headers
location / { proxy_pass http://127.0.0.1:3000; ... }
```

`client_max_body_size 10m`. **The TLS block is not in the repo** — certbot generates it:

```bash
sudo cp deploy/nginx/locus.pawanpatra.com.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/locus.pawanpatra.com /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d locus.pawanpatra.com
```

## Redeploying

```bash
sudo /home/pawanpatrapp/Locus/deploy/deploy.sh
```

It refuses to run without root, then, as the app user:

```
git pull --ff-only
backend:  uv sync  &&  uv run alembic upgrade head
frontend: npm ci   &&  npm run build
systemctl restart locus-backend locus-celery locus-frontend
systemctl status  (grepped to the Active: lines)
```

**There is no seeding step** — the app seeds itself on first boot through the FastAPI
lifespan, and the seed is idempotent.

## Production checklist

- [ ] `SECRET_KEY` — 32+ random characters, not the shipped placeholder
- [ ] `COOKIE_SECURE=true` — the refresh cookie must not travel in clear
- [ ] `APP_ENV=production` — otherwise a 500 returns the exception string
- [ ] `FRONTEND_URL` — the exact browser origin, or CORS fails
- [ ] `NEXT_PUBLIC_API_URL` — set at **build** time; `npm run build` bakes it in
- [ ] `DATABASE_URL` — a real user and password
- [ ] `VERTEX_PROJECT` + credentials for the VM, if AI is wanted
- [ ] `certbot` run, and the TLS block present
- [ ] Redis reachable — the backend unit `Requires` it

## Operational notes

- **A migration runs before the restart**, so a deploy that changes the schema briefly serves
  old code against a new schema. Every migration so far is additive or deliberately
  destructive at a point where the old rows were meaningless — check before relying on it.
- **Killing the worker mid-audit** leaves the job `running` until it is re-run. `stop.sh`
  warns about this; the production unit does a warm shutdown on `systemctl stop`.
- **`worker_max_tasks_per_child = 50`** recycles workers, which bounds any leak in a long
  audit.
- **No custom queues.** Audits and agent turns share the default queue, so a long audit can
  delay a chat turn. Splitting them is the obvious first change under load.
- **Logs**: `journalctl -u locus-backend -f` (or `-celery`, `-frontend`).
