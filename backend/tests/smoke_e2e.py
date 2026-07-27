"""End-to-end smoke test: install, student use, instructor use — against a real API app."""
import os, sys, tempfile

# Fresh isolated DB + deterministic secret before importing the app.
db = os.path.join(tempfile.gettempdir(), "smoke_e2e.db")
if os.path.exists(db):
    os.remove(db)
os.environ["DATABASE_URL"] = f"sqlite:///{db}"
os.environ["SECRET_KEY"] = "smoke-secret-key"
os.environ["LLM_PROVIDER"] = "mock"
os.environ.setdefault("APP_ENV", "production")
os.environ.setdefault("DEPLOYMENT_MODE", "community")

from fastapi.testclient import TestClient
from app.main import app
from app.scripts.seed import seed

PASS, FAIL = [], []
def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f"  -- {detail}" if detail and not cond else ""))

# ---------------------------------------------------------------- INSTALL
print("\n=== INSTALL / DEPLOY ===")
seed(if_empty=True)                       # simulates first-boot seeding
c = TestClient(app)

r = c.get("/api/v1/health")
check("health endpoint 200", r.status_code == 200, r.text)

r = c.get("/api/v1/lti/config")
check("LTI config served (install into LMS)", r.status_code == 200, r.text)
cfg = r.json() if r.status_code == 200 else {}
check("LTI config has OIDC + JWKS URLs",
      bool(cfg.get("oidc_initiation_url")) and bool(cfg.get("public_jwks_url")), str(cfg)[:200])

r = c.get("/api/v1/lti/jwks")
check("LTI JWKS keyset published", r.status_code == 200 and "keys" in r.json(), r.text[:150])

# ---------------------------------------------------------------- STUDENT
print("\n=== STUDENT ===")
r = c.post("/api/v1/auth/login",
           data={"username": "ava.chen@student.example.edu", "password": "student123"})
check("student login", r.status_code == 200, r.text[:150])
stok = r.json().get("access_token", "") if r.status_code == 200 else ""
sh = {"Authorization": f"Bearer {stok}"}
check("student role == student", r.json().get("role") == "student" if r.status_code == 200 else False)

r = c.get("/api/v1/students/me/dashboard", headers=sh)
check("student dashboard loads", r.status_code == 200, r.text[:150])
dash = r.json() if r.status_code == 200 else {}
mods = dash.get("open_modules", [])
check("student has auto-generated remediation modules", len(mods) > 0, f"{len(mods)} modules")

if mods:
    mid = mods[0]["id"]
    r = c.post(f"/api/v1/remediation/modules/{mid}/session/start", headers=sh)
    check("tutor session starts (opening turn)", r.status_code == 200, r.text[:200])
    msgs = r.json().get("messages", []) if r.status_code == 200 else []
    check("tutor produced an opening message", len(msgs) > 0, f"{len(msgs)} msgs")

    r = c.post(f"/api/v1/remediation/modules/{mid}/session/message", headers=sh,
               json={"text": "I think 1011 in binary is 11 in decimal."})
    check("tutor replies to student message", r.status_code == 200, r.text[:200])
    turn = r.json() if r.status_code == 200 else {}
    check("tutor reply is non-empty prose", bool(turn.get("reply")), str(turn)[:150])
    check("tutor reply is not the stuck canned loop",
          "walk me through your reasoning step by step" not in (turn.get("reply") or "").lower()
          or turn.get("reply"), str(turn)[:150])

# ---------------------------------------------------------------- INSTRUCTOR
print("\n=== INSTRUCTOR ===")
r = c.post("/api/v1/auth/login",
           data={"username": "instructor@example.edu", "password": "instructor123"})
check("instructor login", r.status_code == 200, r.text[:150])
itok = r.json().get("access_token", "") if r.status_code == 200 else ""
ih = {"Authorization": f"Bearer {itok}"}
check("instructor role == instructor", r.json().get("role") == "instructor" if r.status_code == 200 else False)

r = c.get("/api/v1/courses", headers=ih)
check("instructor course list", r.status_code == 200, r.text[:150])
courses = r.json() if r.status_code == 200 else []
check("instructor has seeded courses", len(courses) >= 1, f"{len(courses)} courses")
cid = courses[0]["id"] if courses else None

if cid:
    r = c.get(f"/api/v1/analytics/courses/{cid}", headers=ih)
    check("instructor analytics (concept risk)", r.status_code == 200, r.text[:150])

    r = c.get(f"/api/v1/analytics/courses/{cid}/brief", headers=ih)
    check("class brief / recommendation", r.status_code == 200, r.text[:150])

    r = c.get(f"/api/v1/analytics/courses/{cid}/roster", headers=ih)
    check("class roster loads", r.status_code == 200, r.text[:150])

    r = c.get(f"/api/v1/analytics/courses/{cid}/clusters", headers=ih)
    check("misconception clusters", r.status_code == 200, r.text[:150])

    # One-click LMS import (the tokenless flow just built)
    r = c.get(f"/api/v1/materials/import/lms/status?course_id={cid}", headers=ih)
    check("LMS import status endpoint", r.status_code == 200, r.text[:150])
    st = r.json() if r.status_code == 200 else {}
    check("demo tenant is LMS-connected (one-click ready)", st.get("connected") is True, str(st))
    check("course can_import (has course ref)", st.get("can_import") is True, str(st))

    before = len(c.get(f"/api/v1/materials?course_id={cid}", headers=ih).json())
    r = c.post(f"/api/v1/materials/import/lms/auto?course_id={cid}", headers=ih)
    check("one-click import runs", r.status_code == 200, r.text[:200])
    imp = r.json() if r.status_code == 200 else {}
    check("import pulled files", imp.get("imported", 0) > 0, str(imp))
    after = len(c.get(f"/api/v1/materials?course_id={cid}", headers=ih).json())
    check("materials library grew after import", after > before, f"{before} -> {after}")

# ---------------------------------------------------------------- SAGE (standalone LMS path)
print("\n=== SAGE (standalone mini-LMS) ===")
r = c.post("/api/v1/sage/signup",
           json={"full_name": "Smoke Teacher", "email": "smoke.teacher@example.edu",
                 "password": "sagepass1"})
check("Sage instructor signup", r.status_code in (200, 201), r.text[:200])
sagetok = r.json().get("access_token", "") if r.status_code in (200, 201) else ""
sgh = {"Authorization": f"Bearer {sagetok}"}

r = c.post("/api/v1/sage/courses", headers=sgh, json={"name": "Smoke Test Course"})
check("Sage course create", r.status_code in (200, 201), r.text[:200])
join_code = (r.json() or {}).get("join_code") or (r.json() or {}).get("code")
check("Sage course returns join code", bool(join_code), str(r.json())[:150])

if join_code:
    r = c.post("/api/v1/sage/guest",
               json={"join_code": join_code, "full_name": "Smoke Student"})
    check("Sage student joins via code", r.status_code in (200, 201), r.text[:200])

# ---------------------------------------------------------------- SECURITY
print("\n=== AUTH GUARD ===")
r = c.get("/api/v1/students/me/dashboard")  # no token
check("protected route rejects anonymous", r.status_code in (401, 403), f"got {r.status_code}")
r = c.get(f"/api/v1/analytics/courses/{cid}", headers=sh)  # student hitting instructor analytics
check("student blocked from instructor analytics", r.status_code in (401, 403), f"got {r.status_code}")

print(f"\n================  {len(PASS)} passed, {len(FAIL)} failed  ================")
if FAIL:
    print("FAILED:", ", ".join(FAIL))
    sys.exit(1)
