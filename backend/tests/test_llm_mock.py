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
