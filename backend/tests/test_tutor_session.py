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
