# LMS Bridge — Learning Mastery Support

*Bridge early gaps before they widen.*

**Free, open-source AI-guided remediation for undergraduate STEM — install it in your own LMS.**

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](./LICENSE)

LMS Bridge converts LMS learning analytics into timely, pedagogically-constrained remediation.
When a student struggles on a formative assessment, the system detects the likely concept-level
misconception and generates a tailored, interactive tutor session — built on retrieval practice,
Socratic scaffolding, and mastery-based progression. **It diagnoses and guides; it never hands
over answers.**

**Any institution can self-host it for free.** It installs into your LMS via LTI 1.3 (Canvas,
Blackboard, Brightspace, Moodle), runs on **your own AI provider + key** so student data stays
under your control, and is licensed under **AGPL-3.0** (see [Licensing](#licensing)). There is no
per-student fee and no size limit — optional commercial support/hosting is available for those who
want it ([`COMMERCIAL.md`](./COMMERCIAL.md)).

### Deployment modes

LMS Bridge runs in one of two modes, set by `DEPLOYMENT_MODE` (default **`community`**):

- **`community`** *(default — self-hosting)*: a single institution. Launches are **never
  license-gated**, there are no sales/leads surfaces, and your admin manages everything
  (including your LMS registration). This is what you get out of the box.
- **`hosted`**: multi-tenant SaaS run by an operator — enables the platform-operator role, lead
  capture, and per-tenant license/subscription enforcement. Only needed if *you* run a shared
  service for many institutions.

---

## Table of contents

- [What's in the box](#whats-in-the-box)
- [Architecture at a glance](#architecture-at-a-glance)
- [Quick start (Docker — recommended)](#quick-start-docker--recommended)
- [Quick start (local dev, no Docker)](#quick-start-local-dev-no-docker)
- [Demo accounts](#demo-accounts)
- [Configuration](#configuration)
- [Swapping the LLM provider](#swapping-the-llm-provider)
- [Connecting real Brightspace](#connecting-real-brightspace)
- [Deploying online](#deploying-online)
- [Testing, linting & CI](#testing-linting--ci)
- [Project layout](#project-layout)
- [Security, privacy & FERPA notes](#security-privacy--ferpa-notes)

---

## What's in the box

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend API** | FastAPI (Python 3.10+), SQLAlchemy 2, Alembic | Domain model, remediation engine, REST API, JWT auth + RBAC |
| **Frontend** | React 18 + TypeScript + Vite | Student remediation experience + multi-tab instructor console |
| **Course materials** | pypdf / python-docx extraction | Instructor uploads (PDF/DOCX/MD/text) that **ground** the AI in the course's own content |
| **Database** | PostgreSQL (SQLite for local/tests) | Persistence with versioned migrations |
| **LLM layer** | Provider-agnostic abstraction | Anthropic / OpenAI / Azure OpenAI / deterministic mock |
| **LMS integration** | **LTI 1.3 / LTI Advantage** tool provider | Installs into Blackboard, Brightspace, Canvas, Moodle: SSO launch, AGS, NRPS, Deep Linking + Brightspace Valence scaffold + seeded mock |
| **Sales platform** | Static marketing site + lead-capture API | Landing page, pricing, demo/purchase form → `/api/v1/leads` |
| **Ops** | Docker, docker-compose, GitHub Actions | One-command stack, CI, cloud-agnostic deploy configs |

### LMS integration (LTI 1.3) and the sales site

LMS Bridge ships a real **LTI 1.3 / LTI Advantage** tool provider (`backend/app/lti/`), so it
installs into any compliant LMS from a single integration — OIDC SSO launch, id_token validation
against the platform JWKS, just-in-time user/course provisioning, and the **AGS** (grades),
**NRPS** (roster), and **Deep Linking** services. See **[`docs/INSTALL_LTI.md`](docs/INSTALL_LTI.md)**
for per-LMS setup, and **[`docs/LMS_INTEGRATION_AND_BUSINESS_MODEL.md`](docs/LMS_INTEGRATION_AND_BUSINESS_MODEL.md)**
for the integration + go-to-market strategy. A polished **marketing/sales site** lives in
`marketing/` (served at **http://localhost:8090** in the stack) with pricing, a buy/demo flow, and
an install guide; its form posts to a public lead-capture endpoint that admins review at
`GET /api/v1/leads`.

### Data privacy, bring-your-own-AI, and self-hosting

Addressing the top institutional concern — student-data confidentiality — each institution
(tenant) can run inference through **its own model and API key** (Azure OpenAI / OpenAI / Anthropic
/ local), configured admin-only under the console's **AI & Privacy** tab (`/api/v1/tenants/me/ai`).
Keys are **encrypted at rest** and never returned. A **PII-minimization** layer redacts identifiers
from everything sent to the model, an **"external AI off"** switch prevents live student content
from leaving for a commercial API, and a **self-hosted profile**
(`infra/docker-compose.selfhosted.yml`) runs the entire stack inside the institution's own cloud so
no student data reaches the vendor at all. Full details, deployment models, and a procurement
checklist are in **[`docs/PRIVACY_AND_SELF_HOSTING.md`](docs/PRIVACY_AND_SELF_HOSTING.md)**.

## Architecture at a glance

```
                 ┌────────────────────────────────────────────────────┐
                 │                    LMS Bridge                        │
  Brightspace    │                                                     │
  (Valence API   │   ┌────────────┐   ┌──────────────┐                 │
   or mock)  ───────▶│  Sync /    │──▶│  Ingestion   │                 │
                 │   │  Adapter   │   │  pipeline    │                 │
                 │   └────────────┘   └──────┬───────┘                 │
                 │                           │ updates mastery (EWMA)  │
                 │                           ▼                         │
                 │                    ┌──────────────┐                 │
                 │   at-risk concept  │  Remediation │  pedagogically  │
                 │   ───────────────▶ │  engine      │──┐ constrained  │
                 │                    └──────────────┘  │ prompts      │
                 │                                       ▼             │
                 │                            ┌──────────────────┐     │
                 │                            │  LLM provider    │     │
                 │                            │ (mock/anthropic/ │     │
                 │                            │  openai/azure)   │     │
                 │                            └──────────────────┘     │
                 │   ┌──────────────┐                                  │
   Student  ─────────│  REST API    │  JWT + role-based access         │
   Instructor ───────│  (FastAPI)   │                                  │
                 │   └──────┬───────┘                                  │
                 └──────────┼─────────────────────────────────────────┘
                            ▼
                   React SPA (student + instructor UIs)
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full design, data model, and the
pedagogical guardrails that constrain the AI.

### Key capabilities

- **Detailed LMS analytics (mock today, real LMS later).** The mock Brightspace feed simulates
  what an institution's LMS provides via API or export: a standard plan of 9 assessments per
  course (5 assignments, 2 quizzes, 2 exams), per-question scores tagged to concepts, rubric-level
  criteria with instructor feedback, and engagement signals (attempts, time-on-task, lateness).
  A real feed only has to populate the same shape — nothing downstream changes.
- **Multiple-choice answer-level diagnosis.** Quizzes and exams are multiple-choice: the feed
  carries each question, the student's selected option, and the correct option. Because every
  distractor is authored to reveal a specific misconception, the *exact wrong option a student
  chose* is the signal the engine uses. The remediation prompt cites the student's actual wrong
  answers — "chose X (correct: Y) → likely misconception: …" — so the AI's "what to focus on" is
  justified by real responses. Instructors can inspect every answer in the student drill-down.
- **Instructor uploads course material → AI grounding.** Instructors upload PDF/DOCX/Markdown/text
  (syllabi, lecture notes, problem sets). The text is extracted and the most relevant excerpts are
  injected into the remediation prompt, so generated activities use the course's own notation,
  terminology, and examples. Each module records which materials grounded it, for transparency.
- **Rich instructor console.** A tabbed dashboard with: overview (class concept-risk), a student
  roster with per-student drill-down (mastery, every assessment result, modules), per-assessment
  and rubric breakdowns, a course-material library, class-wide remediation visibility (every
  module, activity, student response, and AI feedback), and one-click CSV export.
- **Interactive AI-tutor sessions (not worksheets).** Each remediation is a live, turn-by-turn
  Socratic dialogue the student completes with the AI tutor — opened with their specific wrong
  answer, grounded in course material, advancing through learning checkpoints, and ending only when
  the tutor judges the misconception resolved. Completing a session raises the student's mastery.
  Instructors can read the full transcript in the remediation tab.
- **Per-assessment adaptive control.** Each assessment has an enable/disable toggle (admin /
  instructor): disabled assessments are still recorded and shown in analytics, but their feedback
  no longer affects mastery or triggers remediation. A one-click **Recompute** replays only the
  enabled assessments (chronologically, for a deterministic estimate) so the change applies
  retroactively to the whole class.

---

## Quick start (Docker — recommended)

**Prerequisites:** Docker + Docker Compose.

### Option A — Prebuilt images, no build (fastest)

Pulls published images from the GitHub Container Registry. You don't even need
the full source tree — just one compose file:

```bash
curl -fsSLO https://raw.githubusercontent.com/hjmacemail/lmsbridge/main/docker-compose.prod.yml
curl -fsSL  https://raw.githubusercontent.com/hjmacemail/lmsbridge/main/.env.example -o .env
# edit .env (defaults work out of the box: mock LLM + mock Brightspace)
docker compose -f docker-compose.prod.yml up -d
```

> Requires that a release has been published — see [`PUBLISHING.md`](./PUBLISHING.md).

### Option B — Build from source

```bash
# 1. Clone and configure
git clone https://github.com/hjmacemail/lmsbridge.git && cd lmsbridge
cp .env.example .env            # defaults work out of the box (mock LLM + mock Brightspace)

# 2. Bring up the whole stack (db + backend + frontend)
docker compose up --build
```

That's it. On first boot the backend runs migrations and seeds demo data automatically.

- Frontend: **http://localhost:8080**
- API + interactive docs: **http://localhost:8000/docs**
- Health check: **http://localhost:8000/api/v1/health**

Log in with one of the [demo accounts](#demo-accounts).

---

## Quick start (local dev, no Docker)

**Prerequisites:** Python 3.10+ and Node 18+.

### Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Uses SQLite by default — no database server needed.
alembic upgrade head            # create tables
python -m app.scripts.seed      # seed demo courses, students, and remediation
uvicorn app.main:app --reload   # http://localhost:8000/docs
```

### Frontend

```bash
cd frontend
npm install
npm run dev                     # http://localhost:5173  (proxies /api to :8000)
```

Or use the convenience `Makefile` from the repo root:

```bash
make backend-install
make migrate
make backend-seed
make backend-run        # in one terminal
make frontend-install
make frontend-run       # in another terminal
```

Run `make help` to see all targets.

---

## Demo accounts

The seed script (`python -m app.scripts.seed`) creates:

| Role | Email | Password |
|------|-------|----------|
| Student | `ava.chen@student.example.edu` | `student123` |
| Instructor | `instructor@example.edu` | `instructor123` |
| Institution admin | `admin@example.edu` | `admin123` |
| Platform operator *(hosted mode only)* | `platform@lmsbridge.app` | `platform123` |

In `community` mode the institution admin (`admin@example.edu`) runs everything; the platform
operator account only matters when running in `hosted` (multi-tenant) mode.

The student already has auto-generated remediation modules waiting (because the seeded
Brightspace mock includes low scores on early concepts). The instructor can view per-concept
class risk and trigger a fresh Brightspace sync from the dashboard.

---

## Configuration

All configuration is via environment variables (see [`.env.example`](.env.example) for the
full annotated list). The most important ones:

| Variable | Default | Notes |
|----------|---------|-------|
| `APP_ENV` | `development` | `development` / `staging` / `production` |
| `DEPLOYMENT_MODE` | `community` | `community` (self-host, no license gate) / `hosted` (multi-tenant SaaS) |
| `DATABASE_URL` | SQLite file | Set to a `postgresql+psycopg://…` URL in production |
| `SECRET_KEY` | dev value | **Must** be a strong random value in production (`openssl rand -hex 32`) |
| `CORS_ORIGINS` | localhost | Comma-separated allowed origins |
| `LLM_PROVIDER` | `mock` | `mock` / `anthropic` / `openai` / `azure_openai` |
| `BRIGHTSPACE_ADAPTER` | `mock` | `mock` / `valence` |
| `REMEDIATION_TRIGGER_THRESHOLD` | `0.7` | Concept score at/below which remediation triggers |
| `MASTERY_THRESHOLD` | `0.85` | Score required to mark a concept mastered |

## Swapping the LLM provider

The system never depends on a specific vendor. To use a real model, set `LLM_PROVIDER` and the
matching credentials, then install the optional SDK:

```bash
# Anthropic
pip install -e ".[anthropic]"
export LLM_PROVIDER=anthropic LLM_MODEL=claude-3-5-sonnet-latest ANTHROPIC_API_KEY=sk-...

# OpenAI
pip install -e ".[openai]"
export LLM_PROVIDER=openai LLM_MODEL=gpt-4o OPENAI_API_KEY=sk-...

# Azure OpenAI (common for university-approved, compliant deployments)
pip install -e ".[openai]"
export LLM_PROVIDER=azure_openai AZURE_OPENAI_API_KEY=... \
       AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com \
       AZURE_OPENAI_DEPLOYMENT=your-deployment
```

If a provider is selected but its credentials are missing, the system logs a warning and falls
back to the deterministic mock so the app never crashes.

## Connecting real Brightspace

Set `BRIGHTSPACE_ADAPTER=valence` and fill the `BRIGHTSPACE_*` variables. The Valence adapter
(`backend/app/integrations/brightspace/valence.py`) is a structured scaffold that documents
exactly where to wire D2L authentication (app/user-key HMAC or OAuth2), classlist retrieval,
and grade polling with a concept-to-grade-item mapping. Until that is completed it logs a
warning and returns no results, so it is safe to enable in staging. See
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md#brightspace-integration) for the integration checklist.

---

## Deploying online

LMS Bridge ships Docker images and ready-to-use configs for several hosts. Full
step-by-step instructions are in [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md), and a complete
**go-live runbook for Render + a custom domain** (the recommended path for a first public pilot) is
in [`docs/GO_LIVE_RENDER.md`](docs/GO_LIVE_RENDER.md). The short version:

**Render (one-click blueprint):** push to GitHub, then in Render choose *New → Blueprint* and
point it at this repo. It reads [`render.yaml`](render.yaml) and provisions Postgres,
the backend, the frontend, and the marketing site with automatic HTTPS. After the first deploy,
set the service URLs (`TOOL_BASE_URL`, `FRONTEND_BASE_URL`, `CORS_ORIGINS`, and `API_BASE_URL` on
the frontend/marketing) and your AI key in the dashboard. The frontend reads its API URL at
**runtime**, so re-pointing it needs only a restart — no rebuild.

**Railway:** uses [`infra/railway.json`](infra/railway.json). Add a Postgres plugin, set
`DATABASE_URL`, deploy.

**Fly.io:** `fly deploy -c infra/fly.backend.toml` for the API; attach Fly Postgres.

**Any VM / Kubernetes:** build and run the two Dockerfiles (`backend/Dockerfile`,
`frontend/Dockerfile`) behind a reverse proxy. `docker compose` works unchanged on a single host.

In every case the backend container runs migrations and an idempotent seed on startup.

---

## Testing, linting & CI

```bash
cd backend
pytest                 # unit + integration + end-to-end pipeline tests
ruff check app tests   # lint
mypy app               # type-check

cd ../frontend
npm run build          # type-checks (tsc) and builds
```

GitHub Actions ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) runs the backend test
suite, lint, type-check, the frontend build, and Docker image builds on every push and PR.

## Project layout

```
.
├── backend/                 FastAPI service
│   ├── app/
│   │   ├── api/routes/       REST endpoints (auth, courses, assessments,
│   │   │                      remediation, students, analytics, health)
│   │   ├── core/             config, logging, security
│   │   ├── db/               SQLAlchemy base + session
│   │   ├── models/           ORM domain model
│   │   ├── schemas/          Pydantic request/response models
│   │   ├── services/         mastery, remediation engine, ingestion, sync
│   │   ├── llm/              provider-agnostic LLM layer + providers
│   │   ├── integrations/     Brightspace adapter (mock + Valence scaffold)
│   │   ├── pedagogy/         pedagogically-constrained prompt templates
│   │   └── scripts/seed.py   demo data + pipeline exercise
│   ├── alembic/              database migrations
│   └── tests/                pytest suite
├── frontend/                 React + TypeScript SPA
│   └── src/{api,pages,components,context,types}
├── infra/                    deploy configs (render, railway, fly, nginx)
├── docs/                     ARCHITECTURE.md, DEPLOYMENT.md
├── docker-compose.yml        full local/prod-like stack
└── Makefile                  developer convenience targets
```

## Security, privacy & FERPA notes

- **Pedagogical constraint.** The LLM is governed by a system prompt that forbids answer
  delivery and requires active, learning-science-based engagement. Prompts live in
  `backend/app/pedagogy/prompts.py` and are reviewable/versionable.
- **Data governance.** The provider abstraction lets all student-data processing stay inside
  institution-approved infrastructure (e.g. Azure OpenAI in a compliant tenant). No model
  training on identifiable student data occurs.
- **Access control.** JWT auth with role-based guards (student / instructor / admin). Students
  can only access their own dashboard and modules.
- **Secrets.** Never commit `.env`. Set `SECRET_KEY` and API keys via your host's secret manager.
- This is a research-pilot platform; complete a security and privacy review with your
  institution before processing real student records.

---

## Licensing

LMS Bridge is **free and open-source software under the GNU AGPL-3.0** ([`LICENSE`](./LICENSE)).
Any institution may download, self-host, modify, and use it at no cost and with no size limit.
You bring your own AI key, so the software is free and your AI usage runs under your own contract.

AGPL asks one main thing in return: if you **modify** LMS Bridge and run it as a network service,
you must make your modified source available to its users. Unmodified or internal use carries no
extra obligation. A separate **commercial/OEM license and paid support/hosting** are available for
anyone who needs them — see [`COMMERCIAL.md`](./COMMERCIAL.md).

## Maintainer & citation

Built and maintained by **Hasan Aljabbouli**, New York University —
[info@lmsbridge.app](mailto:info@lmsbridge.app).
*(Replace the surname and add your GitHub/LinkedIn/Scholar links.)*

Using LMS Bridge in research or teaching? Please cite it — see [`CITATION.cff`](./CITATION.cff).
Running it somewhere? Add your institution to [`ADOPTERS.md`](./ADOPTERS.md) via a pull request.

---

*LMS Bridge augments instructor feedback and existing resources — it does not replace any core
LMS functionality. Faculty retain full control over content, grading, and learning outcomes.*
