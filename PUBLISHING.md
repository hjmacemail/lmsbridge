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

## After go-live: how others install it

Once steps 1–3 are done, anyone can install LMS Bridge two ways.

### A. Run prebuilt images (no source, no build) — recommended

```bash
curl -fsSLO https://raw.githubusercontent.com/hjmacemail/lmsbridge/main/docker-compose.prod.yml
curl -fsSL  https://raw.githubusercontent.com/hjmacemail/lmsbridge/main/.env.example -o .env
# edit .env: set SECRET_KEY, your AI provider + key, public URLs
docker compose -f docker-compose.prod.yml up -d
```

### B. Build from source

```bash
git clone https://github.com/hjmacemail/lmsbridge.git
cd lmsbridge
cp .env.example .env   # edit it
docker compose up --build
```

App → http://localhost:8080 · API docs → http://localhost:8000/docs ·
Marketing site → http://localhost:8090

---

## Quick status of the distribution gap

| Requirement | State | Fixed by |
| --- | --- | --- |
| GitHub link resolves | ❌ 404 (private/unpushed) | Steps 1–2 |
| AGPL public source | ❌ not public | Step 2 |
| Downloadable/runnable artifact | ✅ prod compose + release workflow added | Step 3 publishes images |
| Links use the real repo URL | ✅ done in code | — |
