# Deploying LMS Bridge to Railway

This deploys the full stack — **Postgres + backend + frontend (Sage/app) + marketing site** — as
four services in one Railway project. The repo is already Railway-ready: each service has a
`railway.toml`, and all services bind Railway's injected `$PORT`.

> Why Railway over Render free: Railway services **don't sleep**, so there are no cold starts.
> The trade-off is cost — Railway has no permanent free tier. New accounts get a small trial
> credit; after that it's the **Hobby plan (~$5/month, usage-based)**. Postgres + three light
> services on Hobby typically runs a few dollars a month.

---

## 0. Prerequisites

- A Railway account (railway.app), logged in with GitHub.
- The repo **pushed to GitHub** and, ideally, public (`git push origin main`).

## 1. Create the project + database

1. Railway → **New Project** → **Deploy PostgreSQL**. This creates the DB and a `DATABASE_URL`
   variable on the Postgres service. (The backend auto-rewrites `postgresql://` to the psycopg
   driver, so no edit needed.)
2. You now have an empty project with one Postgres service.

## 2. Add the three app services (same repo, different root directories)

For **each** of the three services below: **New → GitHub Repo → pick your repo**, then open the
service's **Settings → Root Directory** and set it. Railway reads that folder's `railway.toml` and
its Dockerfile automatically.

| Service | Root Directory | Notes |
|---|---|---|
| `backend` | `backend` | runs migrations + seed + uvicorn on `$PORT` |
| `frontend` | `frontend` | the Sage/app SPA (nginx) |
| `marketing` | `marketing` | the marketing site (nginx) |

> Tip: naming the services exactly `backend`, `frontend`, `marketing` makes the reference variables
> in step 4 copy-paste cleanly.

## 3. Give each service a public domain

For `backend`, `frontend`, and `marketing`: **Settings → Networking → Generate Domain**. You'll get
URLs like `https://backend-production-xxxx.up.railway.app`. (Postgres stays private — no domain.)

## 4. Set environment variables

Railway supports **reference variables** — `${{ServiceName.VAR}}` — so services can point at each
other without you pasting URLs. Set these under each service's **Variables** tab.

### backend

| Variable | Value |
|---|---|
| `APP_ENV` | `production` |
| `DEPLOYMENT_MODE` | `community` |
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` (reference the Postgres service) |
| `SECRET_KEY` | a long random string (e.g. `openssl rand -hex 32`) |
| `LLM_PROVIDER` | `mock` (or `anthropic` / `openai` / `azure_openai`) |
| `ANTHROPIC_API_KEY` | your key, if `LLM_PROVIDER=anthropic` |
| `TOOL_BASE_URL` | `https://${{backend.RAILWAY_PUBLIC_DOMAIN}}` |
| `FRONTEND_BASE_URL` | `https://${{frontend.RAILWAY_PUBLIC_DOMAIN}}` |
| `CORS_ORIGINS` | `https://${{frontend.RAILWAY_PUBLIC_DOMAIN}},https://${{marketing.RAILWAY_PUBLIC_DOMAIN}}` |
| `PLATFORM_ADMIN_EMAIL` | your operator login email |
| `PLATFORM_ADMIN_PASSWORD` | a strong password (created on first boot) |

> If the Postgres service isn't named `Postgres`, use its actual name in `${{...}}`. You can also
> just click the "Add reference" button in the Variables UI and pick it from a list.

### frontend

| Variable | Value |
|---|---|
| `API_BASE_URL` | `https://${{backend.RAILWAY_PUBLIC_DOMAIN}}/api/v1` |

Optional white-label vars (`BRAND_NAME`, `BRAND_TAGLINE`, `BRAND_ACCENT`, `BRAND_LOGO_URL`) work
here too — see `docs/BRANDING.md`.

### marketing

| Variable | Value |
|---|---|
| `API_BASE_URL` | `https://${{backend.RAILWAY_PUBLIC_DOMAIN}}/api/v1` |
| `APP_BASE_URL` | `https://${{frontend.RAILWAY_PUBLIC_DOMAIN}}` |

## 5. Deploy

Each service redeploys when you save variables (or hit **Deploy**). Watch the **backend** logs — you
should see Alembic run `upgrade head`, the seed step, then `Uvicorn running`. The backend's
healthcheck (`/api/v1/health`) must go green before it's marked live.

## 6. Verify

- `https://<backend>/api/v1/health` → returns OK.
- `https://<frontend>/` → the app loads; `https://<frontend>/sage` → Sage.
- `https://<marketing>/` → the marketing site; the "try the live demo" link points at the frontend.
- Log in to the app with your `PLATFORM_ADMIN_EMAIL` / `PLATFORM_ADMIN_PASSWORD`.

## 7. (Optional) custom domains

Per service: **Settings → Networking → Custom Domain**, add e.g. `app.lmsbridge.app` (frontend),
`api.lmsbridge.app` (backend), `www.lmsbridge.app` (marketing), and create the CNAME records Railway
shows. Then update `TOOL_BASE_URL`, `FRONTEND_BASE_URL`, `CORS_ORIGINS`, and the two `API_BASE_URL`
values to the custom hostnames and redeploy.

---

## Notes & gotchas

- **CLI alternative:** `npm i -g @railway/cli`, `railway login`, then from each folder
  `railway up` after `railway link`. The dashboard flow above is simpler for a first move.
- **Migrations** run automatically on every backend deploy (idempotent). No manual step.
- **Data:** Railway Postgres persists across deploys. Set up backups under the Postgres service if
  this becomes production data.
- **Cost control:** stopping/deleting the marketing service (or hosting it on GitHub Pages/Netlify
  free instead) trims usage if you only need the app + API on Railway.
- **Render leftovers:** `render.yaml` and `infra/railway.json` can stay in the repo; Railway ignores
  `render.yaml`, and the per-service `railway.toml` files supersede `infra/railway.json`.
