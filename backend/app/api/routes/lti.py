"""LTI 1.3 / Advantage tool-provider endpoints.

Flow: the LMS hits /lti/login (OIDC third-party login) -> we redirect to the platform's
auth endpoint -> the platform POSTs a signed id_token to /lti/launch -> we validate it,
provision the user/course, and redirect into the SPA (single sign-on).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import require_instructor, require_platform_admin
from app.core.config import settings
from app.db.session import get_db
from app.lti import keys
from app.lti.ags_sync import maybe_sync_assessments_on_launch, sync_course_from_ags
from app.lti.deeplink import build_deep_linking_response, resource_link_item
from app.lti.launch import validate_launch
from app.lti.oidc import LtiError, build_login_redirect
from app.lti.provisioning import maybe_sync_roster_on_launch, provision, sync_course_roster
from app.models.course import Course
from app.models.lti import LtiDeployment, LtiRegistration
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.lti import (
    DeploymentCreate,
    RegistrationCreate,
    RegistrationOut,
    RegistrationUpdate,
)

router = APIRouter(prefix="/lti", tags=["lti"])
# LMS registrations are a cross-tenant, platform-operator concern.
require_admin = require_platform_admin


@router.get("/jwks")
def jwks(db: Session = Depends(get_db)) -> dict:
    """Public JWK Set so platforms can verify JWTs signed by this tool."""
    return keys.public_jwks(db)


@router.get("/config")
def tool_config(db: Session = Depends(get_db)) -> dict:
    """Endpoints an LMS admin needs to register LMS Bridge as an LTI 1.3 tool."""
    base = settings.tool_base_url.rstrip("/")
    lms_connected = bool(
        db.scalar(
            select(func.count(LtiRegistration.id)).where(LtiRegistration.active.is_(True))
        )
    )
    return {
        "title": "LMS Bridge",
        "deployment_mode": settings.deployment_mode,
        "lms_connected": lms_connected,
        "oidc_initiation_url": f"{base}/api/v1/lti/login",
        "target_link_uri": f"{base}/api/v1/lti/launch",
        "redirect_uris": [f"{base}/api/v1/lti/launch"],
        "public_jwks_url": f"{base}/api/v1/lti/jwks",
        "deep_linking_url": f"{base}/api/v1/lti/launch",
        "dynamic_registration_url": f"{base}/api/v1/lti/register",
        "scopes": [
            "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem",
            "https://purl.imsglobal.org/spec/lti-ags/scope/result.readonly",
            "https://purl.imsglobal.org/spec/lti-ags/scope/score",
            "https://purl.imsglobal.org/spec/lti-nrps/scope/contextmembership.readonly",
        ],
    }


@router.api_route("/register", methods=["GET", "POST"], response_model=None)
async def dynamic_register(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """LTI Advantage Dynamic Registration endpoint (one-click setup in Canvas/Moodle)."""
    params = dict(request.query_params)
    if request.method == "POST":
        params.update(dict(await request.form()))
    openid_config = params.get("openid_configuration")
    if not openid_config:
        raise HTTPException(status_code=400, detail="Missing openid_configuration")
    from app.lti.dynamic_registration import register_with_platform
    try:
        reg = register_with_platform(
            db, openid_configuration_url=openid_config,
            registration_token=params.get("registration_token"),
        )
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Dynamic registration failed: {e}") from e
    # Tell the LMS the registration window can close.
    return HTMLResponse(
        f"<!doctype html><html><body>"
        f"<p>LMS Bridge registered successfully for <b>{reg.issuer}</b>. "
        f"You can close this window.</p>"
        "<script>"
        "if (window.opener) window.opener.postMessage("
        "{subject:'org.imsglobal.lti.close'}, '*');"
        "else window.parent.postMessage({subject:'org.imsglobal.lti.close'}, '*');"
        "</script></body></html>"
    )


async def _login_params(request: Request) -> dict:
    if request.method == "POST":
        form = await request.form()
        return dict(form)
    return dict(request.query_params)


@router.api_route("/login", methods=["GET", "POST"])
async def login(request: Request, db: Session = Depends(get_db)) -> RedirectResponse:
    p = await _login_params(request)
    issuer = p.get("iss")
    login_hint = p.get("login_hint")
    target_link_uri = p.get("target_link_uri")
    if not (issuer and login_hint and target_link_uri):
        raise HTTPException(status_code=400, detail="Missing iss/login_hint/target_link_uri")
    try:
        url = build_login_redirect(
            db,
            issuer=issuer,
            login_hint=login_hint,
            target_link_uri=target_link_uri,
            launch_redirect_uri=f"{settings.tool_base_url.rstrip('/')}/api/v1/lti/launch",
            client_id=p.get("client_id"),
            lti_message_hint=p.get("lti_message_hint"),
        )
    except LtiError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return RedirectResponse(url, status_code=302)


@router.post("/launch", response_model=None)
def launch(
    state: str = Form(...), id_token: str = Form(...), db: Session = Depends(get_db)
) -> HTMLResponse | RedirectResponse:
    try:
        parsed = validate_launch(db, state=state, id_token=id_token)
    except (LtiError, ValueError) as e:
        raise HTTPException(status_code=401, detail=f"LTI launch rejected: {e}") from e

    # Deep Linking: return a content item that places the tool back into the course.
    if parsed.is_deep_linking:
        base = settings.tool_base_url.rstrip("/")
        item = resource_link_item("LMS Bridge — Adaptive Learning", f"{base}/api/v1/lti/launch")
        return_url, jwt_token = build_deep_linking_response(db, parsed, content_items=[item])
        return HTMLResponse(_auto_post_form(return_url, {"JWT": jwt_token}))

    # Resource link launch: provision + single sign-on into the SPA.
    user, course, token = provision(db, parsed)

    # On an instructor/admin launch, import the whole class roster via NRPS and the
    # gradebook assessments via AGS, so the instructor console isn't empty.
    maybe_sync_roster_on_launch(db, parsed, course)
    maybe_sync_assessments_on_launch(db, parsed, course)

    # Licensing gate: block the launch (with a friendly screen) when the institution's
    # subscription/seat entitlement — or a self-hosted license — does not permit it.
    from app.models.tenant import Tenant
    from app.services import license_service
    tenant = db.get(Tenant, user.tenant_id) if user.tenant_id else None
    if tenant is not None:
        decision = license_service.authorize_launch(db, tenant, user)
        if not decision.allowed:
            return HTMLResponse(
                _license_blocked_page(decision.detail), status_code=403
            )

    fe = settings.frontend_base_url.rstrip("/")
    params = f"token={token}&role={user.role.value}"
    if course:
        params += f"&course_id={course.id}"
    return RedirectResponse(f"{fe}/lti?{params}", status_code=302)


@router.post("/courses/{course_id}/sync-roster")
def sync_roster_endpoint(
    course_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_instructor),
) -> dict:
    """Manually (re)import a course's roster from the LMS via NRPS."""
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if not course.lti_memberships_url:
        raise HTTPException(
            status_code=400,
            detail="No LMS roster link for this course yet — launch it once from the LMS "
            "as an instructor so LMS Bridge can capture the membership endpoint.",
        )
    tenant = db.get(Tenant, course.tenant_id) if course.tenant_id else None
    reg = (
        db.get(LtiRegistration, tenant.lti_registration_id)
        if tenant and tenant.lti_registration_id
        else None
    )
    if not reg:
        raise HTTPException(status_code=400, detail="No LMS registration is linked to this course.")
    try:
        return sync_course_roster(db, reg, course)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Roster sync failed: {e}") from e


