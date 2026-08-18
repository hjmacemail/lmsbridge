"""Localization helper: translates via the model, but safely falls back to English."""
from app.services.localize_service import localize_texts


class _FakeLLM:
    def __init__(self, text):
        self._text = text
    def complete(self, messages, *, json_mode=False):
        from app.llm.base import LLMResponse
        return LLMResponse(text=self._text, model="fake", provider="fake")


def test_english_and_empty_are_passthrough(db):
    # English / None locale: never calls a model, returns input unchanged.
    assert localize_texts(db, None, ["Forgets zero is representable"], "en") == \
        ["Forgets zero is representable"]
    assert localize_texts(db, None, [], "ar") == []


def test_translation_applied_when_model_returns_items(db, monkeypatch):
    import app.services.localize_service as svc
    monkeypatch.setattr(svc, "resolve_provider",
                        lambda *a, **k: _FakeLLM('{"items": ["ينسى أن الصفر قابل للتمثيل"]}'))
    out = localize_texts(db, 1, ["Forgets zero is representable"], "ar")
    assert out == ["ينسى أن الصفر قابل للتمثيل"]


def test_length_mismatch_falls_back_to_source(db, monkeypatch):
    import app.services.localize_service as svc
    monkeypatch.setattr(svc, "resolve_provider",
                        lambda *a, **k: _FakeLLM('{"items": ["only one"]}'))
    src = ["a misconception", "another one"]
    assert localize_texts(db, 1, src, "ar") == src  # unchanged on mismatch


def test_bad_output_falls_back_to_source(db, monkeypatch):
    import app.services.localize_service as svc
    monkeypatch.setattr(svc, "resolve_provider", lambda *a, **k: _FakeLLM("not json at all"))
    src = ["keeps its English"]
    assert localize_texts(db, 1, src, "ar") == src


def test_empty_strings_are_preserved(db, monkeypatch):
    import app.services.localize_service as svc
    # Only the non-empty item is sent/translated; the empty one stays empty.
    monkeypatch.setattr(svc, "resolve_provider", lambda *a, **k: _FakeLLM('{"items": ["مترجم"]}'))
    assert localize_texts(db, 1, ["", "translate me"], "ar") == ["", "مترجم"]
