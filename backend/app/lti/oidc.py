"""OIDC third-party login initiation (LTI 1.3 first leg of the launch)."""
from __future__ import annotations

import secrets
from urllib.parse import urlencode

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.lti import LtiNonce, LtiRegistration


class LtiError(Exception):
    pass


def find_registration(
    db: Session, issuer: str, client_id: str | None
) -> LtiRegistration:
    stmt = select(LtiRegistration).where(
        LtiRegistration.issuer == issuer, LtiRegistration.active.is_(True)
    )
    if client_id:
        stmt = stmt.where(LtiRegistration.client_id == client_id)
    reg = db.scalars(stmt).first()
    if not reg:
        raise LtiError(f"No LTI registration for issuer={issuer} client_id={client_id}")
    return reg


def build_login_redirect(
    db: Session,
    *,
    issuer: str,
    login_hint: str,
    target_link_uri: str,
    launch_redirect_uri: str,
    client_id: str | None = None,
    lti_message_hint: str | None = None,
) -> str:
    """Validate the login request, persist state+nonce, and build the platform auth URL."""
    reg = find_registration(db, issuer, client_id)
    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    db.add(LtiNonce(
        state=state, nonce=nonce, registration_id=reg.id, target_link_uri=target_link_uri,
    ))
    db.commit()

    params = {
        "scope": "openid",
        "response_type": "id_token",
        "response_mode": "form_post",
        "prompt": "none",
        "client_id": client_id or reg.client_id,
        "redirect_uri": launch_redirect_uri,
        "state": state,
        "nonce": nonce,
        "login_hint": login_hint,
    }
    if lti_message_hint:
        params["lti_message_hint"] = lti_message_hint
    sep = "&" if "?" in reg.auth_login_url else "?"
    return f"{reg.auth_login_url}{sep}{urlencode(params)}"
