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


def test_sage_question_types_and_quiz_management(client):
    ih = _auth(client.post("/api/v1/sage/signup", json={
        "full_name": "Dr Q", "email": "q@uni.edu", "password": "secret123"}).json())
    cid = client.post("/api/v1/sage/courses", headers=ih, json={"name": "Types"}).json()["id"]

    # A quiz mixing all four question types.
    q = client.post(f"/api/v1/sage/courses/{cid}/quizzes", headers=ih, json={
        "title": "Mixed", "questions": [
            {"prompt": "Pick one", "qtype": "mcq", "choices": ["a", "b", "c"], "correct": "b",
             "concept": "C1"},
            {"prompt": "2+2=4?", "qtype": "true_false", "correct": "True", "concept": "C2"},
            {"prompt": "Pick all evens", "qtype": "multi", "choices": ["1", "2", "3", "4"],
             "correct": ["2", "4"], "concept": "C3"},
            {"prompt": "Capital of France?", "qtype": "short", "correct": ["Paris", "paris"],
             "concept": "C4"},
        ]})
    assert q.status_code == 201, q.text
    quiz_id = q.json()["id"]

    sh = _auth(client.post("/api/v1/sage/guest", json={
        "join_code": client.get(f"/api/v1/sage/courses/{cid}", headers=ih).json()["join_code"],
        "full_name": "Stu"}).json())
    take = client.get(f"/api/v1/sage/quizzes/{quiz_id}/take", headers=sh).json()
    qs = {x["prompt"]: x for x in take["questions"]}
    assert qs["2+2=4?"]["choices"] == ["True", "False"]
    assert qs["Capital of France?"]["choices"] == []  # short answer: no choices leaked

    # Answer all correctly (multi via `choices`, short via `choice`, case-insensitive).
    ans = []
    for x in take["questions"]:
        if x["qtype"] == "multi":
            ans.append({"question_id": x["id"], "choices": ["4", "2"]})
        elif x["prompt"].startswith("Capital"):
            ans.append({"question_id": x["id"], "choice": "PARIS"})
        elif x["prompt"].startswith("2+2"):
            ans.append({"question_id": x["id"], "choice": "True"})
        else:
            ans.append({"question_id": x["id"], "choice": "b"})
    res = client.post(f"/api/v1/sage/quizzes/{quiz_id}/submit", headers=sh, json={"answers": ans})
    assert res.json()["correct"] == 4 and res.json()["total"] == 4

    # Edit, duplicate, delete (instructor only).
    ed = client.put(f"/api/v1/sage/quizzes/{quiz_id}", headers=ih, json={
        "title": "Mixed v2", "questions": [
            {"prompt": "T or F?", "qtype": "true_false", "correct": "False", "concept": "C2"}]})
    assert ed.status_code == 200 and ed.json()["question_count"] == 1
    dup = client.post(f"/api/v1/sage/quizzes/{quiz_id}/duplicate", headers=ih)
    assert dup.status_code == 201 and dup.json()["title"].endswith("(copy)")
    assert client.post(f"/api/v1/sage/quizzes/{quiz_id}/duplicate", headers=sh).status_code == 403
    assert client.delete(f"/api/v1/sage/quizzes/{dup.json()['id']}", headers=ih).status_code == 204


def test_sage_announcements_and_due_dates(client):
    ih = _auth(client.post("/api/v1/sage/signup", json={
        "full_name": "Dr A", "email": "a2@uni.edu", "password": "secret123"}).json())
    cid = client.post("/api/v1/sage/courses", headers=ih, json={"name": "Course"}).json()["id"]

    ann = client.post(f"/api/v1/sage/courses/{cid}/announcements", headers=ih,
                      json={"title": "Welcome", "body": "Read chapter 1"})
    assert ann.status_code == 201

    qz = client.post(f"/api/v1/sage/courses/{cid}/quizzes", headers=ih, json={
        "title": "Q1", "due_at": "2026-12-01T23:59:00Z",
        "questions": [{"prompt": "x?", "qtype": "mcq", "choices": ["a", "b"], "correct": "a",
                       "concept": "C"}]})
    assert qz.status_code == 201
    lst = client.get(f"/api/v1/sage/courses/{cid}/quizzes", headers=ih).json()
    assert lst[0]["due_at"] is not None

    sh = _auth(client.post("/api/v1/sage/guest", json={
        "join_code": client.get(f"/api/v1/sage/courses/{cid}", headers=ih).json()["join_code"],
        "full_name": "Stu"}).json())
    anns = client.get(f"/api/v1/sage/courses/{cid}/announcements", headers=sh).json()
    assert len(anns) == 1 and anns[0]["title"] == "Welcome"
    # Students can't post or delete announcements.
    assert client.post(f"/api/v1/sage/courses/{cid}/announcements", headers=sh,
                       json={"title": "x", "body": ""}).status_code == 403
    assert client.delete(f"/api/v1/sage/announcements/{ann.json()['id']}",
                         headers=ih).status_code == 204


def test_sage_student_drilldown_and_csv(client):
    ih = _auth(client.post("/api/v1/sage/signup", json={
        "full_name": "Dr D", "email": "d@uni.edu", "password": "secret123"}).json())
    course = client.post("/api/v1/sage/courses", headers=ih, json={"name": "C"}).json()
    cid, code = course["id"], course["join_code"]
    quiz = client.post(f"/api/v1/sage/courses/{cid}/quizzes", headers=ih,
                       json=_quiz_payload()).json()
    g = client.post("/api/v1/sage/guest", json={"join_code": code, "full_name": "Sam"}).json()
    sh = _auth(g)
    sid = g["user_id"]
    take = client.get(f"/api/v1/sage/quizzes/{quiz['id']}/take", headers=sh).json()
    qids = [q["id"] for q in take["questions"]]
    client.post(f"/api/v1/sage/quizzes/{quiz['id']}/submit", headers=sh, json={
        "answers": [{"question_id": qids[0], "choice": "9"},
                    {"question_id": qids[1], "choice": "2"}]})

    drill = client.get(f"/api/v1/sage/courses/{cid}/students/{sid}", headers=ih)
    assert drill.status_code == 200, drill.text
    body = drill.json()
    assert body["full_name"] == "Sam" and body["quizzes"][0]["attempts"] >= 1
    assert len(body["remediation"]) >= 1  # failed -> remediation listed

    csv = client.get(f"/api/v1/sage/courses/{cid}/grades.csv", headers=ih)
    assert csv.status_code == 200 and "text/csv" in csv.headers["content-type"]
    assert "Student" in csv.text and "Sam" in csv.text

    # Students cannot drill into others or export grades.
    assert client.get(f"/api/v1/sage/courses/{cid}/grades.csv", headers=sh).status_code == 403
    assert client.get(f"/api/v1/sage/courses/{cid}/students/{sid}", headers=sh).status_code == 403


def test_email_is_noop_when_unconfigured():
    from app.services.email_service import email_configured, send_bulk, send_email
    assert email_configured() is False
    assert send_email("x@example.com", "s", "b") is False
    assert send_bulk(["x@example.com", "y@sage.local"], "s", "b") == 0


def test_sage_join_requires_valid_code(client):
    client.post("/api/v1/sage/signup", json={
        "full_name": "X", "email": "x@uni.edu", "password": "secret123"})
    bad = client.post("/api/v1/sage/guest", json={"join_code": "ZZZZZZ", "full_name": "Nobody"})
    assert bad.status_code == 404
