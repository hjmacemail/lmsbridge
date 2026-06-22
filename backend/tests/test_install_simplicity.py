"""Install-simplicity tests.

These assert that integrating LMS Bridge into an LMS is *simple, standard, and straightforward*:
- an admin discovers every URL from ONE endpoint and constructs nothing by hand,
- Canvas/Moodle install via a single pasted Dynamic Registration URL (no keys, no shared secret),
- the tool generates its own keys (no crypto setup by the admin),
- the first launch auto-provisions the user, course, role, and enrollment (no manual roster),
- dynamically-registered deployments are auto-trusted (no copying a Deployment ID back),
and a runbook audit that keeps the recommended per-LMS steps short.
"""
from __future__ import annotations

import base64
import re
import time
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwt
from sqlalchemy import select

from app.lti import claims as C
from app.lti import jwks_client
from app.lti.oidc import build_login_redirect
from app.models.lti import LtiDeployment, LtiNonce, LtiRegistration

REPO = Path(__file__).resolve().parents[2]
RUNBOOK = REPO / "docs" / "INSTALL_LTI.md"

ISS, CID, DEP, KID = "https://lms.simple.edu", "client-simple", "dep-simple", "kid-simple"


def _b64u(n: int) -> str:
    raw = n.to_bytes((n.bit_length() + 7) // 8, "big")
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _keypair():
    priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = priv.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                             serialization.NoEncryption()).decode()
    n = priv.public_key().public_numbers()
    return pem, {"keys": [{"kty": "RSA", "use": "sig", "alg": "RS256", "kid": KID,
                           "n": _b64u(n.n), "e": _b64u(n.e)}]}


# ---------------------------------------------------------- 1. one discovery endpoint

def test_admin_discovers_everything_from_one_endpoint(client):
    """An admin never constructs a URL by hand — /lti/config returns them all, ready to paste."""
    cfg = client.get("/api/v1/lti/config").json()
    needed = ["oidc_initiation_url", "target_link_uri", "redirect_uris",
              "public_jwks_url", "deep_linking_url", "dynamic_registration_url"]
    for k in needed:
        assert cfg.get(k), f"config missing {k}"
    # Every URL is absolute (copy-paste ready), not a relative fragment.
    for k in needed:
        v = cfg[k]
        for url in (v if isinstance(v, list) else [v]):
            assert url.startswith("http"), f"{k} is not an absolute URL"


# ---------------------------------------------------------- 2. no shared secret (LTI 1.3)

def test_no_shared_secret_anywhere(client):
    """LTI 1.3 uses keysets, not consumer keys/secrets — nothing secret to exchange or leak."""
    cfg = client.get("/api/v1/lti/config").json()
    blob = str(cfg).lower()
    assert "secret" not in blob and "shared_secret" not in blob
    # The registration model has no secret column to manage.
    cols = {c.name for c in LtiRegistration.__table__.columns}
    assert not any("secret" in c for c in cols)


# ---------------------------------------------------------- 3. tool generates its own keys

def test_tool_serves_its_own_keys_with_zero_setup(client):
    """The admin supplies no crypto — the tool publishes its JWKS out of the box."""
    j = client.get("/api/v1/lti/jwks").json()
    assert j["keys"] and j["keys"][0]["kty"] == "RSA"


# ---------------------------------------------------------- 4. Canvas/Moodle: one pasted URL

def test_canvas_moodle_register_with_one_url_no_keys(db, monkeypatch):
    """Dynamic Registration: the LMS hands over a single config URL; the tool self-configures."""
    from app.lti import dynamic_registration as dr

    class _Resp:
        def __init__(self, d):
            self._d = d
        def raise_for_status(self):
            pass
        def json(self):
            return self._d

    cfg = {"issuer": "https://canvas.test", "authorization_endpoint": "https://canvas.test/auth",
           "token_endpoint": "https://canvas.test/token", "jwks_uri": "https://canvas.test/jwks",
           "registration_endpoint": "https://canvas.test/reg"}
    monkeypatch.setattr(dr.httpx, "get", lambda url, **kw: _Resp(cfg))
    monkeypatch.setattr(dr.httpx, "post", lambda url, **kw: _Resp({"client_id": "auto-c1"}))

    # The ONLY input is the platform's openid_configuration URL — no key, no secret.
    reg = dr.register_with_platform(
        db, openid_configuration_url="https://canvas.test/.well-known", registration_token=None)
    assert reg.client_id == "auto-c1"
    assert reg.auto_register_deployments is True  # deployments trusted automatically too


# ---------------------------------------------------------- 5. first launch: zero prior setup

