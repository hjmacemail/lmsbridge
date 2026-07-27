"""Interactive AI-tutor session: opening turn, dialogue, completion, mastery bump."""
from sqlalchemy import select

from app.models.enums import RemediationStatus
from app.models.mastery import ConceptMastery
from app.models.remediation import RemediationModule, TutorMessage


def _login(client, email, pw="pw"):
    r = client.post("/api/v1/auth/login", data={"username": email, "password": pw})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _student_with_module(db):
    from app.core.security import hash_password
    module = db.scalars(select(RemediationModule)).first()
    student = db.get(type(module.student), module.student_id)
    student.hashed_password = hash_password("pw")
    db.commit()
    return student, module


def test_session_start_creates_opening_turn(client, db, seeded):
    student, module = _student_with_module(db)
    h = _login(client, student.email)
    r = client.post(f"/api/v1/remediation/modules/{module.id}/session/start", headers=h)
    assert r.status_code == 200, r.text
    state = r.json()
    assert state["status"] == "in_progress"
    assert len(state["messages"]) == 1
    assert state["messages"][0]["role"] == "tutor"
    # Structured learning context for the tutoring UI.
    assert state["concept_name"]
    assert isinstance(state["objectives"], list)
    assert "mastery_score" in state
    assert "evidence" in state  # may be null when no MCQ trigger exists


def test_session_completes_and_raises_mastery(client, db, seeded):
    student, module = _student_with_module(db)
    concept_id = module.concept_id
    h = _login(client, student.email)
    client.post(f"/api/v1/remediation/modules/{module.id}/session/start", headers=h)

    before = db.scalar(
        select(ConceptMastery.mastery_score).where(
            ConceptMastery.student_id == student.id,
            ConceptMastery.concept_id == concept_id,
        )
    )

    complete = False
    for msg in [
        "I think it relates to the topic but I mixed up the key rule on that question.",
        "Right — the rule is applied at runtime based on the actual object, not the reference.",
        "So the overridden method runs because dispatch uses the real object's type.",
        "I can now justify each step by naming the rule before applying it.",
    ]:
        resp = client.post(
            f"/api/v1/remediation/modules/{module.id}/session/message",
            headers=h, json={"text": msg},
        )
        assert resp.status_code == 200, resp.text
        if resp.json()["complete"]:
            complete = True
            break

    assert complete, "session should complete after enough substantive turns"
    db.expire_all()
    refreshed = db.get(RemediationModule, module.id)
    assert refreshed.status == RemediationStatus.completed
    # A transcript was recorded.
    assert db.scalars(
        select(TutorMessage).where(TutorMessage.module_id == module.id)
    ).all()
    after = db.scalar(
        select(ConceptMastery.mastery_score).where(
            ConceptMastery.student_id == student.id,
            ConceptMastery.concept_id == concept_id,
        )
    )
    assert after >= (before or 0), "completing the session should not lower mastery"


def test_turn_response_includes_choices_key(client, db, seeded):
    student, module = _student_with_module(db)
    h = _login(client, student.email)
    client.post(f"/api/v1/remediation/modules/{module.id}/session/start", headers=h)
    r = client.post(f"/api/v1/remediation/modules/{module.id}/session/message",
                    headers=h, json={"text": "not sure"})
    assert r.status_code == 200, r.text
    assert "choices" in r.json()  # null with the mock; a list when the model poses an MCQ


def test_session_never_exceeds_turn_cap(client, db, seeded):
    from app.services.tutor_session_service import MAX_STUDENT_TURNS
    student, module = _student_with_module(db)
    h = _login(client, student.email)
    client.post(f"/api/v1/remediation/modules/{module.id}/session/start", headers=h)
    completed = False
    for _ in range(MAX_STUDENT_TURNS):
        r = client.post(f"/api/v1/remediation/modules/{module.id}/session/message",
                        headers=h, json={"text": "hmm"})
        if r.status_code == 409:  # already completed earlier — fine
            completed = True
            break
        if r.json()["complete"]:
            completed = True
            break
    assert completed, "session must end by the turn cap, never run forever"


