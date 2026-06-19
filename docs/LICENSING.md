# LMS Bridge — Licensing & Entitlements

**LMS Bridge is free and open-source software (AGPL-3.0). The default deployment does not gate
or meter anything.** See [`../LICENSE`](../LICENSE) and [`../COMMERCIAL.md`](../COMMERCIAL.md).

## 0. Default: community mode — no gating

With `DEPLOYMENT_MODE=community` (the default), there is **no license check at all**:
`authorize_launch` always allows, no student is ever blocked, there is no subscription, seat
limit, or "tool unavailable" screen, and the **Licenses**/**Leads** surfaces are hidden. A
self-hosting institution just runs it. Everything in the rest of this document applies **only**
if an operator deliberately runs in `hosted` mode (or installs a signed license file) — for
example, if *you* offer a managed multi-tenant service. It is optional plumbing for the
commercial/hosted path, not something a free self-hoster ever touches.

The entitlement code is gated by `license_service.enforcement_active()`, which is `False` in
community mode and when `LICENSE_ENFORCEMENT_DISABLED=true`.

---

## 1. Hosted mode (optional) — per-institution subscriptions

Only when `DEPLOYMENT_MODE=hosted`. Entitlement is enforced **server-side** (not by the LMS):
each institution is one `Tenant`, checked on **every LTI launch**:

| Field | Meaning |
|------|---------|
| `subscription_status` | `active` / `trial` → allowed; `expired` / `suspended` / `canceled` → blocked |
| `plan` | `free` / `pilot` / `standard` / `enterprise` (label) |
| `seat_limit` | Max distinct students who may launch (`null` = unlimited) |
| `license_expires_at` | Hard cutoff; launches blocked after this instant |

When a launch is not entitled, the student/instructor sees a branded **“tool unavailable”**
page (with your `LICENSE_CONTACT_EMAIL`) instead of signing in. Seat enforcement only blocks
the **overflow** students (the first `seat_limit` by join order keep working) and never
blocks instructors or admins.

**Manage it:** sign in as the platform operator → **Licenses** tab. Set status / plan /
seats / expiry per institution. Institution admins see their own plan (read-only) on their
**Usage** tab. A Stripe webhook can flip `subscription_status` automatically (see the
business-model doc).

New tenants default to `trial`, so nobody is locked out the moment you deploy.

## 2. Signed license file (optional) — for commercial self-hosted customers

This is **only** relevant if you sell a commercial/OEM arrangement to a customer who self-hosts
and you want a contractual entitlement enforced offline (it is *not* used or needed for the free
AGPL self-host path). Entitlement travels in a **signed license token** (RS256 JWT) validated
at startup against your public key.

Vendor side (you), once:

```bash
# Generate your signing keypair — keep the private key secret, forever.
python -m app.scripts.mint_license keygen --out ./license_keys

# Issue a license for a customer
python -m app.scripts.mint_license issue \
  --private ./license_keys/license_private.pem \
  --customer "Acme University" --plan enterprise --seats 2500 --days 365
# -> prints the signed LICENSE_KEY token
```

Customer side — set two env vars and restart:

```
LICENSE_PUBLIC_KEY = <contents of license_public.pem>   # you ship this
LICENSE_KEY        = <the signed token you issued>
```

On boot the app verifies the token (signature + expiry). If it's missing, invalid, or
expired, the install is **unlicensed** and launches are blocked; seat/expiry otherwise come
from the token. The signing **private key is never shipped** — customers cannot self-issue.

## Bypass (dev/demo only)

`LICENSE_ENFORCEMENT_DISABLED=true` skips all gating. Never set this in production.

## Where it lives

- `app/services/license_service.py` — entitlement logic (SaaS + self-hosted, seat math).
- `app/scripts/mint_license.py` — vendor keygen + token issuance.
- `app/api/routes/lti.py` — launch enforcement + the blocked screen.
- `app/api/routes/tenants.py` — `GET /tenants/licenses`, `PUT /tenants/{id}/license`,
  `GET /tenants/license/status` (platform operator / institution admin).
