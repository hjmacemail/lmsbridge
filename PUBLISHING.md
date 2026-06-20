# Publishing & Go-Live Checklist

Everything in this repo is finished and runs locally. The only reason nobody can
install it yet is that **the source has not been made public**. The repo
`https://github.com/hjmacemail/lmsbridge` currently returns **404** to the
outside world — so the "View source" link, the AGPL source requirement, and the
clone-and-run install path all fail until you complete the steps below.

These are the steps **only you can do** (they require your GitHub/Render
credentials). Each is a few minutes.

---

## 1. Push the latest code to GitHub

You have local commits and uncommitted changes. Publish them:

```bash
cd "<your repo folder>"
git add -A
git commit -m "Publish: real repo URLs, prebuilt-image release workflow, prod compose"
git push origin main
```

> If `git push` says the remote is empty or rejects, the repo may not exist yet.
> Create it once at https://github.com/new with the name **lmsbridge** under the
> **hjmacemail** account, then `git push -u origin main`.

## 2. Make the repository PUBLIC

This is the single most important step — it's what makes the GitHub link work
and satisfies the AGPL-3.0 source-availability requirement.

1. Go to **https://github.com/hjmacemail/lmsbridge → Settings → General**.
2. Scroll to **Danger Zone → Change repository visibility → Make public**.
3. Confirm.

Verify: open https://github.com/hjmacemail/lmsbridge in a private/incognito
window. You should see the code, not a 404.

## 3. Cut the first release (publishes prebuilt images)

This produces the true "downloadable/executable" artifact — Docker images on
GHCR that institutions can run with **no build**.

```bash
git tag v1.0.0
git push origin v1.0.0
```

The `.github/workflows/release.yml` workflow then builds and pushes three images
to the GitHub Container Registry:

- `ghcr.io/hjmacemail/lmsbridge-backend:v1.0.0` (and `:latest`)
- `ghcr.io/hjmacemail/lmsbridge-frontend:v1.0.0`
- `ghcr.io/hjmacemail/lmsbridge-marketing:v1.0.0`

Watch it under the repo's **Actions** tab. When it finishes:

4. Go to your profile → **Packages**, open each `lmsbridge-*` package →
   **Package settings → Change visibility → Public**. (GHCR packages default to
   private even in a public repo; this makes `docker pull` work for everyone.)

Optional: create a GitHub **Release** from the `v1.0.0` tag (Releases → Draft a
new release → choose the tag) so there's a versioned download page with notes.

## 4. (Optional) Point the public site's links at the repo

If you host the marketing/app site on Render, set this env var on the
**marketing** and **frontend** services so "View source" links resolve:

```
SOURCE_URL = https://github.com/hjmacemail/lmsbridge
```

The code already defaults to this URL, so this is only needed if you previously
overrode it. Redeploy after changing.

---

## After go-live: how an institution installs it

> **Important — LMS Bridge is an LTI 1.3 tool, not a standalone website.** Students
> and instructors never visit it directly or "log in" — they open it from a link
> *inside their LMS course* (Canvas, Moodle, Brightspace, Blackboard). So
> installing it is **two stages**: (1) **host** the tool, then (2) **register** it
> in the LMS so it appears inside courses. The demo logins and `localhost` URLs
> below are for local preview only.

### Stage 1 — Host the tool (get it running on a public HTTPS URL)

The LMS will only talk to the tool over **HTTPS at a real domain** — it rejects
`http://` and `localhost`. So host it on a server/PaaS with TLS. Two ways:

**A. Prebuilt images (no source, no build) — recommended**

```bash
curl -fsSLO https://raw.githubusercontent.com/hjmacemail/lmsbridge/main/docker-compose.prod.yml
curl -fsSL  https://raw.githubusercontent.com/hjmacemail/lmsbridge/main/.env.example -o .env
# edit .env — set SECRET_KEY, your AI provider + key, and the PUBLIC HTTPS URLs:
#   TOOL_BASE_URL=https://lms-bridge.your-university.edu
#   FRONTEND_BASE_URL=https://lms-bridge.your-university.edu
docker compose -f docker-compose.prod.yml up -d
```

**B. Build from source**

```bash
git clone https://github.com/hjmacemail/lmsbridge.git
cd lmsbridge && cp .env.example .env   # edit it (same public URLs as above)
docker compose up --build
```

Put it behind a TLS-terminating reverse proxy (Caddy, nginx, Cloudflare Tunnel)
or deploy on a PaaS that terminates TLS for you — a one-click
[Render blueprint](./render.yaml) is included (see [`docs/GO_LIVE_RENDER.md`](./docs/GO_LIVE_RENDER.md)).

*Local preview only:* on your own machine the app is at http://localhost:8080,
API docs at http://localhost:8000/docs, marketing site at http://localhost:8090.
You can sign in with the [demo accounts](./README.md#demo-accounts) just to look
around — but that standalone login is **not** how real users reach it.

### Stage 2 — Register it in the LMS (the actual integration)

Once it's running at `https://YOUR-HOST`, the tool publishes everything an LMS
admin needs at `GET https://YOUR-HOST/api/v1/lti/config`:

| LMS form field | LMS Bridge URL |
| --- | --- |
| OIDC initiation / login | `https://YOUR-HOST/api/v1/lti/login` |
| Target Link / Launch URI | `https://YOUR-HOST/api/v1/lti/launch` |
| Redirect URI(s) | `https://YOUR-HOST/api/v1/lti/launch` |
| Public keyset (JWKS) | `https://YOUR-HOST/api/v1/lti/jwks` |
| Dynamic Registration (Canvas/Moodle one-click) | `https://YOUR-HOST/api/v1/lti/register` |

**Follow the exact click-by-click runbook for each LMS in
[`docs/INSTALL_LTI.md`](./docs/INSTALL_LTI.md)** (Canvas & Moodle support one-click
Dynamic Registration; Brightspace & Blackboard use manual registration). After
registration, add an LMS Bridge link to a course and launch it — single sign-on,
rostering (NRPS), and gradebook access (AGS) all work automatically. That
in-course experience is exactly what the simulated demo shows.

---

## Quick status of the distribution gap

| Requirement | State | Fixed by |
| --- | --- | --- |
| GitHub link resolves | ❌ 404 (private/unpushed) | Steps 1–2 |
| AGPL public source | ❌ not public | Step 2 |
| Downloadable/runnable artifact | ✅ prod compose + release workflow added | Step 3 publishes images |
| Links use the real repo URL | ✅ done in code | — |
