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


def test_sage_profile_syllabus_and_materials(client):
    ih = _auth(client.post("/api/v1/sage/signup", json={
        "full_name": "Dr Ray", "email": "ray@uni.edu", "password": "secret123"}).json())

    # Instructor profile (minimal self-details).
    prof = client.put("/api/v1/sage/me", headers=ih,
                      json={"title": "Professor of CS, NYU", "bio": "I teach systems."})
    assert prof.status_code == 200 and prof.json()["title"] == "Professor of CS, NYU"

    cid = client.post("/api/v1/sage/courses", headers=ih, json={"name": "Systems"}).json()["id"]

    # Syllabus.
    client.put(f"/api/v1/sage/courses/{cid}/syllabus", headers=ih,
               json={"syllabus": "Week 1: binary. Week 2: logic."})
    detail = client.get(f"/api/v1/sage/courses/{cid}", headers=ih).json()
    assert "binary" in detail["syllabus"]
    assert detail["instructor"]["title"] == "Professor of CS, NYU"

    # Materials: a note, a code snippet, and a file.
    note = client.post(f"/api/v1/sage/courses/{cid}/materials/text", headers=ih, json={
        "kind": "note", "title": "Lecture 1 notes", "body": "Two's complement is..."})
    assert note.status_code == 201 and note.json()["kind"] == "note"
    code = client.post(f"/api/v1/sage/courses/{cid}/materials/text", headers=ih, json={
        "kind": "code", "title": "adder.py", "body": "def add(a,b): return a+b",
        "language": "python"})
    assert code.json()["language"] == "python"
    up = client.post(f"/api/v1/sage/courses/{cid}/materials/file", headers=ih,
                     files={"file": ("syllabus.txt", b"hello world", "text/plain")},
                     data={"title": "Handout"})
    assert up.status_code == 201 and up.json()["kind"] == "file"

    mats = client.get(f"/api/v1/sage/courses/{cid}/materials", headers=ih).json()
    assert len(mats) == 3

    # Note body is readable; student (joined) can view materials too.
    body = client.get(f"/api/v1/sage/materials/{note.json()['id']}", headers=ih).json()
    assert "complement" in body["body"]
    code_g = client.get(f"/api/v1/sage/courses/{cid}", headers=ih).json()["join_code"]
    sh = _auth(client.post("/api/v1/sage/guest",
                           json={"join_code": code_g, "full_name": "Su"}).json())
    assert client.get(f"/api/v1/sage/courses/{cid}/materials", headers=sh).status_code == 200
    # Students cannot add materials.
    assert client.post(f"/api/v1/sage/courses/{cid}/materials/text", headers=sh, json={
        "kind": "note", "title": "x", "body": "y"}).status_code == 403


def test_sage_join_requires_valid_code(client):
    client.post("/api/v1/sage/signup", json={
        "full_name": "X", "email": "x@uni.edu", "password": "secret123"})
    bad = client.post("/api/v1/sage/guest", json={"join_code": "ZZZZZZ", "full_name": "Nobody"})
    assert bad.status_code == 404
