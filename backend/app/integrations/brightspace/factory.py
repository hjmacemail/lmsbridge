"""Factory selecting the configured Brightspace adapter."""
from __future__ import annotations

from functools import lru_cache

from app.core.config import settings
from app.core.logging import get_logger
from app.integrations.brightspace.base import BrightspaceAdapter
from app.integrations.brightspace.mock import MockBrightspaceAdapter

logger = get_logger("brightspace")


@lru_cache
def get_brightspace_adapter() -> BrightspaceAdapter:
    adapter = settings.brightspace_adapter.lower()
    if adapter == "valence":
        try:
            from app.integrations.brightspace.valence import ValenceBrightspaceAdapter
            return ValenceBrightspaceAdapter()
        except Exception as e:  # noqa: BLE001
            logger.error("Valence adapter init failed (%s); falling back to mock.", e)
    return MockBrightspaceAdapter()
