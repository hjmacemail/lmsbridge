from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import __version__
from app.core.config import settings
from app.db.session import get_db

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
        "brightspace_adapter": settings.brightspace_adapter,
        "database": "ok" if db_ok else "unavailable",
    }