@router.post("/courses/{course_id}/sync-assessments")
def sync_assessments_endpoint(
    course_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_instructor),
) -> dict:
    """Manually (re)import a course's assessments from the LMS gradebook via AGS."""
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if not course.lti_lineitems_url:
        raise HTTPException(
            status_code=400,
            detail="No LMS gradebook link for this course yet — launch it once from the LMS "
            "as an instructor so LMS Bridge can capture the AGS line-items endpoint.",
        )
    tenant = db.get(Tenant, course.tenant_id) if course.tenant_id else None
    reg = (
        db.get(LtiRegistration, tenant.lti_registration_id)
        if tenant and tenant.lti_registration_id
        else None
    )
    if not reg:
        raise HTTPException(status_code=400, detail="No LMS registration is linked to this course.")
    try:
        return sync_course_from_ags(
            db, course_id=course.id, reg=reg,
            ags_endpoint={"lineitems": course.lti_lineitems_url},
        )
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Assessment sync failed: {e}") from e


def _license_blocked_page(detail: str) -> str:
    contact = settings.license_contact_email
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        "<title>LMS Bridge — access unavailable</title>"
        "<style>body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;"
        "background:#f6f7f9;color:#1f2733;margin:0;display:flex;min-height:100vh;"
        "align-items:center;justify-content:center}"
        ".card{background:#fff;max-width:520px;padding:40px;border-radius:14px;"
        "box-shadow:0 6px 24px rgba(0,0,0,.08);text-align:center}"
        "h1{font-size:20px;margin:0 0 10px}p{line-height:1.55;color:#48566a}"
        ".badge{display:inline-block;font-size:12px;font-weight:600;color:#9a3412;"
        "background:#ffedd5;padding:4px 10px;border-radius:999px;margin-bottom:16px}"
        "a{color:#2563eb;text-decoration:none}</style></head><body>"
        "<div class='card'><div class='badge'>LMS Bridge</div>"
        "<h1>This tool isn't available right now</h1>"
        f"<p>{detail}</p>"
        f"<p>Administrators: contact <a href='mailto:{contact}'>{contact}</a> "
        "to restore access.</p></div></body></html>"
    )


