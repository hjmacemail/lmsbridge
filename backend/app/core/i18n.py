"""Supported UI/AI languages and locale normalization.

Keep this list in sync with the frontend's i18n locales (frontend/src/i18n). A locale coming from
the LMS launch (e.g. "es-419", "ar-SA", "fr_CA") is normalized to the base language we ship.
"""
from __future__ import annotations

# Must match frontend/src/i18n supportedLngs.
SUPPORTED_LANGS: tuple[str, ...] = ("en", "es", "fr", "ar")


def normalize_lang(locale: str | None) -> str | None:
    """Return a supported base language for an incoming locale, or None if unsupported/empty.

    Examples: "es-419" -> "es", "AR" -> "ar", "fr_CA" -> "fr", "de" -> None.
    """
    if not locale:
        return None
    base = locale.strip().lower().replace("_", "-").split("-")[0]
    return base if base in SUPPORTED_LANGS else None
