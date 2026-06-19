# LMS Bridge — Deployment Guide

This guide covers running LMS Bridge in production. The platform is fully containerized and
cloud-agnostic. Every option below runs database migrations and an idempotent seed on backend
startup, so a fresh environment comes up working.

## Before you deploy — production checklist

- [ ] Set a strong `SECRET_KEY` (`openssl rand -hex 32`) via your host's secret manager.
- [ ] Set `APP_ENV=production`.
- [ ] Choose `DEPLOYMENT_MODE` — `community` (default: free self-host, no license gate, single institution) or `hosted` (multi-tenant SaaS with the platform-operator role, lead capture, and license enforcement).
- [ ] Provision PostgreSQL and set `DATABASE_URL` (`postgresql+psycopg://user:pass@host:5432/db`).
- [ ] Set `CORS_ORIGINS` to your real frontend origin(s).
- [ ] Choose your `LLM_PROVIDER` and set its credentials (or keep `mock` to demo without a model).
- [ ] Point the frontend at the backend with `API_BASE_URL` (runtime env on the frontend container — no rebuild needed).
- [ ] Decide whether to keep the auto-seed. To disable, change the container command to drop the
      `python -m app.scripts.seed --if-empty` step.

---

## Option A — Docker Compose on a single host (simplest)

Good for a pilot on one VM (e.g. an institutional or cloud VM with Docker installed).

```bash
git clone <your-repo> && cd lms-bridge
cp .env.example .env
# edit .env: set SECRET_KEY, APP_ENV=production, CORS_ORIGINS, LLM provider keys
docker compose up --build -d
```

- Frontend on port **8080**, backend on **8000**, Postgres on **5432** (with a named volume).
- Put a TLS-terminating reverse proxy (Caddy, nginx, or your cloud LB) in front of ports 8080/8000.
- Update with `git pull && docker compose up --build -d`. Data persists in the `postgres-data` volume.

---

## Option B — Render (managed, one-click blueprint)

1. Push the repo to GitHub.
2. In Render: **New → Blueprint**, select the repo. Render reads [`render.yaml` (repo root)](../render.yaml)
   and provisions a Postgres database, the backend web service, and the frontend web service.
3. In the backend service's **Environment**, set:
   - `CORS_ORIGINS` → your frontend service URL (e.g. `https://lms-bridge-frontend.onrender.com`)
   - `ANTHROPIC_API_KEY` (or switch `LLM_PROVIDER`/keys as needed)
4. In the frontend (and marketing) service, set `API_BASE_URL` → `https://<backend-url>/api/v1` (runtime env), then restart. Also set the backend's `TOOL_BASE_URL` / `FRONTEND_BASE_URL`.

`DATABASE_URL` and `SECRET_KEY` are wired automatically by the blueprint.

---

## Option C — Railway

1. **New Project → Deploy from GitHub repo.** Railway uses [`infra/railway.json`](../infra/railway.json)
   to build `backend/Dockerfile`.
2. Add the **PostgreSQL** plugin; Railway injects a connection string. Map it to `DATABASE_URL`
   (use the `postgresql+psycopg://` scheme — adjust the provided URL's prefix).
3. Set `SECRET_KEY`, `APP_ENV=production`, `CORS_ORIGINS`, and LLM keys in **Variables**.
4. Deploy the frontend as a second service (Dockerfile `frontend/Dockerfile`) and set the
   runtime env `API_BASE_URL` to the backend's public URL + `/api/v1`.

---

## Option D — Fly.io

```bash
# Backend
fly launch --no-deploy -c infra/fly.backend.toml
fly postgres create --name lms-bridge-db
fly postgres attach lms-bridge-db -a lms-bridge-backend   # sets DATABASE_URL
fly secrets set SECRET_KEY=$(openssl rand -hex 32) APP_ENV=production -a lms-bridge-backend
fly deploy -c infra/fly.backend.toml

# Frontend: build once, set API_BASE_URL at runtime (no rebuild to repoint)
docker build -t registry.fly.io/lms-bridge-frontend ./frontend
fly secrets set API_BASE_URL=https://lms-bridge-backend.fly.dev/api/v1 -a lms-bridge-frontend
```

> Note: the bundled `DATABASE_URL` from Fly Postgres uses the `postgres://` scheme. Convert it to
> `postgresql+psycopg://…` for SQLAlchemy (the `psycopg` v3 driver is already a dependency).

---

## Option E — Kubernetes / ECS / generic container platform

Build and push the two images:

```bash
docker build -t <registry>/lms-bridge-backend:latest ./backend
docker build -t <registry>/lms-bridge-frontend:latest ./frontend  # set API_BASE_URL at runtime
docker push <registry>/lms-bridge-backend:latest
docker push <registry>/lms-bridge-frontend:latest
```

Then:

- Run the **backend** as a Deployment (2+ replicas; it is stateless). Provide env via Secret/ConfigMap.
  Use the container's existing startup command (migrate → seed-if-empty → uvicorn), or run
  `alembic upgrade head` as an init container / Job and start uvicorn directly in the main container.
- Run the **frontend** as a Deployment (bundled nginx); set env `API_BASE_URL` to the backend URL.
- Provision **PostgreSQL** (RDS, Cloud SQL, or an operator) and inject `DATABASE_URL`.
- Expose via Ingress/ALB with TLS. Set the liveness/readiness probe to `GET /api/v1/health`.

---

## Running migrations manually

The containers migrate automatically, but you can run migrations yourself:

```bash
# inside the backend container or a venv with DATABASE_URL set
alembic upgrade head            # apply
alembic revision --autogenerate -m "describe change"   # create a new migration after model changes
alembic downgrade -1            # roll back one
```

## Observability

- **Health:** `GET /api/v1/health` returns app version, env, selected LLM/Brightspace adapters,
  and database connectivity — wire it to your platform's health check.
- **Logs:** structured stdout logging (configurable via `LOG_LEVEL`); collect with your platform's
  log aggregator.

## Zero-downtime updates

1. Build and push new images (CI does this on every push to `main`).
2. Apply migrations (backwards-compatible migrations first; the startup step is idempotent).
3. Roll out the new backend, then the frontend. Because the API is versioned under `/api/v1`,
   you can introduce `/api/v2` alongside it for breaking changes.