def _auto_post_form(action: str, fields: dict[str, str]) -> str:
    inputs = "".join(
        f'<input type="hidden" name="{k}" value="{v}"/>' for k, v in fields.items()
    )
    return (
        f'<!doctype html><html><body onload="document.forms[0].submit()">'
        f'<form method="post" action="{action}">{inputs}'
        f'<noscript><button type="submit">Continue</button></noscript>'
        f"</form></body></html>"
    )


# ---- Admin: manage LMS registrations (manual onboarding for Blackboard/Brightspace) ----

def _load_reg(db: Session, reg_id: int) -> LtiRegistration:
    reg = db.scalar(
        select(LtiRegistration)
        .where(LtiRegistration.id == reg_id)
        .options(selectinload(LtiRegistration.deployments))
    )
    if not reg:
        raise HTTPException(status_code=404, detail="Registration not found")
    return reg


@router.get("/registrations", response_model=list[RegistrationOut])
def list_registrations(
    db: Session = Depends(get_db), _: User = Depends(require_admin)
) -> list[LtiRegistration]:
    return list(
        db.scalars(
            select(LtiRegistration)
            .options(selectinload(LtiRegistration.deployments))
            .order_by(LtiRegistration.id)
        ).all()
    )


@router.post("/registrations", response_model=RegistrationOut, status_code=201)
def create_registration(
    payload: RegistrationCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)
) -> LtiRegistration:
    if db.scalar(
        select(LtiRegistration).where(
            LtiRegistration.issuer == payload.issuer,
            LtiRegistration.client_id == payload.client_id,
        )
    ):
        raise HTTPException(status_code=409, detail="Registration for issuer+client_id exists")
    reg = LtiRegistration(
        name=payload.name, issuer=payload.issuer, client_id=payload.client_id,
        auth_login_url=payload.auth_login_url, auth_token_url=payload.auth_token_url,
        key_set_url=payload.key_set_url, audience=payload.audience, active=True,
    )
    db.add(reg)
    db.flush()
    if payload.deployment_id:
        db.add(LtiDeployment(registration_id=reg.id, deployment_id=payload.deployment_id))
    db.commit()
    return _load_reg(db, reg.id)


@router.put("/registrations/{reg_id}", response_model=RegistrationOut)
def update_registration(
    reg_id: int, payload: RegistrationUpdate, db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> LtiRegistration:
    reg = _load_reg(db, reg_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(reg, field, value)
    db.commit()
    return _load_reg(db, reg_id)


@router.delete("/registrations/{reg_id}", status_code=204)
def delete_registration(
    reg_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)
) -> None:
    db.delete(_load_reg(db, reg_id))
    db.commit()


@router.post("/registrations/{reg_id}/deployments", response_model=RegistrationOut, status_code=201)
def add_deployment(
    reg_id: int, payload: DeploymentCreate, db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> LtiRegistration:
    reg = _load_reg(db, reg_id)
    if not db.scalar(
        select(LtiDeployment).where(
            LtiDeployment.registration_id == reg.id,
            LtiDeployment.deployment_id == payload.deployment_id,
        )
    ):
        db.add(LtiDeployment(registration_id=reg.id, deployment_id=payload.deployment_id,
                             label=payload.label))
        db.commit()
    db.expire_all()  # reload the deployments collection
    return _load_reg(db, reg_id)
