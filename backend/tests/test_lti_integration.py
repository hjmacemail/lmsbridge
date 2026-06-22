"""LTI 1.3 integration & compliance suite.

Covers spec/security conformance (signature, iss/aud/exp/azp, version, message type),
Deep Linking, Dynamic Registration advertisement, JIT provisioning behavior, multi-tenant
isolation, and usability (config/lms-context/friendly errors).
"""
from __future__ import annotations

import base64
import time
from urllib.parse import parse_qs, urlparse

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwt
from sqlalchemy import select

from app.lti import claims as C
from app.lti import jwks_client
from app.lti.oidc import build_login_redirect
from app.models.lti import LtiDeployment, LtiNonce, LtiRegistration

KID = "kid-itest"


def _b64u(n: int) -> str:
    raw = n.to_bytes((n.bit_length() + 7) // 8, "big")
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _keypair(kid: str = KID):
    priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = priv.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                             serialization.NoEncryption()).decode()
    nums = priv.public_key().public_numbers()
    jwks = {"keys": [{"kty": "RSA", "use": "sig", "alg": "RS256", "kid": kid,
                      "n": _b64u(nums.n), "e": _b64u(nums.e)}]}
    return pem, jwks


def _register(db, *, issuer, client_id, deployment, name="LMS"):
    reg = LtiRegistration(
        name=name, issuer=issuer, client_id=client_id,
        auth_login_url=f"{issuer}/auth", auth_token_url=f"{issuer}/token",
        key_set_url=f"{issuer}/jwks", active=True)
    db.add(reg)
    db.flush()
    db.add(LtiDeployment(registration_id=reg.id, deployment_id=deployment))
    db.commit()
    return reg


def _state_nonce(db, *, issuer, client_id):
    build_login_redirect(db, issuer=issuer, login_hint="lh", target_link_uri="https://t/launch",
                         launch_redirect_uri="https://t/api/v1/lti/launch", client_id=client_id)
    row = db.scalars(select(LtiNonce).order_by(LtiNonce.id.desc())).first()
    return row.state, row.nonce


def _mint(pem, *, issuer, client_id, deployment, nonce, sub="u1", instructor=False,
          kid=KID, services=False, context_id="c1", **over):
    now = int(time.time())
    roles = (["http://purl.imsglobal.org/vocab/lis/v2/membership#Instructor"] if instructor
             else ["http://purl.imsglobal.org/vocab/lis/v2/membership#Learner"])
    payload = {
        "iss": issuer, "aud": client_id, "sub": sub, "name": "User", "nonce": nonce,
        "iat": now, "exp": now + 300,
        C.C_MESSAGE_TYPE: C.MSG_RESOURCE_LINK, C.C_VERSION: "1.3.0",
        C.C_DEPLOYMENT_ID: deployment, C.C_TARGET_LINK_URI: "https://t/launch",
        C.C_ROLES: roles, C.C_CONTEXT: {"id": context_id, "title": "Course"},
        C.C_RESOURCE_LINK: {"id": "rl1", "title": "Link"},
    }
    if services:
        payload[C.C_AGS_ENDPOINT] = {"scope": [C.SCOPE_AGS_LINEITEM],
                                     "lineitems": f"{issuer}/ags/lineitems"}
        payload[C.C_NRPS] = {"context_memberships_url": f"{issuer}/nrps"}
    payload.update(over)
    return jwt.encode(payload, pem, algorithm="RS256", headers={"kid": kid})


ISS = "https://lms.example.edu"
CID = "client-itest"
DEP = "dep-itest"


def _setup(db):
    pem, jwks = _keypair()
    reg = _register(db, issuer=ISS, client_id=CID, deployment=DEP)
    jwks_client.prime_cache(reg.key_set_url, jwks)
    return pem


# ------------------------------------------------------------------ compliance: config/JWKS

def test_jwks_is_valid_rsa_keyset(client):
    j = client.get("/api/v1/lti/jwks").json()
    assert j["keys"]
    k = j["keys"][0]
    assert k["kty"] == "RSA" and k["use"] == "sig" and k["alg"] == "RS256"
    assert k.get("kid") and k.get("n") and k.get("e")


def test_config_advertises_endpoints_and_advantage_scopes(client):
    cfg = client.get("/api/v1/lti/config").json()
    for key in ("oidc_initiation_url", "target_link_uri", "redirect_uris",
                "public_jwks_url", "deep_linking_url", "dynamic_registration_url"):
        assert key in cfg, key
    assert C.SCOPE_NRPS in cfg["scopes"]
    assert C.SCOPE_AGS_LINEITEM in cfg["scopes"] and C.SCOPE_AGS_SCORE in cfg["scopes"]


