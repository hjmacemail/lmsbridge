"""Sage Q&A board: signup, join, post -> AI reply, answers, endorse, insights."""
from __future__ import annotations


def _auth(client, resp_json):
    return {"Authorization": f"Bearer {resp_json['access_token']}"}


def test_sage_end_to_end(client):
    # Instructor signs up and creates a class.
    s = client.post("/api/v1/sage/signup", json={
        "full_name": "Dr Lee", "email": "lee@uni.edu", "password": "secret123"})
    assert s.status_code == 201, s.text
    ih = _auth(client, s.json())
    assert s.json()["role"] == "instructor"

    c = client.post("/api/v1/sage/classes", headers=ih,
                    json={"name": "CS 201", "subject": "Data Structures"})
    assert c.status_code == 201, c.text
    cls = c.json()
    code = cls["join_code"]
    cid = cls["id"]
    assert cls["role"] == "instructor" and len(code) == 6

    # Student joins by code (guest, name only).
    g = client.post("/api/v1/sage/guest", json={"join_code": code, "full_name": "Sam"})
    assert g.status_code == 201, g.text
    sh = _auth(client, g.json())

    # Student posts a question -> Sage auto-replies (AI) with a misconception flag.
    p = client.post(f"/api/v1/sage/classes/{cid}/posts", headers=sh, json={
        "title": "Why is my BST insert wrong?", "body": "It overwrites the root every time.",
        "tags": "trees,bst", "anonymous": True})
    assert p.status_code == 201, p.text
    post = p.json()
    pid = post["id"]
    assert any(a["is_ai"] for a in post["answers"])  # Sage answered
    # Anonymous: student viewer sees "Anonymous" as author.
    assert post["author"] == "Anonymous"

    # Instructor view of the same post sees the real (flagged) author + misconception field.
    pi = client.get(f"/api/v1/sage/posts/{pid}", headers=ih).json()
    assert "anonymous" in pi["author"].lower()
    assert "ai_misconception" in pi

    # Instructor answers and endorses their own answer.
    a = client.post(f"/api/v1/sage/posts/{pid}/answers", headers=ih,
                    json={"body": "Check what your function returns on the empty case."})
    ans = a.json()["answers"]
    instr_ans = [x for x in ans if x["is_instructor"]][0]
    assert instr_ans["author"].endswith("(instructor)")
    e = client.post(f"/api/v1/sage/answers/{instr_ans['id']}/endorse", headers=ih)
    assert e.json()["endorsed"] is True

    # A non-instructor cannot endorse.
    no = client.post(f"/api/v1/sage/answers/{instr_ans['id']}/endorse", headers=sh)
    assert no.status_code == 403

    # Insights (instructor only) reflect the activity.
    ins = client.get(f"/api/v1/sage/classes/{cid}/insights", headers=ih)
    assert ins.status_code == 200, ins.text
    body = ins.json()
    assert body["total_posts"] == 1 and body["members"] == 2
    assert {"tag": "trees", "count": 1} in body["top_tags"]
    # Students may not see insights.
    assert client.get(f"/api/v1/sage/classes/{cid}/insights", headers=sh).status_code == 403


def test_sage_join_requires_valid_code(client):
    client.post("/api/v1/sage/signup", json={
        "full_name": "X", "email": "x@uni.edu", "password": "secret123"})
    bad = client.post("/api/v1/sage/guest", json={"join_code": "ZZZZZZ", "full_name": "Nobody"})
    assert bad.status_code == 404