def test_first_launch_autoprovisions_with_no_prior_setup(client, db):
    """After registration, the very first launch creates the user, course, role + enrollment.

    No course shell, concepts, roster, or assessments need to exist first — it just works.
    """
    from app.models.course import Course, Enrollment
    from app.models.user import User

    pem, jwks = _keypair()
    reg = LtiRegistration(name="LMS", issuer=ISS, client_id=CID,
                          auth_login_url=f"{ISS}/a", auth_token_url=f"{ISS}/t",
                          key_set_url=f"{ISS}/jwks", active=True)
    db.add(reg)
    db.flush()
    db.add(LtiDeployment(registration_id=reg.id, deployment_id=DEP))
    db.commit()
    jwks_client.prime_cache(reg.key_set_url, jwks)

    build_login_redirect(db, issuer=ISS, login_hint="lh", target_link_uri="https://t/launch",
                         launch_redirect_uri="https://t/api/v1/lti/launch", client_id=CID)
    row = db.scalars(select(LtiNonce).order_by(LtiNonce.id.desc())).first()
    now = int(time.time())
    tok = jwt.encode({
        "iss": ISS, "aud": CID, "sub": "newuser", "name": "New User", "nonce": row.nonce,
        "iat": now, "exp": now + 300, C.C_MESSAGE_TYPE: C.MSG_RESOURCE_LINK, C.C_VERSION: "1.3.0",
        C.C_DEPLOYMENT_ID: DEP, C.C_ROLES: ["...#Instructor"],
        C.C_CONTEXT: {"id": "fresh-course", "title": "Fresh Course"},
    }, pem, algorithm="RS256", headers={"kid": KID})

    r = client.post("/api/v1/lti/launch", data={"state": row.state, "id_token": tok},
                    follow_redirects=False)
    assert r.status_code == 302
    q = parse_qs(urlparse(r.headers["location"]).query)
    assert "token" in q and "course_id" in q  # single sign-on, course ready
    user = db.scalar(select(User).where(User.external_id == f"lti::{ISS}::newuser"))
    course = db.get(Course, int(q["course_id"][0]))
    enr = db.scalar(select(Enrollment).where(
        Enrollment.user_id == user.id, Enrollment.course_id == course.id))
    assert user and course and enr  # everything provisioned with zero admin action


# ---------------------------------------------------------- 6. deployments auto-trusted

def test_dynamic_deployment_auto_trusted_no_copy_back(client, db):
    """For dynamically-registered platforms the admin doesn't copy a Deployment ID back."""
    from app.models.course import Course  # noqa: F401

    pem, jwks = _keypair()
    reg = LtiRegistration(name="LMS", issuer=ISS, client_id=CID,
                          auth_login_url=f"{ISS}/a", auth_token_url=f"{ISS}/t",
                          key_set_url=f"{ISS}/jwks", active=True, auto_register_deployments=True)
    db.add(reg)
    db.commit()
    jwks_client.prime_cache(reg.key_set_url, jwks)
    build_login_redirect(db, issuer=ISS, login_hint="lh", target_link_uri="https://t/launch",
                         launch_redirect_uri="https://t/api/v1/lti/launch", client_id=CID)
    row = db.scalars(select(LtiNonce).order_by(LtiNonce.id.desc())).first()
    now = int(time.time())
    tok = jwt.encode({
        "iss": ISS, "aud": CID, "sub": "u", "name": "U", "nonce": row.nonce, "iat": now,
        "exp": now + 300, C.C_MESSAGE_TYPE: C.MSG_RESOURCE_LINK, C.C_VERSION: "1.3.0",
        C.C_DEPLOYMENT_ID: "NEVER-REGISTERED", C.C_ROLES: [],
        C.C_CONTEXT: {"id": "c", "title": "C"},
    }, pem, algorithm="RS256", headers={"kid": KID})
    r = client.post("/api/v1/lti/launch", data={"state": row.state, "id_token": tok},
                    follow_redirects=False)
    assert r.status_code == 302  # accepted without the admin pre-registering the deployment


# ---------------------------------------------------------- 7. runbook simplicity audit

def _section(text: str, header: str) -> str:
    lines = text.splitlines()
    out, capturing = [], False
    for ln in lines:
        if ln.startswith("## "):
            capturing = header.lower() in ln.lower()
            continue
        if capturing:
            if ln.startswith("## "):
                break
            out.append(ln)
    return "\n".join(out)


def test_runbook_promises_one_click_and_self_discovery():
    text = RUNBOOK.read_text()
    # Canvas + Moodle advertise a one-click Dynamic Registration path.
    assert "Dynamic Registration" in text
    assert "## 1. Canvas" in text and "## 2. Moodle" in text
    # The admin is told the URLs come from one endpoint, not hand-built.
    assert "/api/v1/lti/config" in text
    # Auto-provisioning is promised (no manual roster).
    assert "auto-provisions" in text or "no manual roster" in text


def test_recommended_paths_are_short():
    """The recommended (one-click) path for Canvas and Moodle should be a handful of steps."""
    text = RUNBOOK.read_text()
    for lms in ("1. Canvas", "2. Moodle"):
        sec = _section(text, lms)
        # Count numbered steps in the recommended "Option A — Dynamic Registration" block.
        opt_a = sec.split("Option B")[0]
        steps = re.findall(r"^\s*\d+\.\s", opt_a, flags=re.MULTILINE)
        assert 0 < len(steps) <= 8, f"{lms} dynamic-registration path has {len(steps)} steps"
