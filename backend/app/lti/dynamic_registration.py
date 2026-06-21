"""LTI Advantage Dynamic Registration (one-click tool setup for Canvas/Moodle).

Flow: the LMS opens the tool's registration URL with an `openid_configuration` URL (and
optional `registration_token`). The tool fetches that config, POSTs an OpenID client
registration describing itself (LTI tool configuration), and stores the resulting
registration so launches work immediately.

Spec: 1EdTech LTI Dynamic Registration + OpenID Connect Dynamic Client Registration.
"""
from __future__ import annotations

from urllib.parse import urlparse

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.lti import claims as C
from app.models.lti import LtiDeployment, LtiRegistration

logger = get_logger("lti.dynreg")

LTI_TOOL_CONFIG = "https://purl.imsglobal.org/spec/lti-tool-configuration"
SCOPES = [
    C.SCOPE_AGS_LINEITEM, C.SCOPE_AGS_RESULT, C.SCOPE_AGS_SCORE, C.SCOPE_NRPS,
]


def _tool_registration_body() -> dict:
    base = settings.tool_base_url.rstrip("/")
    domain = urlparse(base).netloc
    launch = f"{base}/api/v1/lti/launch"
    return {
        "application_type": "web",
        "response_types": ["id_token"],
        "grant_types": ["client_credentials", "implicit"],
        "initiate_login_uri": f"{base}/api/v1/lti/login",
        "redirect_uris": [launch],
        "client_name": settings.app_name,
        "jwks_uri": f"{base}/api/v1/lti/jwks",
        "logo_uri": f"{base}/favicon.ico",
        "token_endpoint_auth_method": "private_key_jwt",
        "scope": " ".join(SCOPES),
        LTI_TOOL_CONFIG: {
            "domain": domain,
            "target_link_uri": launch,
            "claims": ["iss", "sub", "name", "email"],
            "messages": [
                # Course-level launch. Advertise the placements so the platform
                # actually surfaces the tool: course_navigation puts an "LMS Bridge"
                # link in the course menu (Canvas), link/assignment selection enable
                # placing it as content.
                {
                    "type": "LtiResourceLinkRequest",
                    "target_link_uri": launch,
                    "label": settings.app_name,
                    "icon_uri": f"{base}/favicon.ico",
                    "placements": ["course_navigation", "link_selection", "assignment_selection"],
                    # Canvas extensions: show to all roles, enabled by default.
                    "https://canvas.instructure.com/lti/course_navigation/default_enabled": True,
                    "https://canvas.instructure.com/lti/visibility": "public",
                },
                {
                    "type": "LtiDeepLinkingRequest",
                    "target_link_uri": launch,
                    "label": settings.app_name,
                    "placements": ["link_selection", "assignment_selection"],
                },
            ],
        },
    }


def register_with_platform(
    db: Session, *, openid_configuration_url: str, registration_token: str | None
) -> LtiRegistration:
    # 1. Fetch the platform's OpenID configuration.
    cfg = httpx.get(openid_configuration_url, timeout=15.0)
    cfg.raise_for_status()
    config = cfg.json()
    issuer = config["issuer"]
    registration_endpoint = config["registration_endpoint"]

    # 2. Register this tool as an OpenID client with the platform.
    headers = {"Content-Type": "application/json"}
    if registration_token:
        headers["Authorization"] = f"Bearer {registration_token}"
    resp = httpx.post(
        registration_endpoint, json=_tool_registration_body(), headers=headers, timeout=20.0
    )
    resp.raise_for_status()
    reg_resp = resp.json()
    client_id = reg_resp["client_id"]

    # 3. Persist (or update) the registration. Deployment id arrives at first launch.
    existing = db.scalar(
        select(LtiRegistration).where(
            LtiRegistration.issuer == issuer, LtiRegistration.client_id == client_id
        )
    )
    reg = existing or LtiRegistration(issuer=issuer, client_id=client_id, name=issuer)
    reg.name = config.get("https://purl.imsglobal.org/spec/lti-platform-configuration", {}).get(
        "product_family_code", issuer
    ) or issuer
    reg.client_id = client_id
    reg.auth_login_url = config["authorization_endpoint"]
    reg.auth_token_url = config["token_endpoint"]
    reg.key_set_url = config["jwks_uri"]
    reg.active = True
    reg.auto_register_deployments = True
    if not existing:
        db.add(reg)
    db.flush()

    # Some platforms return a deployment_id in the tool-config echo.
    dep = (reg_resp.get(LTI_TOOL_CONFIG) or {}).get("deployment_id")
    if dep and not db.scalar(
        select(LtiDeployment).where(
            LtiDeployment.registration_id == reg.id, LtiDeployment.deployment_id == dep
        )
    ):
        db.add(LtiDeployment(registration_id=reg.id, deployment_id=dep, label="dynamic"))

    db.commit()
    db.refresh(reg)
    logger.info("Dynamic registration complete for issuer=%s client_id=%s", issuer, client_id)
    return reg
