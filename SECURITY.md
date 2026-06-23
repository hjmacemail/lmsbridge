# Security Policy

LMS Bridge is built to run inside an institution's own infrastructure with the institution's own
AI key, so student data stays under institutional control. This document summarizes the security
posture and how to report a vulnerability. For data-flow and procurement detail see
[`docs/COMPLIANCE.md`](docs/COMPLIANCE.md) and [`docs/PRIVACY_AND_SELF_HOSTING.md`](docs/PRIVACY_AND_SELF_HOSTING.md).

## Reporting a vulnerability

Please report security issues privately — do **not** open a public issue for an exploitable bug.

- Email: **security@lmsbridge.app** (or the address in `CITATION.cff` if that is unattended).
- Or use GitHub's **"Report a vulnerability"** (Security Advisories) on
  `https://github.com/hjmacemail/lmsbridge`.

Include steps to reproduce and impact. We aim to acknowledge within 5 business days and to credit
reporters who request it. As an AGPL project run by each institution, patches are released on the
public repository; self-hosters should track releases and apply updates.

## Security posture

Authentication & integration
- LMS integration uses **LTI 1.3 / LTI Advantage** — there are **no shared secrets**. The platform
  is verified against its published **JWKS**; the tool signs service calls with its own RSA keypair.
- Application sessions use signed **JWT** access tokens (`SECRET_KEY`, HS256) with role claims.
- The launch flow validates signature, `iss`, `aud`, `nonce` (single-use, anti-replay), `exp`,
  deployment id, LTI version, and `azp` — covered by an automated conformance test suite.

Authorization
- **Role-based access control** (student / instructor / institution-admin / platform-operator).
- **Per-course authorization**: instructor endpoints (roster, grades, materials, analytics) verify
  the caller actually belongs to that course — preventing cross-course / cross-tenant data access
  (IDOR). Covered by tests.
- **Multi-tenant isolation**: each LMS registration maps to its own tenant; data is tenant-scoped.

Data protection
- **Data minimization for AI**: the model receives concept, answer text, misconception, and
  instructor-provided material excerpts — **not** names, emails, or LMS user ids. A PII-minimization
  layer is an enforced safety net.
- **Bring-your-own AI key**: inference runs under the institution's own provider contract; with
  self-hosting, student data never leaves the institution's boundary.
- Per-tenant secrets (e.g. AI keys) are stored **encrypted at rest** (Fernet, derived from
  `SECRET_KEY`). Transport is HTTPS/TLS (terminated by your proxy or PaaS).
- No silent telemetry or analytics phone-home.

Operational
- Reproducible **Docker** images; pinned dependencies; **CI** runs linting, type checks, and the
  test suite (including LTI conformance + authorization tests) on every change.
- Database changes ship as reviewed **Alembic migrations**.

## Hardening checklist for self-hosters

- Set a strong, unique `SECRET_KEY` (`openssl rand -hex 32`) and keep it secret.
- Serve only over **HTTPS**; set `TOOL_BASE_URL` / `FRONTEND_BASE_URL` to your real `https://` host.
- Restrict `CORS_ORIGINS` to your own front-end origins.
- Use a managed Postgres with backups and encryption at rest; restrict network access to the DB.
- Keep `DEPLOYMENT_MODE=community` unless you intentionally run a multi-tenant service.
- Rotate the AI provider key per your institution's policy; review your provider's data-retention
  settings (e.g. disable training on your data).
- Subscribe to repository releases and apply security updates promptly.

## Supported versions

Security fixes target the latest released version on the default branch. Pin a release tag for
production and upgrade forward to receive fixes.
