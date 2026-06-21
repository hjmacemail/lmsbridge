"""End-to-end LTI 1.3 launch against a SIMULATED platform.

We generate a platform RSA keypair, publish its JWKS, register it, run the OIDC login
to obtain state+nonce, mint a platform-signed id_token, and assert the tool validates
the launch and provisions the user/course — the same path a real Blackboard/Brightspace/
Canvas/Moodle launch follows.
"""
from __future__ import annotations

import base64
import time

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwt
from sqlalchemy import select

from app.lti import claims as C
from app.lti import jwks_client
from app.lti.launch import validate_launch
from app.lti.oidc import build_login_redirect
from app.lti.provisioning import provision
from app.models.course import Enrollment
from app.models.lti import LtiDeployment, LtiNonce, LtiRegistration

ISSUER = "https://lms.example.edu"
CLIENT_ID = "lms-bridge-client-123"
DEPLOYMENT = "dep-1"
KID = "platform-kid-1"


def _b64u(n: int) -> str:
    raw = n.to_bytes((n.bit_length() + 7) // 8, "big")
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _platform_keypair():
    priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = priv.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    nums = priv.public_key().public_numbers()
    jwks = {"keys": [{"kty": "RSA", "use": "sig", "alg": "RS256", "kid": KID,
                      "n": _b64u(nums.n), "e": _b64u(nums.e)}]}
    return pem, jwks


def _register(db) -> LtiRegistration:
    reg = LtiRegistration(
        name="Example LMS", issuer=ISSUER, client_id=CLIENT_ID,
        auth_login_url=f"{ISSUER}/auth", auth_token_url=f"{ISSUER}/token",
        key_set_url=f"{ISSUER}/jwks", active=True,
    )
    db.add(reg)
    db.flush()
    db.add(LtiDeployment(registration_id=reg.id, deployment_id=DEPLOYMENT))
    db.commit()
    return reg


def _mint_id_token(pem, nonce, *, instructor=False, with_services=True) -> str:
    now = int(time.time())
    roles = (["http://purl.imsglobal.org/vocab/lis/v2/membership#Instructor"]
             if instructor else ["http://purl.imsglobal.org/vocab/lis/v2/membership#Learner"])
    payload = {
        "iss": ISSUER, "aud": CLIENT_ID, "sub": "user-42",
        "name": "Jordan Lee", "email": "jordan@student.example.edu",
        "nonce": nonce, "iat": now, "exp": now + 300,
        C.C_MESSAGE_TYPE: C.MSG_RESOURCE_LINK, C.C_VERSION: "1.3.0",
        C.C_DEPLOYMENT_ID: DEPLOYMENT,
        C.C_TARGET_LINK_URI: "https://tool/launch",
        C.C_ROLES: roles,
        C.C_CONTEXT: {"id": "course-9", "title": "Computer Architecture"},
        C.C_RESOURCE_LINK: {"id": "rl-1", "title": "Adaptive Review"},
    }
    if with_services:
        payload[C.C_AGS_ENDPOINT] = {
            "scope": [C.SCOPE_AGS_LINEITEM], "lineitems": f"{ISSUER}/ags/lineitems"}
        payload[C.C_NRPS] = {"context_memberships_url": f"{ISSUER}/nrps/members"}
    return jwt.encode(payload, pem, algorithm="RS256", headers={"kid": KID})


def _login_state(db, reg) -> tuple[str, str]:
    build_login_redirect(
        db, issuer=ISSUER, login_hint="lh", target_link_uri="https://tool/launch",
        launch_redirect_uri="https://tool/api/v1/lti/launch", client_id=CLIENT_ID,
    )
    row = db.scalars(select(LtiNonce).order_by(LtiNonce.id.desc())).first()
    return row.state, row.nonce


def test_full_launch_provisions_student(db):
    pem, jwks = _platform_keypair()
    reg = _register(db)
    jwks_client.prime_cache(reg.key_set_url, jwks)
    state, nonce = _login_state(db, reg)

    parsed = validate_launch(db, state=state, id_token=_mint_id_token(pem, nonce))
    assert parsed.sub == "user-42"
    assert parsed.context_id == "course-9"
    assert parsed.ags and parsed.nrps

    user, course, token = provision(db, parsed)
    assert user.external_id == f"lti::{ISSUER}::user-42"
    assert user.role.value == "student"
    assert course and course.title == "Computer Architecture"
    enr = db.scalar(select(Enrollment).where(
        Enrollment.user_id == user.id, Enrollment.course_id == course.id))
    assert enr is not None
    assert token  # signed app session


def test_instructor_role_mapped(db):
    pem, jwks = _platform_keypair()
    reg = _register(db)
    jwks_client.prime_cache(reg.key_set_url, jwks)
    state, nonce = _login_state(db, reg)
    parsed = validate_launch(db, state=state, id_token=_mint_id_token(pem, nonce, instructor=True))
    user, _course, _t = provision(db, parsed)
    assert user.role.value == "instructor"


def test_instructor_launch_syncs_full_roster_via_nrps(db, monkeypatch):
    from app.lti import provisioning
    from app.models.enums import UserRole
    from app.models.user import User

    pem, jwks = _platform_keypair()
    reg = _register(db)
    jwks_client.prime_cache(reg.key_set_url, jwks)
    state, nonce = _login_state(db, reg)

    parsed = validate_launch(db, state=state, id_token=_mint_id_token(pem, nonce, instructor=True))
    _instructor, course, _t = provision(db, parsed)
    # The NRPS membership URL from the launch is captured on the course.
    assert course.lti_memberships_url == f"{ISSUER}/nrps/members"

    learner = ["http://purl.imsglobal.org/vocab/lis/v2/membership#Learner"]
    members = [
        {"user_id": "stu-1", "name": "Ada", "email": "ada@ex.edu", "roles": learner,
         "status": "Active"},
        {"user_id": "stu-2", "name": "Bo", "email": "bo@ex.edu", "roles": learner,
         "status": "Active"},
        {"user_id": "stu-3", "name": "Gone", "email": "g@ex.edu", "roles": learner,
         "status": "Inactive"},  # must be skipped
    ]
    calls = {"n": 0}

    def fake_members(db, reg, url):
        calls["n"] += 1
        assert url == f"{ISSUER}/nrps/members"
        return members

    monkeypatch.setattr(provisioning.services, "nrps_get_members", fake_members)

    provisioning.maybe_sync_roster_on_launch(db, parsed, course)
    provisioning.maybe_sync_roster_on_launch(db, parsed, course)  # idempotent

    assert calls["n"] == 2  # NRPS actually called each time
    students = db.scalars(
        select(Enrollment).where(
            Enrollment.course_id == course.id, Enrollment.role == UserRole.student
        )
    ).all()
    assert len(students) == 2  # stu-1, stu-2 (stu-3 inactive skipped); no duplicates on re-run
    ada = db.scalar(select(User).where(User.external_id == f"lti::{ISSUER}::stu-1"))
    assert ada and ada.role == UserRole.student and ada.full_name == "Ada"


def test_student_launch_does_not_trigger_roster_sync(db, monkeypatch):
    from app.lti import provisioning

    pem, jwks = _platform_keypair()
    reg = _register(db)
    jwks_client.prime_cache(reg.key_set_url, jwks)
    state, nonce = _login_state(db, reg)
    parsed = validate_launch(db, state=state, id_token=_mint_id_token(pem, nonce))  # learner
    _u, course, _t = provision(db, parsed)

    called = {"n": 0}
    monkeypatch.setattr(
        provisioning.services, "nrps_get_members",
        lambda *a, **k: called.__setitem__("n", called["n"] + 1) or [],
    )
    provisioning.maybe_sync_roster_on_launch(db, parsed, course)
    assert called["n"] == 0  # students don't pull the roster


def test_replayed_state_is_rejected(db):
    pem, jwks = _platform_keypair()
    reg = _register(db)
    jwks_client.prime_cache(reg.key_set_url, jwks)
    state, nonce = _login_state(db, reg)
    token = _mint_id_token(pem, nonce)
    validate_launch(db, state=state, id_token=token)  # first use ok
    try:
        validate_launch(db, state=state, id_token=token)
        raise AssertionError("replay should be rejected")
    except Exception as e:
        assert "already used" in str(e).lower() or "replay" in str(e).lower()


def test_bad_nonce_is_rejected(db):
    pem, jwks = _platform_keypair()
    reg = _register(db)
    jwks_client.prime_cache(reg.key_set_url, jwks)
    state, _nonce = _login_state(db, reg)
    try:
        validate_launch(db, state=state, id_token=_mint_id_token(pem, "wrong-nonce"))
        raise AssertionError("nonce mismatch should be rejected")
    except Exception as e:
        assert "nonce" in str(e).lower()


def test_jwks_endpoint_and_config(client):
    j = client.get("/api/v1/lti/jwks")
    assert j.status_code == 200
    assert j.json()["keys"] and j.json()["keys"][0]["kty"] == "RSA"
    cfg = client.get("/api/v1/lti/config")
    assert cfg.status_code == 200
    assert "oidc_initiation_url" in cfg.json()


def test_api_login_redirects_to_platform(client, db):
    _register(db)
    r = client.post("/api/v1/lti/login", data={
        "iss": ISSUER, "login_hint": "lh", "target_link_uri": "https://tool/launch",
        "client_id": CLIENT_ID,
    }, follow_redirects=False)
    assert r.status_code == 302
    loc = r.headers["location"]
    assert loc.startswith(f"{ISSUER}/auth")
    assert "state=" in loc and "nonce=" in loc


# ---- Registration management + dynamic registration ----

def _admin_headers(client, db):
    from app.core.security import hash_password
    from app.models.enums import UserRole
    from app.models.user import User
    a = User(email="admin@lti.edu", full_name="Admin", role=UserRole.admin,
             is_platform_admin=True, hashed_password=hash_password("pw"))
    db.add(a)
    db.commit()
    r = client.post("/api/v1/auth/login", data={"username": "admin@lti.edu", "password": "pw"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_admin_registration_crud(client, db):
    h = _admin_headers(client, db)
    body = {
        "name": "My Canvas", "issuer": "https://canvas.test", "client_id": "cid-1",
        "auth_login_url": "https://canvas.test/auth", "auth_token_url": "https://canvas.test/token",
        "key_set_url": "https://canvas.test/jwks", "deployment_id": "dep-1",
    }
    created = client.post("/api/v1/lti/registrations", headers=h, json=body)
    assert created.status_code == 201, created.text
    rid = created.json()["id"]
    assert created.json()["deployments"][0]["deployment_id"] == "dep-1"

    assert any(r["id"] == rid for r in client.get("/api/v1/lti/registrations", headers=h).json())
    # Non-admin cannot list.
    assert client.get("/api/v1/lti/registrations").status_code == 401

    add = client.post(f"/api/v1/lti/registrations/{rid}/deployments", headers=h,
                      json={"deployment_id": "dep-2"})
    assert len(add.json()["deployments"]) == 2
    assert client.delete(f"/api/v1/lti/registrations/{rid}", headers=h).status_code == 204


def test_auto_deployment_for_dynamic_platform(db):
    pem, jwks = _platform_keypair()
    reg = _register(db)
    reg.auto_register_deployments = True
    db.commit()
    jwks_client.prime_cache(reg.key_set_url, jwks)
    state, nonce = _login_state(db, reg)
    # Mint with a deployment_id that is NOT pre-registered.
    token = _mint_id_token(pem, nonce).replace(DEPLOYMENT, "BRAND-NEW-DEP")
    # (re-mint properly so the signature is valid for the new deployment)
    import time

    from jose import jwt
    now = int(time.time())
    payload = {
        "iss": ISSUER, "aud": CLIENT_ID, "sub": "u9", "name": "X", "nonce": nonce,
        "iat": now, "exp": now + 300, C.C_MESSAGE_TYPE: C.MSG_RESOURCE_LINK,
        C.C_VERSION: "1.3.0", C.C_DEPLOYMENT_ID: "BRAND-NEW-DEP",
        C.C_ROLES: [], C.C_CONTEXT: {"id": "c1", "title": "T"},
    }
    token = jwt.encode(payload, pem, algorithm="RS256", headers={"kid": KID})
    parsed = validate_launch(db, state=state, id_token=token)
    assert parsed.deployment_id == "BRAND-NEW-DEP"  # auto-accepted


def test_dynamic_registration(db, monkeypatch):
    from app.lti import dynamic_registration as dr

    class _Resp:
        def __init__(self, data):
            self._data = data
        def raise_for_status(self):
            pass
        def json(self):
            return self._data

    config = {
        "issuer": "https://moodle.test",
        "authorization_endpoint": "https://moodle.test/auth",
        "token_endpoint": "https://moodle.test/token",
        "jwks_uri": "https://moodle.test/jwks",
        "registration_endpoint": "https://moodle.test/register",
    }
    monkeypatch.setattr(dr.httpx, "get", lambda url, **kw: _Resp(config))
    monkeypatch.setattr(dr.httpx, "post", lambda url, **kw: _Resp({"client_id": "dyn-client-1"}))

    reg = dr.register_with_platform(
        db, openid_configuration_url="https://moodle.test/.well-known/openid",
        registration_token="tok",
    )
    assert reg.issuer == "https://moodle.test"
    assert reg.client_id == "dyn-client-1"
    assert reg.auto_register_deployments is True
