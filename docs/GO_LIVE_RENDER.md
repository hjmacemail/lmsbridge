# Go Live on Render (+ custom domain)

A step-by-step path from the repo to a public, HTTPS deployment that a real LMS can connect to,
plus how to buy and wire up a domain. Budget ~30–45 minutes for the first deploy.

---

## 0. What you'll end up with

Three public services (Render gives each free automatic HTTPS), backed by managed Postgres:

| Service | Default Render URL | With your domain |
|---------|--------------------|------------------|
| Backend API | `lms-bridge-backend.onrender.com` | `api.yourdomain.edu` |
| Student/instructor app | `lms-bridge-frontend.onrender.com` | `app.yourdomain.edu` |
| Marketing / sales site | `lms-bridge-marketing.onrender.com` | `www.yourdomain.edu` (root) |

You do **not** need a domain to do the first LTI test — the free `*.onrender.com` URLs are already
HTTPS. Add the domain when you're ready to show people.

---

## 1. Push the repo to GitHub

Render deploys from a Git repo. Create a repo and push the project (the `.git` folder may already
exist; otherwise `git init`, commit, and push).

## 2. Deploy with the blueprint

1. In Render: **New → Blueprint**, connect your GitHub, pick the repo.
2. Render reads [`render.yaml` (repo root)](../render.yaml) and proposes: a Postgres database +
   three web services. Click **Apply**.
3. First build takes a few minutes. The database and `SECRET_KEY` are provisioned automatically.

## 3. Wire the service URLs (one-time)

Because the services need each other's URLs, set these in each service's **Environment** tab after
the first deploy, then **Manual Deploy → Deploy latest** (or just Save, which redeploys):

**backend** (`lms-bridge-backend`):
- `TOOL_BASE_URL` = `https://lms-bridge-backend.onrender.com`
- `FRONTEND_BASE_URL` = `https://lms-bridge-frontend.onrender.com`
- `CORS_ORIGINS` = `https://lms-bridge-frontend.onrender.com,https://lms-bridge-marketing.onrender.com`
- `LLM_PROVIDER` + the matching key when you're ready for real AI (leave `mock` to demo).

**frontend** (`lms-bridge-frontend`):
- `API_BASE_URL` = `https://lms-bridge-backend.onrender.com/api/v1`

**marketing** (`lms-bridge-marketing`):
- `API_BASE_URL` = `https://lms-bridge-backend.onrender.com/api/v1`
- `APP_BASE_URL` = `https://lms-bridge-frontend.onrender.com` (powers the "Try the live demo" button)

> The frontend/marketing read `API_BASE_URL` at **runtime**, so changing it just needs a restart —
> no rebuild. The backend runs migrations + seeds the demo data automatically on boot.

## 4. Verify

- `https://lms-bridge-backend.onrender.com/api/v1/health` → `{"status":"ok",...}`
- Open the frontend URL, sign in with the demo accounts (e.g. `admin@example.edu / admin123`).
- Open the marketing URL; submit the demo form; confirm the lead appears under
  `GET /api/v1/leads` (as admin).

> **Note on Render's free tier:** services sleep after inactivity and the free Postgres expires
> after ~90 days. Fine for a pilot/demo; move to paid instances + a persistent database before a
> real rollout.

---

## 5. Buy and connect a custom domain

### Where to buy
Any registrar works; good low-cost options: **Cloudflare Registrar** (at-cost pricing, free DNS),
**Porkbun**, or **Namecheap**. A `.com` is ~$10–12/yr; if you're at an institution you may instead
get a subdomain of the school's domain from IT (e.g. `lmsbridge.it.youruni.edu`) — that also works.

### What to name it
Pick something short and product-like, e.g. `lmsbridge.app` / `lmsbridge.io` / `getlmsbridge.com`.
Plan three hostnames:
- `app.<domain>` → the student/instructor app
- `api.<domain>` → the backend
- `www.<domain>` (and root) → the marketing site

### Wire it up on Render
1. In each Render service: **Settings → Custom Domains → Add** the matching hostname
   (`api.<domain>` on the backend, `app.<domain>` on the frontend, `www.<domain>` on marketing).
2. Render shows the DNS record to create. At your registrar's DNS, add:
   - `api`  → **CNAME** → `lms-bridge-backend.onrender.com`
   - `app`  → **CNAME** → `lms-bridge-frontend.onrender.com`
   - `www`  → **CNAME** → `lms-bridge-marketing.onrender.com`
   - root `@` → use your registrar's ALIAS/ANAME (or a redirect to `www`) per Render's instructions.
3. Render issues TLS certificates automatically once DNS resolves (minutes to an hour).
4. **Update the env vars from step 3** to your domain:
   - backend `TOOL_BASE_URL` = `https://api.<domain>`, `FRONTEND_BASE_URL` = `https://app.<domain>`,
     `CORS_ORIGINS` = `https://app.<domain>,https://www.<domain>`
   - frontend & marketing `API_BASE_URL` = `https://api.<domain>/api/v1`
   - Redeploy.

---

## 6. Connect your LMS and run the pilot

1. Sign in to the app as an **admin** → **LMS (LTI)** tab.
2. **Canvas/Moodle:** copy the **Dynamic Registration URL** and paste it into the LMS's
   "register tool by URL" — done in one step.
   **Blackboard/Brightspace:** register the tool with the four URLs shown, then **+ Add LMS
   manually** with the issuer/client/deployment the LMS gives you.
3. In a sandbox **course**, add LMS Bridge as content (Deep Linking) and launch it — confirm SSO,
   roster, and grades flow.
4. Run the pilot in one course, measure outcomes, iterate.

Per-LMS detail: [`docs/INSTALL_LTI.md`](INSTALL_LTI.md). Deployment models & privacy for
procurement: [`docs/PRIVACY_AND_SELF_HOSTING.md`](PRIVACY_AND_SELF_HOSTING.md).

---

## Quick checklist

- [ ] Repo on GitHub
- [ ] Blueprint applied on Render (db + 3 services)
- [ ] Service URLs wired (`TOOL_BASE_URL`, `FRONTEND_BASE_URL`, `CORS_ORIGINS`, `API_BASE_URL` ×2)
- [ ] `/api/v1/health` returns ok; demo login works
- [ ] (Optional) Domain bought + CNAMEs added + env vars switched to the domain
- [ ] AI provider/key set (or kept on `mock` for demo)
- [ ] LMS registered (dynamic or manual) and a test launch succeeds
