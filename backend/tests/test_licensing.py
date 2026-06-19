"""Licensing: signed self-hosted token + launch entitlement gating."""
import time

import pytest
from jose import jwt

from app.models.enums import UserRole
from app.models.tenant import Tenant
from app.models.user import User
from app.services import license_service as L
from app.services.license_service import LICENSE_ISSUER


def _keypair():
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    pub = key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return priv, pub


def _token(priv, *, seats=100, days=365, iss=LICENSE_ISSUER):
    now = int(time.time())
    return jwt.encode(
        {"iss": iss, "sub": "Acme U", "plan": "enterprise", "seats": seats,
         "iat": now, "exp": now + days * 86400},
        priv, algorithm="RS256",
    )


def test_signed_license_valid_and_tampered():
    priv, pub = _keypair()
    tok = _token(priv)
    claims = L.verify_license_token(tok, pub)
    assert claims["sub"] == "Acme U" and claims["seats"] == 100
    # Tamper: a different keypair's public key must reject it.
    _, other_pub = _keypair()
    with pytest.raises(Exception):
        L.verify_license_token(tok, other_pub)


def test_expired_license_rejected():
    priv, pub = _keypair()
    tok = _token(priv, days=-1)  # already expired
    with pytest.raises(Exception):
        L.verify_license_token(tok, pub)


def _mk_student(db, tid, n=1):
    from app.core.security import hash_password
    out = []
    for i in range(n):
        u = User(email=f"s{i}-{tid}@x.edu", full_name=f"S{i}", role=UserRole.student,
                 tenant_id=tid, hashed_password=hash_password("pw"))
        db.add(u)
        out.append(u)
    db.commit()
    return out


def test_launch_blocked_when_subscription_inactive(db):
    t = Tenant(name="T", slug="t-block", subscription_status="suspended", plan="standard")
    db.add(t)
    db.flush()
    (student,) = _mk_student(db, t.id)
    d = L.authorize_launch(db, t, student)
    assert not d.allowed and d.reason == "subscription_suspended"


def test_launch_allowed_for_trial_and_active(db):
    for status in ("trial", "active"):
        t = Tenant(name="T", slug=f"t-{status}", subscription_status=status, plan="pilot")
        db.add(t)
        db.flush()
        (student,) = _mk_student(db, t.id)
        assert L.authorize_launch(db, t, student).allowed


def test_seat_limit_blocks_only_overflow_students(db):
    t = Tenant(name="T", slug="t-seats", subscription_status="active",
               plan="standard", seat_limit=2)
    db.add(t)
    db.flush()
    s1, s2, s3 = _mk_student(db, t.id, n=3)
    # First two by id are within the cap; the third is the overflow.
    assert L.authorize_launch(db, t, s1).allowed
    assert L.authorize_launch(db, t, s2).allowed
    over = L.authorize_launch(db, t, s3)
    assert not over.allowed and over.reason == "seat_limit_reached"


def test_staff_never_blocked_by_seat_limit(db):
    from app.core.security import hash_password
    t = Tenant(name="T", slug="t-staff", subscription_status="active",
               plan="standard", seat_limit=0)
    db.add(t)
    db.flush()
    instr = User(email="prof@x.edu", full_name="Prof", role=UserRole.instructor,
                 tenant_id=t.id, hashed_password=hash_password("pw"))
    db.add(instr)
    db.commit()
    assert L.authorize_launch(db, t, instr).allowed
