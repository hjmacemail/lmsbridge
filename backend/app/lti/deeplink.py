"""Build a signed LTI Deep Linking response (places content back into the LMS course)."""
from __future__ import annotations

import time
import uuid

from jose import jwt
from sqlalchemy.orm import Session

from app.lti import claims as C
from app.lti.keys import private_pem
from app.lti.launch import LtiLaunch


def build_deep_linking_response(
    db: Session, launch: LtiLaunch, *, content_items: list[dict]
) -> tuple[str, str]:
    """Return (return_url, signed_jwt) to auto-POST back to the platform."""
    settings = launch.deep_linking_settings or {}
    return_url = settings.get("deep_link_return_url", "")
    kid, pem = private_pem(db)
    now = int(time.time())
    payload = {
        "iss": launch.registration.client_id,
        "aud": launch.registration.issuer,
        "iat": now,
        "exp": now + 600,
        "nonce": uuid.uuid4().hex,
        C.C_MESSAGE_TYPE: "LtiDeepLinkingResponse",
        C.C_VERSION: "1.3.0",
        C.C_DEPLOYMENT_ID: launch.deployment_id,
        C.C_DL_CONTENT_ITEMS: content_items,
    }
    if settings.get("data"):
        payload[C.C_DL_DATA] = settings["data"]
    token = jwt.encode(payload, pem, algorithm="RS256", headers={"kid": kid})
    return return_url, token


def resource_link_item(title: str, url: str, custom: dict | None = None) -> dict:
    item = {"type": "ltiResourceLink", "title": title, "url": url}
    if custom:
        item["custom"] = custom
    return item