def test_login_requires_iss_login_hint_target(client, db):
    _register(db, issuer=ISS, client_id=CID, deployment=DEP)
    assert client.post("/api/v1/lti/login", data={"iss": ISS}).status_code == 400


# ------------------------------------------------------------------ compliance: launch security

def _launch(client, state, token):
    return client.post("/api/v1/lti/launch", data={"state": state, "id_token": token},
                       follow_redirects=False)


def test_rejects_bad_signature(client, db):
    _setup(db)
    other_pem, _ = _keypair()  # not the published key
    state, nonce = _state_nonce(db, issuer=ISS, client_id=CID)
    tok = _mint(other_pem, issuer=ISS, client_id=CID, deployment=DEP, nonce=nonce)
    assert _launch(client, state, tok).status_code == 401


def test_rejects_wrong_issuer(client, db):
    pem = _setup(db)
    state, nonce = _state_nonce(db, issuer=ISS, client_id=CID)
    tok = _mint(pem, issuer="https://evil.example", client_id=CID, deployment=DEP, nonce=nonce)
    assert _launch(client, state, tok).status_code == 401


def test_rejects_wrong_audience(client, db):
    pem = _setup(db)
    state, nonce = _state_nonce(db, issuer=ISS, client_id=CID)
    tok = _mint(pem, issuer=ISS, client_id="someone-else", deployment=DEP, nonce=nonce)
    assert _launch(client, state, tok).status_code == 401


def test_rejects_expired_token(client, db):
    pem = _setup(db)
    state, nonce = _state_nonce(db, issuer=ISS, client_id=CID)
    tok = _mint(pem, issuer=ISS, client_id=CID, deployment=DEP, nonce=nonce,
                iat=int(time.time()) - 3600, exp=int(time.time()) - 1800)
    assert _launch(client, state, tok).status_code == 401


def test_rejects_unsupported_version(client, db):
    pem = _setup(db)
    state, nonce = _state_nonce(db, issuer=ISS, client_id=CID)
    tok = _mint(pem, issuer=ISS, client_id=CID, deployment=DEP, nonce=nonce,
                **{C.C_VERSION: "1.2.0"})
    assert _launch(client, state, tok).status_code == 401


def test_rejects_unsupported_message_type(client, db):
    pem = _setup(db)
    state, nonce = _state_nonce(db, issuer=ISS, client_id=CID)
    tok = _mint(pem, issuer=ISS, client_id=CID, deployment=DEP, nonce=nonce,
                **{C.C_MESSAGE_TYPE: "SomethingBogus"})
    assert _launch(client, state, tok).status_code == 401


def test_rejects_azp_mismatch_with_multiple_audiences(client, db):
    pem = _setup(db)
    state, nonce = _state_nonce(db, issuer=ISS, client_id=CID)
    tok = _mint(pem, issuer=ISS, client_id=CID, deployment=DEP, nonce=nonce,
                aud=[CID, "other-aud"], azp="not-the-client")
    assert _launch(client, state, tok).status_code == 401


def test_unknown_deployment_rejected_without_autoregister(client, db):
    pem = _setup(db)
    state, nonce = _state_nonce(db, issuer=ISS, client_id=CID)
    tok = _mint(pem, issuer=ISS, client_id=CID, deployment="NOT-REGISTERED", nonce=nonce)
    assert _launch(client, state, tok).status_code == 401


def test_friendly_error_detail_on_rejected_launch(client, db):
    _setup(db)
    state, nonce = _state_nonce(db, issuer=ISS, client_id=CID)
    other_pem, _ = _keypair()
    tok = _mint(other_pem, issuer=ISS, client_id=CID, deployment=DEP, nonce=nonce)
    r = _launch(client, state, tok)
    assert r.status_code == 401 and "rejected" in r.json()["detail"].lower()


# ------------------------------------------------------------------ valid launch + provisioning

def _full_launch(client, db, pem, *, sub, instructor, context_id="c1"):
    state, nonce = _state_nonce(db, issuer=ISS, client_id=CID)
    tok = _mint(pem, issuer=ISS, client_id=CID, deployment=DEP, nonce=nonce,
                sub=sub, instructor=instructor, context_id=context_id)
    r = _launch(client, state, tok)
    assert r.status_code == 302, r.text
    q = parse_qs(urlparse(r.headers["location"]).query)
    return {"token": q["token"][0], "role": q["role"][0],
            "course_id": int(q["course_id"][0]) if "course_id" in q else None}


