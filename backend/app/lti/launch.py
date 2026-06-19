"""Validate an LTI 1.3 launch id_token and parse its claims."""
from __future__ import annotations

from dataclasses import dataclass, field

from jose import jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.lti import claims as C
from app.lti.jwks_client import find_key
from app.lti.oidc import LtiError
from app.models.lti import LtiDeployment, LtiNonce, LtiRegistration


@dataclass
class LtiLaunch:
    registration: LtiRegistration
    message_type: str
    deployment_id: str
    sub: str
    name: str | None
    email: str | None
    roles: list[str]
    context_id: str | None
    context_title: str | None
    resource_link_id: str | None
    resource_link_title: str | None
    target_link_uri: str | None
    ags: dict | None = None
    nrps: dict | None = None
    deep_linking_settings: dict | None = None
    custom: dict = field(default_factory=dict)
    raw: dict = field(default_factory=dict)

    @property
    def is_deep_linking(self) -> bool:
        return self.message_type == C.MSG_DEEP_LINKING


def _consume_state(db: Session, state: str) -> LtiNonce:
    row = db.scalar(select(LtiNonce).where(LtiNonce.state == state))
    if not row:
        raise LtiError("Unknown or expired launch state")
    if row.used:
        raise LtiError("Launch state already used (possible replay)")
    row.used = True
    db.flush()
    return row


def validate_launch(db: Session, *, state: str, id_token: str) -> LtiLaunch:
    """Full spec validation: state, signature, iss/aud/nonce/exp, deployment, message type."""
    nonce_row = _consume_state(db, state)
    reg = db.get(LtiRegistration, nonce_row.registration_id) if nonce_row.registration_id else None
    if not reg:
        raise LtiError("Launch registration not found")

    # Resolve the platform signing key by `kid` and verify the signature + standard claims.
    header = jwt.get_unverified_header(id_token)
    key = find_key(reg.key_set_url, header.get("kid", ""))
    try:
        payload = jwt.decode(
            id_token, key, algorithms=["RS256"],
            audience=reg.client_id, issuer=reg.issuer,
            options={"verify_at_hash": False},
        )
    except Exception as e:  # noqa: BLE001
        raise LtiError(f"id_token validation failed: {e}") from e

    # azp must equal our client_id when multiple audiences are present.
    aud = payload.get("aud")
    if isinstance(aud, list) and len(aud) > 1 and payload.get("azp") != reg.client_id:
        raise LtiError("azp does not match client_id")

    # nonce must match the value we issued at login.
    if payload.get("nonce") != nonce_row.nonce:
        raise LtiError("nonce mismatch")

    # LTI version + message type.
    if payload.get(C.C_VERSION) != "1.3.0":
        raise LtiError("Unsupported LTI version")
    message_type = payload.get(C.C_MESSAGE_TYPE)
    if message_type not in (C.MSG_RESOURCE_LINK, C.MSG_DEEP_LINKING):
        raise LtiError(f"Unsupported message_type {message_type}")

    # Deployment must be registered.
    deployment_id = payload.get(C.C_DEPLOYMENT_ID)
    known = db.scalar(
        select(LtiDeployment).where(
            LtiDeployment.registration_id == reg.id,
            LtiDeployment.deployment_id == deployment_id,
        )
    )
    if not known:
        # The launch is cryptographically verified against the platform's keys and matches a
        # known registration; for dynamically-registered platforms we trust the deployment_id
        # asserted by that verified launch (the deployment id is delivered at launch time).
        if reg.auto_register_deployments and deployment_id:
            db.add(LtiDeployment(registration_id=reg.id, deployment_id=deployment_id,
                                 label="auto (dynamic registration)"))
            db.flush()
        else:
            raise LtiError(f"Unknown deployment_id {deployment_id}")

    context = payload.get(C.C_CONTEXT) or {}
    resource = payload.get(C.C_RESOURCE_LINK) or {}
    db.commit()
    return LtiLaunch(
        registration=reg,
        message_type=message_type,
        deployment_id=deployment_id,
        sub=payload.get("sub", ""),
        name=payload.get("name") or payload.get("given_name"),
        email=payload.get("email"),
        roles=payload.get(C.C_ROLES, []),
        context_id=context.get("id"),
        context_title=context.get("title") or context.get("label"),
        resource_link_id=resource.get("id"),
        resource_link_title=resource.get("title"),
        target_link_uri=payload.get(C.C_TARGET_LINK_URI),
        ags=payload.get(C.C_AGS_ENDPOINT),
        nrps=payload.get(C.C_NRPS),
        deep_linking_settings=payload.get(C.C_DL_SETTINGS),
        custom=payload.get(C.C_CUSTOM, {}) or {},
        raw=payload,
    )
