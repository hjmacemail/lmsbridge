"""LTI hardening: launch-state TTL (anti-replay) and unambiguous registration lookup."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.lti.launch import LAUNCH_STATE_TTL, _consume_state
from app.lti.oidc import LtiError, find_registration
from app.models.lti import LtiNonce, LtiRegistration


def _reg(db, issuer="https://lms.example.edu", client_id="client-A") -> LtiRegistration:
    reg = LtiRegistration(
        name="X", issuer=issuer, client_id=client_id,
        auth_login_url=f"{issuer}/auth", auth_token_url=f"{issuer}/token",
        key_set_url=f"{issuer}/jwks", active=True,
    )
    db.add(reg); db.flush()
    return reg


def _nonce(db, reg, *, state, age_minutes=0):
    db.add(LtiNonce(
        state=state, nonce="n-" + state, registration_id=reg.id,
        created_at=datetime.now(timezone.utc) - timedelta(minutes=age_minutes),
    ))
    db.commit()


def test_fresh_state_consumes_but_expired_is_rejected(db):
    reg = _reg(db)
    _nonce(db, reg, state="fresh", age_minutes=1)
    assert _consume_state(db, "fresh").state == "fresh"       # within TTL -> ok
    # Reusing it now fails (already used).
    with pytest.raises(LtiError):
        _consume_state(db, "fresh")

    old = int(LAUNCH_STATE_TTL.total_seconds() // 60) + 5
    _nonce(db, reg, state="stale", age_minutes=old)
    with pytest.raises(LtiError):
        _consume_state(db, "stale")                           # past TTL -> replay rejected


def test_find_registration_disambiguation(db):
    iss = "https://multi.example.edu"
    a = _reg(db, issuer=iss, client_id="A")
    # One registration + no client_id -> resolves fine.
    assert find_registration(db, iss, None).id == a.id
    # Add a second registration for the same issuer.
    b = _reg(db, issuer=iss, client_id="B")
    db.commit()
    # No client_id is now ambiguous -> error; with client_id it picks the right one.
    with pytest.raises(LtiError):
        find_registration(db, iss, None)
    assert find_registration(db, iss, "B").id == b.id
