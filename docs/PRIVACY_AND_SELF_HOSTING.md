# Privacy, Data Governance & Self-Hosting

This document explains where student data lives, exactly what the AI sees, and the deployment
options institutions can choose to satisfy their confidentiality requirements. It is written to
support a procurement / privacy review (FERPA, DPA). *It is informational, not legal advice —
have your institution's counsel review any agreement.*

## 1. Deployment models — pick your comfort level

| Model | Who hosts the app | Who runs the AI | Where student data lives |
|-------|-------------------|-----------------|--------------------------|
| **Managed SaaS** | Vendor | Vendor (managed) | Vendor (as your processor, under a DPA) |
| **Bring-your-own-AI** | Vendor | **You** (your model/key) | App data with vendor; AI inference under **your** contract |
| **Self-hosted** | **You** (your cloud/VPC) | **You** | **Entirely within your boundary** |

You are not locked in — an institution can start managed for a pilot and move to BYO-AI or
self-hosted for production.

## 2. What the AI actually sees (data minimization)

The remediation engine and tutor are deliberately built so the model **does not need identifying
data**. To generate or run a session it receives:

- the **concept** being remediated,
- the student's **answer text** and the **misconception** their wrong option reveals,
- relevant **course-material excerpts** (instructor-provided),
- the running **session transcript**.

It does **not** receive names, emails, or LMS user IDs — those stay in the application database to
run the app, not to prompt the model. As an enforced safety net, a **PII-minimization layer**
(`app/core/privacy.py`, applied at the LLM boundary in `app/llm/guard.py`) redacts emails, long ID
numbers, and supplied names from every message before it leaves the process. It is **on by default**
and configurable per institution.

## 3. Bring-your-own AI (admin-configured)

An institution **admin** sets the model under **AI & Privacy** in the console (or
`PUT /api/v1/tenants/me/ai`):

- **Provider**: Azure OpenAI (recommended — runs in your tenant), OpenAI, Anthropic, a local model,
  or the platform default.
- **API key**: stored **encrypted at rest** (Fernet, key derived from `SECRET_KEY`) and **never
  returned** by the API — responses only indicate whether a key is set.
- With BYO-AI, inference happens under **your** vendor contract; student content never reaches a
  model endpoint the platform vendor controls.

### Privacy policy switches (per institution)

- **PII minimization** (default on) — redact identifiers from anything sent to the model.
- **External AI allowed** (default on; set off for strict environments) — when off, live student
  content is **never** sent to an external commercial API; the engine falls back to your
  self-hosted model or a safe local model instead of leaking.

## 4. Self-hosting (data never leaves your boundary)

Run the whole stack in your own cloud/VPC with your own database and model:

```bash
cp .env.example .env       # set a strong SECRET_KEY, your DATABASE_URL, and your AI provider
docker compose -f docker-compose.yml -f infra/docker-compose.selfhosted.yml up -d --build
```

The self-hosted profile (`infra/docker-compose.selfhosted.yml`) sets production mode, requires your
own AI endpoint, does **not** publish the database, and disables the public marketing site. Put the
backend behind your reverse proxy / SSO. In this model the vendor receives **no student data at
all** — you simply run the software.

## 5. Security & governance posture

- **Encryption**: secrets (AI keys) encrypted at rest; serve all traffic over TLS in production.
- **Access control**: JWT auth with role-based guards (student / instructor / admin). Students see
  only their own data; AI/privacy settings are admin-only.
- **Tenant isolation**: every institution is a tenant; courses, users, and AI config are scoped to
  it. Data is queried by tenant.
- **No training on student data**: student content is used only to generate that student's
  remediation; it is not used to train models.
- **Grades**: mastery is a **private learning aid**, never a grade. Any LMS gradebook write-back is
  a non-graded column.
- **Identity via LTI**: user identity comes from the LMS over LTI; the tool can pseudonymize the
  learner to the model.

## 6. Procurement checklist (what to prepare / request)

- **DPA** (for managed/BYO-AI models) describing roles, sub-processors, and data flows.
- **FERPA** alignment statement.
- **SOC 2** report and **accessibility (VPAT / WCAG)** statement.
- **Data residency** and **retention/deletion** terms.
- For LTI: **1EdTech LTI Advantage certification** and a **TrustEd Apps** (incl. Data Privacy)
  listing.

## 7. Where this lives in the code

| Concern | Location |
|---------|----------|
| PII redaction | `backend/app/core/privacy.py` |
| Secret encryption | `backend/app/core/crypto.py` |
| Privacy/external-AI guard | `backend/app/llm/guard.py` |
| Per-tenant model resolution | `backend/app/llm/tenant_factory.py` |
| Tenant + BYO-AI config | `backend/app/models/tenant.py`, `backend/app/api/routes/tenants.py` |
| Admin settings UI | `frontend/src/components/SettingsPanel.tsx` |
| Self-hosted profile | `infra/docker-compose.selfhosted.yml` |
