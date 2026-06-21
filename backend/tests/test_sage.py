"""Sage standalone mini-LMS: signup, course, quiz authoring, take/submit -> remediation, grades."""
from __future__ import annotations


def _auth(resp_json):
    return {"Authorization": f"Bearer {resp_json['access_token']}"}


def _quiz_payload():
    return {"title": "Binary basics", "questions": [
        {"prompt": "1011 in decimal?", "choices": ["9", "11", "13"], "correct": "11",
         "concept": "Binary representation"},
        {"prompt": "1 + 1 in binary?", "choices": ["10", "2", "11"], "correct": "10",
         "concept": "Binary arithmetic"},
    ]}


def test_sage_minilms_end_to_end(client):
    # Instructor signs up, creates a course, authors a quiz.
    ih = _auth(client.post("/api/v1/sage/signup", json={
        "full_name": "Dr Lee", "email": "lee@uni.edu", "password": "secret123"}).json())
    c = client.post("/api/v1/sage/courses", headers=ih,
                    json={"name": "CS Architecture", "subject": "Computing"})
    assert c.status_code == 201, c.text
    course = c.json()
    cid, code = course["id"], course["join_code"]
    assert len(code) == 6 and course["role"] == "instructor"

    q = client.post(f"/api/v1/sage/courses/{cid}/quizzes", headers=ih, json=_quiz_payload())
    assert q.status_code == 201, q.text
    quiz_id = q.json()["id"]

    # Student joins by code, takes the quiz (no correct answers leaked).
    sh = _auth(client.post("/api/v1/sage/guest", json={
        "join_code": code, "full_name": "Sam"}).json())
    take = client.get(f"/api/v1/sage/quizzes/{quiz_id}/take", headers=sh).json()
    assert len(take["questions"]) == 2
    assert all("correct" not in qq for qq in take["questions"])
    qids = [qq["id"] for qq in take["questions"]]

    # Student answers BOTH wrong -> low score -> mastery drops -> remediation generated.
    sub = client.post(f"/api/v1/sage/quizzes/{quiz_id}/submit", headers=sh, json={
        "answers": [{"question_id": qids[0], "choice": "9"},
                    {"question_id": qids[1], "choice": "2"}]})
    assert sub.status_code == 200, sub.text
    res = sub.json()
    assert res["correct"] == 0 and res["total"] == 2
    assert res["remediation_created"] >= 1  # LMS Bridge kicked in automatically

    # The remediation modules are visible via the existing student endpoint.
    mods = client.get("/api/v1/remediation/modules", headers=sh)
    assert mods.status_code == 200 and len(mods.json()) >= 1

    # Instructor grades view shows the student + their open remediation.
    g = client.get(f"/api/v1/sage/courses/{cid}/grades", headers=ih).json()
    assert g["is_instructor"] is True and len(g["rows"]) == 1
    assert g["rows"][0]["open_remediation"] >= 1

    # Students cannot author quizzes or see instructor grades rows.
    assert client.post(f"/api/v1/sage/courses/{cid}/quizzes", headers=sh,
                       json=_quiz_payload()).status_code == 403
    sg = client.get(f"/api/v1/sage/courses/{cid}/grades", headers=sh).json()
    assert sg["is_instructor"] is False and "scores" in sg


def test_sage_join_requires_valid_code(client):
    client.post("/api/v1/sage/signup", json={
        "full_name": "X", "email": "x@uni.edu", "password": "secret123"})
    bad = client.post("/api/v1/sage/guest", json={"join_code": "ZZZZZZ", "full_name": "Nobody"})
    assert bad.status_code == 404
