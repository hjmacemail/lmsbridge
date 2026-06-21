"""LMS Bridge FastAPI application entrypoint."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.routes import (
    analytics,
    assessments,
    auth,
    courses,
    health,
    leads,
    lti,
    materials,
    remediation,
    sage,
    students,
    tenants,
)
from app.core.config import settings
from app.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger("app")


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info(
        "Starting %s v%s [env=%s, llm=%s, brightspace=%s]",
        settings.app_name, __version__, settings.app_env,
        settings.llm_provider, settings.brightspace_adapter,
    )
    # Idempotent: provision the platform operator from env vars (no shell needed on PaaS).
    from app.scripts.seed import ensure_platform_admin
    ensure_platform_admin()
    # Validate the self-hosted license file (no-op in SaaS mode).
    from app.services.license_service import load_self_hosted_license
    load_self_hosted_license()
    yield
    logger.info("Shutting down %s", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description=(
        "AI-guided adaptive learning layer that converts LMS analytics into "
        "just-in-time, pedagogically-constrained remediation for STEM courses."
    ),
    docs_url="/docs",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API = "/api/v1"
app.include_router(health.router, prefix=API)
app.include_router(auth.router, prefix=API)
app.include_router(courses.router, prefix=API)
app.include_router(assessments.router, prefix=API)
app.include_router(remediation.router, prefix=API)
app.include_router(students.router, prefix=API)
app.include_router(analytics.router, prefix=API)
app.include_router(materials.router, prefix=API)
app.include_router(lti.router, prefix=API)
app.include_router(leads.router, prefix=API)
app.include_router(tenants.router, prefix=API)
app.include_router(sage.router, prefix=API)
