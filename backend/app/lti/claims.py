"""LTI 1.3 claim URIs and role helpers (1EdTech spec)."""
from __future__ import annotations

LTI = "https://purl.imsglobal.org/spec/lti/claim"
AGS = "https://purl.imsglobal.org/spec/lti-ags/claim"
NRPS = "https://purl.imsglobal.org/spec/lti-nrps/claim"
DL = "https://purl.imsglobal.org/spec/lti-dl/claim"

C_MESSAGE_TYPE = f"{LTI}/message_type"
C_VERSION = f"{LTI}/version"
C_DEPLOYMENT_ID = f"{LTI}/deployment_id"
C_TARGET_LINK_URI = f"{LTI}/target_link_uri"
C_RESOURCE_LINK = f"{LTI}/resource_link"
C_ROLES = f"{LTI}/roles"
C_CONTEXT = f"{LTI}/context"
C_CUSTOM = f"{LTI}/custom"
C_AGS_ENDPOINT = f"{AGS}/endpoint"
C_NRPS = f"{NRPS}/namesroleservice"
C_DL_SETTINGS = f"{DL}/deep_linking_settings"
C_DL_CONTENT_ITEMS = f"{DL}/content_items"
C_DL_DATA = f"{DL}/data"

MSG_RESOURCE_LINK = "LtiResourceLinkRequest"
MSG_DEEP_LINKING = "LtiDeepLinkingRequest"

# Token scopes for the LTI Advantage services.
SCOPE_AGS_LINEITEM = "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem"
SCOPE_AGS_RESULT = "https://purl.imsglobal.org/spec/lti-ags/scope/result.readonly"
SCOPE_AGS_SCORE = "https://purl.imsglobal.org/spec/lti-ags/scope/score"
SCOPE_NRPS = "https://purl.imsglobal.org/spec/lti-nrps/scope/contextmembership.readonly"

# Administrator / sysadmin LTI roles -> institution admin in LMS Bridge.
_ADMIN_MARKERS = ("#Administrator", "#SysAdmin", "#AccountAdmin")
_INSTRUCTOR_MARKERS = ("#Instructor", "#ContentDeveloper", "#TeachingAssistant")


def _has(roles: list[str], markers: tuple[str, ...]) -> bool:
    return any(any(m in r for m in markers) for r in roles or [])


def is_admin_role(roles: list[str]) -> bool:
    return _has(roles, _ADMIN_MARKERS)


def is_instructor(roles: list[str]) -> bool:
    return _has(roles, _INSTRUCTOR_MARKERS)
