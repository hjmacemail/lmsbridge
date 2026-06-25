# White-label branding (run an instance under another name)

LMS Bridge can present the **Sage** app under a partner's product name and logo — for example a
TWAS-hosted instance shown as **"TWAS Learning"** — without forking the project. This is intended
for a separate instance, a subdomain, or even a single shareable link. The upstream product stays
unchanged.

Under AGPL-3.0 you may rebrand freely; the only requirement is that the **"source" link stays
visible**. The Sage header keeps a small "· by LMS Bridge" link to the source for exactly this
reason — you can change the wording (see `BRAND_ATTRIBUTION`) but should keep a link to the code.

## Option A — a dedicated instance / subdomain (recommended)

Set any of these environment variables on the **frontend** container. The entrypoint injects them
at startup; nothing needs rebuilding.

| Variable | Effect | Example |
| --- | --- | --- |
| `BRAND_NAME` | Product name in the header and welcome screen | `TWAS Learning` |
| `BRAND_TAGLINE` | Subtitle on the sign-in screen | `Free AI-guided STEM learning for the TWAS community.` |
| `BRAND_ACCENT` | Header colour (hex) | `#0e7a4f` |
| `BRAND_LOGO_URL` | Logo image shown in the header (replaces the default mark) | `https://example.org/twas-logo.svg` |
| `BRAND_ATTRIBUTION` | The text of the source-link after the name | `by LMS Bridge` |

Example (docker compose):

```yaml
  frontend:
    image: ghcr.io/hjmacemail/lmsbridge-frontend:latest
    environment:
      BRAND_NAME: "TWAS Learning"
      BRAND_TAGLINE: "Free, AI-guided STEM learning for the TWAS community."
      BRAND_ACCENT: "#0e7a4f"
      BRAND_LOGO_URL: "https://example.org/twas-logo.svg"
```

Point a subdomain (e.g. `learn.twas.org`) at this instance and members see a fully TWAS-branded app.

## Option B — a "special link" preset (fastest demo)

A built-in preset can be switched on with a query parameter, so you can show a branded version on an
existing deployment without redeploying:

```
https://<your-app>/sage?brand=twas
```

The choice is remembered for the browser session. Presets live in
`frontend/src/lib/brand.ts` (`PRESETS`) — add your own there and rebuild, or just use Option A.

## What is NOT changed

Branding affects only the user-facing name, logo, accent, tagline, and the attribution wording. It
does not change data ownership, the API, or the source link. For a permanent partner brand, prefer
Option A so the configuration lives with the deployment.
