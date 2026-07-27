#!/usr/bin/env python3
"""Live production health check for LMS-Bridge.

Pings the deployed services and verifies they are up and correctly wired. Uses only the
Python standard library (no pip installs). Exits non-zero if any critical check fails, so
it can also be dropped into CI or a cron/uptime job.

Usage:
    python scripts/healthcheck_live.py
    python scripts/healthcheck_live.py --api https://api.lmsbridge.app \
        --app https://app.lmsbridge.app --www https://www.lmsbridge.app
"""
from __future__ import annotations

import argparse
import json
import ssl
import sys
import urllib.request
from urllib.error import HTTPError, URLError

TIMEOUT = 20
PASS, FAIL, WARN = [], [], []


def _get(url: str):
    """Return (status_code, body_text) or (None, error_string)."""
    req = urllib.request.Request(url, headers={"User-Agent": "lmsbridge-healthcheck/1.0"})
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except (URLError, TimeoutError, ssl.SSLError) as e:
        return None, str(e)


def ok(name: str):
    PASS.append(name); print(f"  [PASS] {name}")


def bad(name: str, detail: str = ""):
    FAIL.append(name); print(f"  [FAIL] {name}" + (f"  -- {detail}" if detail else ""))


def warn(name: str, detail: str = ""):
    WARN.append(name); print(f"  [WARN] {name}" + (f"  -- {detail}" if detail else ""))


def check_api(api: str):
    print(f"\n=== API  {api} ===")
    code, body = _get(f"{api}/api/v1/health")
    if code != 200:
        bad("health endpoint reachable (200)", f"HTTP {code}: {body[:120]}")
        return  # nothing else will work
    ok("health endpoint reachable (200)")
    try:
        h = json.loads(body)
    except json.JSONDecodeError:
        bad("health returns JSON", body[:120]); return
    ok("health returns JSON")
    (ok if h.get("status") == "ok" else bad)("status == ok")
    (ok if h.get("database") == "ok" else bad)("database connected")
    if h.get("llm_key_present") is True:
        ok(f"LLM key present (provider={h.get('llm_effective') or h.get('llm_provider')}, "
           f"model={h.get('llm_model')})")
    else:
        warn("LLM key present", "no key — engine will use the safe mock fallback")
    if h.get("llm_last_error"):
        warn("no recent LLM error", str(h.get("llm_last_error"))[:120])
    else:
        ok("no recent LLM error")

    code, body = _get(f"{api}/api/v1/lti/config")
    if code == 200 and "oidc_initiation_url" in body:
        ok("LTI config served (installable into an LMS)")
    else:
        bad("LTI config served", f"HTTP {code}: {body[:120]}")

    code, body = _get(f"{api}/api/v1/lti/jwks")
    if code == 200 and '"keys"' in body:
        ok("LTI JWKS keyset published")
    else:
        bad("LTI JWKS keyset published", f"HTTP {code}: {body[:120]}")


def check_site(label: str, url: str, must_contain: str | None = None):
    print(f"\n=== {label}  {url} ===")
    code, body = _get(url)
    if code == 200:
        ok(f"{label} reachable (200)")
        if must_contain and must_contain.lower() not in body.lower():
            warn(f"{label} contains expected marker", f"'{must_contain}' not found")
        elif must_contain:
            ok(f"{label} rendered expected content")
    else:
        bad(f"{label} reachable", f"HTTP {code}: {body[:120]}")


def main() -> int:
    p = argparse.ArgumentParser(description="LMS-Bridge live health check")
    p.add_argument("--api", default="https://api.lmsbridge.app")
    p.add_argument("--app", default="https://app.lmsbridge.app")
    p.add_argument("--www", default="https://www.lmsbridge.app")
    p.add_argument("--apex", default="https://lmsbridge.app",
                   help="apex domain (non-critical; warns if down)")
    a = p.parse_args()

    print("LMS-Bridge — live production health check")
    check_api(a.api)
    check_site("App (student/instructor SPA)", a.app, "lms bridge")
    check_site("Marketing site", a.www, "LMS Bridge")

    # Apex is a nice-to-have (depends on the ALIAS DNS record); don't fail the run on it.
    print(f"\n=== Apex (optional)  {a.apex} ===")
    code, _ = _get(a.apex)
    if code == 200:
        ok("apex domain resolves")
    else:
        warn("apex domain resolves", f"HTTP {code} — add the apex ALIAS record")

    print(f"\n================  {len(PASS)} passed, {len(FAIL)} failed, "
          f"{len(WARN)} warnings  ================")
    if FAIL:
        print("FAILED:", ", ".join(FAIL))
        return 1
    print("All critical services healthy.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
