from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import __version__
from app.core.config import settings
from app.db.session import get_db
from app.llm.guard import last_provider_error

router = APIRouter(tags=["health"])


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict:
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:  # noqa: BLE001
        db_ok = False
    return {
        "status": "ok" if db_ok else "degraded",
        "version": __version__,
        "env": settings.app_env,
        "deployment_mode": settings.deployment_mode,
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model,
        # null = the real model is working (or hasn't been called yet); a string = it errored and
        # the app fell back to the mock. This is the fastest way to spot a bad key/model id.
        "llm_last_error": last_provider_error(),
        "brightspace_adapter": settings.brightspace_adapter,
        "database": "ok" if db_ok else "unavailable",
    }
