from app.llm.base import LLMMessage
from app.llm.providers.mock import MockProvider, extract_json


def test_mock_generates_activities_json():
    p = MockProvider("mock-model")
    resp = p.complete(
        [LLMMessage("user", "Concept: Binary Arithmetic")], json_mode=True
    )
    data = extract_json(resp.text)
    assert data["activities"]
    assert all("prompt" in a for a in data["activities"])


def test_mock_feedback_judges_short_response_partial():
    p = MockProvider("mock-model")
    resp = p.complete(
        [LLMMessage("user", "Evaluate. Student response: idk")], json_mode=True
    )
    data = extract_json(resp.text)
    assert data["is_correct"] is False


def test_extract_json_tolerates_real_model_quirks():
    # Real models emit fences, multi-line (unescaped-newline) strings, and trailing commas.
    fenced = '```json\n{\n  "reply": "Line one\nLine two",\n  "complete": false,\n}\n```'
    data = extract_json(fenced)
    assert data["reply"].startswith("Line one")
    assert data["complete"] is False
