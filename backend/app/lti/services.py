"""LTI Advantage service clients: OAuth2 token, AGS (grades), NRPS (roster)."""
from __future__ import annotations

import time
import uuid

import httpx
from jose import jwt
from sqlalchemy.orm import Session

from app.lti import claims as C
from app.lti.keys import private_pem
from app.models.lti import LtiRegistration

# Cache: (registration_id, scope_key) -> (expires_at, token)
_TOKEN_CACHE: dict[tuple[int, str], tuple[float, str]] = {}


def get_access_token(db: Session, reg: LtiRegistration, scopes: list[str]) -> str:
    """OAuth2 client-credentials grant using a JWT client assertion signed by the tool key."""
    scope_str = " ".join(sorted(scopes))
    cache_key = (reg.id, scope_str)
    cached = _TOKEN_CACHE.get(cache_key)
    now = time.time()
    if cached and cached[0] - 30 > now:
        return cached[1]

    kid, pem = private_pem(db)
    aud = reg.audience or reg.auth_token_url
    assertion = jwt.encode(
        {
            "iss": reg.client_id,
            "sub": reg.client_id,
            "aud": aud,
            "iat": int(now),
            "exp": int(now) + 300,
            "jti": uuid.uuid4().hex,
        },
        pem, algorithm="RS256", headers={"kid": kid},
    )
    resp = httpx.post(
        reg.auth_token_url,
        data={
            "grant_type": "client_credentials",
            "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
            "client_assertion": assertion,
            "scope": scope_str,
        },
        timeout=15.0,
    )
    resp.raise_for_status()
    body = resp.json()
    token = body["access_token"]
    _TOKEN_CACHE[cache_key] = (now + int(body.get("expires_in", 3600)), token)
    return token


# ---- AGS: Assignment & Grade Services ----

def ags_get_lineitems(db: Session, reg: LtiRegistration, lineitems_url: str) -> list[dict]:
    token = get_access_token(db, reg, [C.SCOPE_AGS_LINEITEM])
    resp = httpx.get(
        lineitems_url,
        headers={"Authorization": f"Bearer {token}",
                 "Accept": "application/vnd.ims.lis.v2.lineitemcontainer+json"},
        timeout=15.0,
    )
    resp.raise_for_status()
    return resp.json()


def ags_get_results(db: Session, reg: LtiRegistration, lineitem_url: str) -> list[dict]:
    token = get_access_token(db, reg, [C.SCOPE_AGS_RESULT])
    sep = "&" if "?" in lineitem_url else "?"
    url = f"{lineitem_url}{sep}" if lineitem_url.endswith("/results") else f"{lineitem_url}/results"
    resp = httpx.get(
        url,
        headers={"Authorization": f"Bearer {token}",
                 "Accept": "application/vnd.ims.lis.v2.resultcontainer+json"},
        timeout=15.0,
    )
    resp.raise_for_status()
    return resp.json()


def ags_post_score(
    db: Session, reg: LtiRegistration, lineitem_url: str, *,
    user_id: str, score_given: float, score_maximum: float, comment: str | None = None,
) -> None:
    """Write a score back to the LMS gradebook line item (used for a NON-graded mastery column)."""
    token = get_access_token(db, reg, [C.SCOPE_AGS_SCORE])
    sep = "&" if "?" in lineitem_url else "?"
    url = lineitem_url if lineitem_url.endswith("/scores") else f"{lineitem_url}/scores"
    _ = sep
    payload = {
        "userId": user_id,
        "scoreGiven": score_given,
        "scoreMaximum": score_maximum,
        "activityProgress": "Completed",
        "gradingProgress": "FullyGraded",
        "timestamp": _now_iso(),
    }
    if comment:
        payload["comment"] = comment
    resp = httpx.post(
        url, json=payload,
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/vnd.ims.lis.v1.score+json"},
        timeout=15.0,
    )
    resp.raise_for_status()


# ---- NRPS: Names & Role Provisioning Services ----

def nrps_get_members(db: Session, reg: LtiRegistration, memberships_url: str) -> list[dict]:
    token = get_access_token(db, reg, [C.SCOPE_NRPS])
    members: list[dict] = []
    url: str | None = memberships_url
    while url:
        resp = httpx.get(
            url,
            headers={"Authorization": f"Bearer {token}",
                     "Accept": "application/vnd.ims.lti-nrps.v2.membershipcontainer+json"},
            timeout=15.0,
        )
        resp.raise_for_status()
        members.extend(resp.json().get("members", []))
        # Follow RFC5988 Link: <...>; rel="next" pagination if present.
        url = _next_link(resp.headers.get("Link", ""))
    return members


def _next_link(link_header: str) -> str | None:
    for part in link_header.split(","):
        if 'rel="next"' in part:
            start, end = part.find("<"), part.find(">")
            if start != -1 and end != -1:
                return part[start + 1:end]
    return None


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()
