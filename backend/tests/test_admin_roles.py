"""Platform admin vs institution admin: scope and endpoint gating."""


def _mk(db, email, role, *, platform=False, tenant_id=None):
    from app.core.security import hash_password
    from app.models.enums import UserRole
    from app.models.user import User
    u = User(email=email, full_name=email, role=UserRole(role),
             is_platform_admin=platform, tenant_id=tenant_id,
             hashed_password=hash_password("pw"))
    db.add(u)
    db.commit()
    return u


def _login(client, email):
    r = client.post("/api/v1/auth/login", data={"username": email, "password": "pw"})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}, r.json()


def test_login_exposes_platform_flag(client, db):
    _mk(db, "plat@x.edu", "admin", platform=True)
    _mk(db, "inst@x.edu", "admin", platform=False)
    _, plat = _login(client, "plat@x.edu")
    _, inst = _login(client, "inst@x.edu")
    assert plat["is_platform_admin"] is True
    assert inst["is_platform_admin"] is False


def test_platform_only_endpoints_blocked_for_institution_admin(client, db):
    from app.models.tenant import Tenant
    t = Tenant(name="Inst", slug="inst")
    db.add(t)
    db.flush()
    _mk(db, "inst@x.edu", "admin", platform=False, tenant_id=t.id)
    _mk(db, "plat@x.edu", "admin", platform=True)

    inst_h, _ = _login(client, "inst@x.edu")
    plat_h, _ = _login(client, "plat@x.edu")

    # Leads + LTI registrations = platform-only.
    assert client.get("/api/v1/leads", headers=inst_h).status_code == 403
    assert client.get("/api/v1/lti/registrations", headers=inst_h).status_code == 403
    assert client.get("/api/v1/leads", headers=plat_h).status_code == 200
    assert client.get("/api/v1/lti/registrations", headers=plat_h).status_code == 200

    # But the institution admin CAN manage their own AI/privacy.
    assert client.get("/api/v1/tenants/me", headers=inst_h).status_code == 200
    upd = client.put("/api/v1/tenants/me/ai", headers=inst_h,
                     json={"pii_minimization": True, "external_ai_allowed": False})
    assert upd.status_code == 200


def test_institution_usage_visible_to_admins_not_students(client, db):
    _mk(db, "inst@x.edu", "admin", platform=False)
    _mk(db, "stu@x.edu", "student")

    inst_h, _ = _login(client, "inst@x.edu")
    stu_h, _ = _login(client, "stu@x.edu")

    r = client.get("/api/v1/analytics/institution", headers=inst_h)
    assert r.status_code == 200, r.text
    body = r.json()
    # Aggregate-only shape — no per-student fields leak here.
    for k in ("courses", "students", "instructors", "completion_rate",
              "lms_connected", "course_rows"):
        assert k in body
    assert client.get("/api/v1/analytics/institution", headers=stu_h).status_code == 403


def test_lms_connected_flag_in_tool_config(client):
    r = client.get("/api/v1/lti/config")
    assert r.status_code == 200
    assert "lms_connected" in r.json()


def test_demo_login_returns_seeded_roles(client, db):
    _mk(db, "stu@demo.edu", "student")
    _mk(db, "prof@demo.edu", "instructor")
    s = client.post("/api/v1/auth/demo-login", json={"role": "student"})
    assert s.status_code == 200 and s.json()["role"] == "student"
    i = client.post("/api/v1/auth/demo-login", json={"role": "instructor"})
    assert i.status_code == 200 and i.json()["role"] == "instructor"
    assert i.json()["access_token"]


def test_demo_reset_restores_state(client, seeded):
    r = client.post("/api/v1/auth/demo-reset")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["courses_reset"] >= 1 and "modules_regenerated" in body


def test_demo_login_can_be_disabled(client, db, monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "demo_login_enabled", False)
    assert client.post("/api/v1/auth/demo-login", json={"role": "student"}).status_code == 404


def test_community_mode_admin_runs_everything(client, db, monkeypatch):
    """In community mode the single institution admin manages their own LMS + is never
    blocked by licensing — no separate platform operator needed."""
    from app.core.config import settings
    from app.models.tenant import Tenant
    from app.services import license_service
    monkeypatch.setattr(settings, "deployment_mode", "community")

    _mk(db, "admin@x.edu", "admin", platform=False)
    admin_h, _ = _login(client, "admin@x.edu")
    # Institution admin (no platform flag) can manage LMS registrations in community mode.
    assert client.get("/api/v1/lti/registrations", headers=admin_h).status_code == 200

    # Licensing never blocks a launch in community mode, even if "suspended".
    t = Tenant(name="T", slug="t-comm", subscription_status="suspended", plan="standard")
    db.add(t)
    db.flush()
    stu = _mk(db, "s@x.edu", "student", tenant_id=t.id)
    assert license_service.authorize_launch(db, t, stu).allowed


def test_lti_administrator_maps_to_institution_admin(db):
    # Reuse the simulated-platform helpers from test_lti.
    import time

    from jose import jwt

    from app.lti import claims as C
    from app.lti import jwks_client
    from app.lti.launch import validate_launch
    from app.lti.provisioning import provision
    from tests.test_lti import (
        CLIENT_ID,
        ISSUER,
        KID,
        _login_state,
        _platform_keypair,
        _register,
    )

    pem, jwks = _platform_keypair()
    reg = _register(db)
    jwks_client.prime_cache(reg.key_set_url, jwks)
    state, nonce = _login_state(db, reg)
    now = int(time.time())
    payload = {
        "iss": ISSUER, "aud": CLIENT_ID, "sub": "admin-1", "name": "Dr Admin",
        "nonce": nonce, "iat": now, "exp": now + 300,
        C.C_MESSAGE_TYPE: C.MSG_RESOURCE_LINK, C.C_VERSION: "1.3.0",
        C.C_DEPLOYMENT_ID: "dep-1",
        C.C_ROLES: ["http://purl.imsglobal.org/vocab/lis/v2/institution/person#Administrator"],
        C.C_CONTEXT: {"id": "c1", "title": "T"},
    }
    token = jwt.encode(payload, pem, algorithm="RS256", headers={"kid": KID})
    parsed = validate_launch(db, state=state, id_token=token)
    user, _course, _t = provision(db, parsed)
    assert user.role.value == "admin"          # institution admin
    assert user.is_platform_admin is False     # never granted via LTI
    assert user.tenant_id is not None          # scoped to their institution