def test_end_session_completes_module(client, db, seeded):
    student, module = _student_with_module(db)
    h = _login(client, student.email)
    client.post(f"/api/v1/remediation/modules/{module.id}/session/start", headers=h)
    r = client.post(f"/api/v1/remediation/modules/{module.id}/complete", headers=h)
    assert r.status_code == 200, r.text
    db.expire_all()
    assert db.get(RemediationModule, module.id).status == RemediationStatus.completed


class _FakeLLM:
    """Scripted provider: returns each queued raw text in turn (last one repeats)."""
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def complete(self, messages, *, json_mode=False):
        from app.llm.base import LLMResponse
        i = min(self.calls, len(self.responses) - 1)
        self.calls += 1
        return LLMResponse(text=self.responses[i], model="fake", provider="fake")


def test_salvage_reply_recovers_unescaped_inner_quote():
    from app.services.tutor_session_service import _salvage_reply
    bad = '{"reply": "You said "1011" means eleven, right?", "complete": false}'
    assert _salvage_reply(bad) == 'You said "1011" means eleven, right?'


def test_salvage_reply_accepts_prose_and_rejects_unrecoverable():
    from app.services.tutor_session_service import _salvage_reply
    assert _salvage_reply("Keep exploring the place values.") == "Keep exploring the place values."
    assert _salvage_reply('{"foo": 3}') is None
    assert _salvage_reply("") is None


def test_tutor_turn_retries_malformed_then_parses():
    from app.llm.base import LLMMessage
    from app.services.tutor_session_service import _tutor_turn
    fake = _FakeLLM(["totally not json {oops", '{"reply": "Great — what is 2^3?", "complete": false}'])
    reply, complete, choices = _tutor_turn(fake, [LLMMessage("user", "hi")], at_limit=False)
    assert fake.calls == 2, "should retry once on malformed JSON"
    assert reply == "Great — what is 2^3?"
    assert complete is False


def test_post_message_salvages_reply_instead_of_canned(db, seeded, monkeypatch):
    """A malformed reply (unescaped quotes) must surface the model's real words, never the
    old canned 'walk me through your reasoning step by step' line that used to loop."""
    from app.services import tutor_session_service as svc
    _student, module = _student_with_module(db)
    bad = '{"reply": "Think about what the "leftmost" bit is worth.", "complete": false}'
    fake = _FakeLLM([bad, bad])  # first + retry both malformed -> salvage from raw
    monkeypatch.setattr(svc, "resolve_provider", lambda *a, **k: fake)
    out = svc.post_message(db, module, "hint please")
    assert out["reply"] == 'Think about what the "leftmost" bit is worth.'
    assert "walk me through your reasoning step by step" not in out["reply"]


def test_post_message_help_fallback_when_unrecoverable(db, seeded, monkeypatch):
    from app.services import tutor_session_service as svc
    _student, module = _student_with_module(db)
    # Parses as JSON but has no usable reply -> helpful, concept-aware fallback (not canned).
    fake = _FakeLLM(['{"complete": false}'])
    monkeypatch.setattr(svc, "resolve_provider", lambda *a, **k: fake)
    out = svc.post_message(db, module, "I still don't get it")
    assert "one small step" in out["reply"]
    assert "walk me through your reasoning step by step" not in out["reply"]


def test_tutor_prompt_includes_language_instruction():
    from app.models.enums import PedagogyStrategy
    from app.pedagogy.prompts import build_tutor_session_system_prompt, language_name
    assert language_name("en") is None and language_name("ar") == "Arabic"
    p = build_tutor_session_system_prompt(
        course_title="CS", concept_name="Binary", concept_description=None,
        strategy=PedagogyStrategy.socratic_scaffolding, objectives=["x"],
        evidence_summary="ev", material_excerpts=None, language="ar",
    )
    assert "Arabic" in p
    # English (default) adds no language directive.
    p_en = build_tutor_session_system_prompt(
        course_title="CS", concept_name="Binary", concept_description=None,
        strategy=PedagogyStrategy.socratic_scaffolding, objectives=["x"],
        evidence_summary="ev", material_excerpts=None, language="en",
    )
    assert "LANGUAGE:" not in p_en