def test_valid_launch_redirects_with_session(client, db):
    pem = _setup(db)
    out = _full_launch(client, db, pem, sub="stud", instructor=False)
    assert out["role"] == "student" and out["course_id"]


def test_provisioning_is_idempotent(client, db):
    from app.models.course import Enrollment
    from app.models.user import User
    pem = _setup(db)
    _full_launch(client, db, pem, sub="same", instructor=False)
    _full_launch(client, db, pem, sub="same", instructor=False)
    users = db.scalars(select(User).where(User.external_id == f"lti::{ISS}::same")).all()
    assert len(users) == 1
    enr = db.scalars(select(Enrollment).where(Enrollment.user_id == users[0].id)).all()
    assert len(enr) == 1


def test_role_not_downgraded_on_later_launch(client, db):
    from app.models.user import User
    pem = _setup(db)
    _full_launch(client, db, pem, sub="prof", instructor=True)
    _full_launch(client, db, pem, sub="prof", instructor=False)  # later student-role launch
    u = db.scalar(select(User).where(User.external_id == f"lti::{ISS}::prof"))
    assert u.role.value == "instructor"  # not downgraded


# ------------------------------------------------------------------ deep linking

def test_deep_linking_returns_autopost_form(client, db):
    pem = _setup(db)
    state, nonce = _state_nonce(db, issuer=ISS, client_id=CID)
    tok = _mint(pem, issuer=ISS, client_id=CID, deployment=DEP, nonce=nonce, instructor=True,
                **{C.C_MESSAGE_TYPE: C.MSG_DEEP_LINKING,
                   C.C_DL_SETTINGS: {"deep_link_return_url": "https://lms/return", "data": "xyz"}})
    r = _launch(client, state, tok)
    assert r.status_code == 200
    body = r.text
    assert "https://lms/return" in body and 'name="JWT"' in body and "form" in body.lower()


# ------------------------------------------------------------------ dynamic registration advertises

def test_dynamic_registration_advertises_placements_and_custom_params(db, monkeypatch):
    from app.lti import dynamic_registration as dr
    captured = {}

    class _Resp:
        def __init__(self, data):
            self._d = data
        def raise_for_status(self):
            pass
        def json(self):
            return self._d

    cfg = {"issuer": "https://canvas.test", "authorization_endpoint": "https://canvas.test/auth",
           "token_endpoint": "https://canvas.test/token", "jwks_uri": "https://canvas.test/jwks",
           "registration_endpoint": "https://canvas.test/reg"}

    def fake_post(url, **kw):
        captured["body"] = kw.get("json")
        return _Resp({"client_id": "c1"})

    monkeypatch.setattr(dr.httpx, "get", lambda url, **kw: _Resp(cfg))
    monkeypatch.setattr(dr.httpx, "post", fake_post)
    dr.register_with_platform(db, openid_configuration_url="https://canvas.test/.well-known",
                              registration_token="t")

    tool_cfg = captured["body"]["https://purl.imsglobal.org/spec/lti-tool-configuration"]
    placements = tool_cfg["messages"][0].get("placements", [])
    assert "course_navigation" in placements
    assert "canvas_course_id" in tool_cfg.get("custom_parameters", {})
    assert C.SCOPE_NRPS in captured["body"]["scope"]


# ------------------------------------------------------------------ multi-tenant isolation

def test_instructor_cannot_read_other_courses_roster(client, db):
    """An instructor provisioned in course A must NOT read course B's roster (IDOR/tenant leak)."""
    pem = _setup(db)
    a = _full_launch(client, db, pem, sub="profA", instructor=True, context_id="courseA")
    b = _full_launch(client, db, pem, sub="profB", instructor=True, context_id="courseB")
    ha = {"Authorization": f"Bearer {a['token']}"}
    own = client.get(f"/api/v1/analytics/courses/{a['course_id']}/roster", headers=ha)
    other = client.get(f"/api/v1/analytics/courses/{b['course_id']}/roster", headers=ha)
    assert own.status_code == 200  # owns course A
    assert other.status_code in (403, 404)  # must not read course B


def test_instructor_cannot_read_other_course_materials(client, db):
    pem = _setup(db)
    a = _full_launch(client, db, pem, sub="iA", instructor=True, context_id="cA")
    b = _full_launch(client, db, pem, sub="iB", instructor=True, context_id="cB")
    ha = {"Authorization": f"Bearer {a['token']}"}
    r = client.get(f"/api/v1/materials?course_id={b['course_id']}", headers=ha)
    assert r.status_code in (403, 404)
