"""Tool RSA key management and JWKS construction for LTI 1.3.

The tool publishes its public key as a JWK Set (so platforms can verify the JWTs we
sign — e.g. Deep Linking responses and OAuth2 client assertions). The private key is
stored once in the database so it is stable across restarts and multiple instances.
"""
from __future__ import annotations

import base64
import uuid

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.lti import LtiToolKey


def _b64url_uint(n: int) -> str:
    raw = n.to_bytes((n.bit_length() + 7) // 8, "big")
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def get_or_create_tool_key(db: Session) -> LtiToolKey:
    key = db.scalar(select(LtiToolKey).where(LtiToolKey.active.is_(True)))
    if key:
        return key
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = private.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("ascii")
    key = LtiToolKey(kid=uuid.uuid4().hex, private_pem=pem, active=True)
    db.add(key)
    db.commit()
    db.refresh(key)
    return key


def private_pem(db: Session) -> tuple[str, str]:
    """Return (kid, private_pem) for signing."""
    key = get_or_create_tool_key(db)
    return key.kid, key.private_pem


def public_jwks(db: Session) -> dict:
    """Build the JWK Set exposing all active tool public keys (creating one if needed)."""
    get_or_create_tool_key(db)
    keys = db.scalars(select(LtiToolKey)).all()
    jwks = []
    for k in keys:
        private = serialization.load_pem_private_key(k.private_pem.encode(), password=None)
        numbers = private.public_key().public_numbers()
        jwks.append({
            "kty": "RSA",
            "use": "sig",
            "alg": "RS256",
            "kid": k.kid,
            "n": _b64url_uint(numbers.n),
            "e": _b64url_uint(numbers.e),
        })
    return {"keys": jwks}
