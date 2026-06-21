import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  api, sageApi, saveToken, clearToken, loadToken,
  type SageAuth, type SageCourseSummary, type SageQuizListItem,
  type SageTakeQuiz, type SageSubmitResult, type SageStudent,
  type SageGrades, type SageQuestionDraft,
} from "../api/client";
import type { RemediationModule } from "../types";

const USER_KEY = "sage_user";
const ink = "#3a2d6d";
const wrap: React.CSSProperties = { maxWidth: 900, margin: "0 auto", padding: "0 16px 48px" };

function loadUser(): SageAuth | null {
  const raw = sessionStorage.getItem(USER_KEY);
  return raw ? (JSON.parse(raw) as SageAuth) : null;
}
function persist(a: SageAuth) {
  saveToken({ access_token: a.access_token, token_type: a.token_type,
    role: a.role, user_id: a.user_id, full_name: a.full_name } as Parameters<typeof saveToken>[0]);
  sessionStorage.setItem(USER_KEY, JSON.stringify(a));
}
function Card({ children, style }: { children: React.ReactNode; style?: React.CSSProperties }) {
  return <div style={{ background: "#fff", border: "1px solid #e7e3f5", borderRadius: 14,
    padding: 20, marginBottom: 16, ...style }}>{children}</div>;
}

export default function SageApp() {
  const [user, setUser] = useState<SageAuth | null>(loadUser());
  const [view, setView] = useState<"auth" | "courses" | "course">(
    loadToken() && loadUser() ? "courses" : "auth");
  const [course, setCourse] = useState<SageCourseSummary | null>(null);

  function onAuth(a: SageAuth) { persist(a); setUser(a); setView("courses"); }
  function signOut() { clearToken(); sessionStorage.removeItem(USER_KEY); setUser(null); setView("auth"); }

  return (
    <div style={{ minHeight: "100vh", background: "#faf9ff" }}>
      <header style={{ background: ink, color: "#fff", padding: "14px 0", marginBottom: 24 }}>
        <div style={{ ...wrap, display: "flex", justifyContent: "space-between",
          alignItems: "center", paddingBottom: 0 }}>
          <div style={{ cursor: "pointer", fontWeight: 800, fontSize: 20 }}
            onClick={() => setView(user ? "courses" : "auth")}>
            Sage <span style={{ opacity: 0.7, fontWeight: 400, fontSize: 13 }}>· by LMS Bridge</span>
          </div>
          {user && (
            <div style={{ fontSize: 13, display: "flex", gap: 14, alignItems: "center" }}>
              <span style={{ opacity: 0.85 }}>{user.full_name}</span>
              <button className="btn" style={{ padding: "4px 12px" }} onClick={signOut}>Sign out</button>
            </div>
          )}
        </div>
      </header>
      <div style={wrap}>
        {view === "auth" && <Auth onAuth={onAuth} />}
        {view === "courses" && <Courses onOpen={(c) => { setCourse(c); setView("course"); }} />}
        {view === "course" && course &&
          <CourseView course={course} onBack={() => setView("courses")} />}
      </div>
    </div>
  );
}

// ----------------------------------------------------------------- Auth
function Auth({ onAuth }: { onAuth: (a: SageAuth) => void }) {
  const [mode, setMode] = useState<"signup" | "join" | "login">("signup");
  const [name, setName] = useState(""); const [email, setEmail] = useState("");
  const [pw, setPw] = useState(""); const [code, setCode] = useState("");
  const [err, setErr] = useState<string | null>(null); const [busy, setBusy] = useState(false);

  async function go(e: React.FormEvent) {
    e.preventDefault(); setBusy(true); setErr(null);
    try {
      if (mode === "signup") onAuth(await sageApi.signup(name, email, pw));
      else if (mode === "login") {
        const t = await sageApi.login(email, pw);
        onAuth({ access_token: t.access_token, token_type: t.token_type,
          user_id: 0, full_name: email, role: "instructor" });
      } else onAuth(await sageApi.guestJoin(code.trim().toUpperCase(), name));
    } catch (e) { setErr((e as Error).message); } finally { setBusy(false); }
  }
  const tab = (m: typeof mode, label: string) => (
    <button onClick={() => { setMode(m); setErr(null); }} style={{ flex: 1, padding: "8px 0",
      border: "none", cursor: "pointer", background: mode === m ? ink : "transparent",
      color: mode === m ? "#fff" : ink, borderRadius: 8, fontWeight: 600, fontSize: 14 }}>{label}</button>
  );
  return (
    <div style={{ maxWidth: 440, margin: "24px auto" }}>
      <h1 style={{ textAlign: "center", color: ink, marginBottom: 6 }}>Welcome to Sage</h1>
      <p style={{ textAlign: "center", color: "#6b6585", marginTop: 0, fontSize: 14 }}>
        Your own mini class platform — create a course, add quizzes, and let LMS Bridge guide
        students through what they miss. No LMS required.
      </p>
      <Card>
        <div style={{ display: "flex", gap: 6, marginBottom: 16, background: "#f1eefb",
          padding: 4, borderRadius: 10 }}>
          {tab("signup", "Teach")}{tab("join", "Join a course")}{tab("login", "Log in")}
        </div>
        <form onSubmit={go} className="stack" style={{ gap: 10 }}>
          {mode === "join" && <input placeholder="Course join code" value={code}
            onChange={(e) => setCode(e.target.value)} />}
          {mode !== "login" && <input placeholder="Your name" value={name}
            onChange={(e) => setName(e.target.value)} />}
          {mode !== "join" && <input placeholder="Email" type="email" value={email}
            onChange={(e) => setEmail(e.target.value)} />}
          {mode !== "join" && <input placeholder="Password" type="password" value={pw}
            onChange={(e) => setPw(e.target.value)} />}
          <button className="btn" disabled={busy} style={{ background: ink, color: "#fff" }}>
            {busy ? "…" : mode === "signup" ? "Create instructor account"
              : mode === "login" ? "Log in" : "Join course"}
          </button>
          {err && <div className="error">{err}</div>}
        </form>
      </Card>
    </div>
  );
}

// ----------------------------------------------------------------- Courses
function Courses({ onOpen }: { onOpen: (c: SageCourseSummary) => void }) {
  const [courses, setCourses] = useState<SageCourseSummary[]>([]);
  const [name, setName] = useState(""); const [subject, setSubject] = useState("");
  const [code, setCode] = useState(""); const [msg, setMsg] = useState<string | null>(null);
  const load = () => sageApi.courses().then(setCourses).catch(() => setCourses([]));
  useEffect(() => { load(); }, []);

  async function create(e: React.FormEvent) {
    e.preventDefault(); if (!name) return;
    try { await sageApi.createCourse(name, subject); setName(""); setSubject(""); load(); }
    catch (e) { setMsg((e as Error).message); }
  }
  async function join(e: React.FormEvent) {
    e.preventDefault(); if (!code) return;
    try { await sageApi.joinExisting(code.trim().toUpperCase()); setCode(""); load(); }
    catch (e) { setMsg((e as Error).message); }
  }
  return (
    <div>
      <h2 style={{ color: ink }}>Your courses</h2>
      {courses.length === 0 && <p style={{ color: "#6b6585" }}>No courses yet — create one or join with a code.</p>}
      {courses.map((c) => (
        <Card key={c.id} style={{ cursor: "pointer" }}>
          <div onClick={() => onOpen(c)} style={{ display: "flex", justifyContent: "space-between" }}>
            <div>
              <div style={{ fontWeight: 700, fontSize: 16 }}>{c.name}</div>
              <div style={{ color: "#6b6585", fontSize: 13 }}>
                {c.student_count} students · {c.quiz_count} quizzes
                {c.role === "instructor" && <> · join code <b>{c.join_code}</b></>}
              </div>
            </div>
            <span className="pill" style={{ background: "#f1eefb", color: ink }}>{c.role}</span>
          </div>
        </Card>
      ))}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginTop: 8 }}>
        <Card>
          <h3 style={{ marginTop: 0 }}>Create a course</h3>
          <form onSubmit={create} className="stack" style={{ gap: 8 }}>
            <input placeholder="Course name" value={name} onChange={(e) => setName(e.target.value)} />
            <input placeholder="Subject (optional)" value={subject}
              onChange={(e) => setSubject(e.target.value)} />
            <button className="btn" style={{ background: ink, color: "#fff" }}>Create</button>
          </form>
        </Card>
        <Card>
          <h3 style={{ marginTop: 0 }}>Join a course</h3>
          <form onSubmit={join} className="stack" style={{ gap: 8 }}>
            <input placeholder="Join code" value={code} onChange={(e) => setCode(e.target.value)} />
            <button className="btn">Join</button>
          </form>
        </Card>
      </div>
      {msg && <div className="error">{msg}</div>}
    </div>
  );
}

// ----------------------------------------------------------------- Course shell
function CourseView({ course, onBack }: { course: SageCourseSummary; onBack: () => void }) {
  const instr = course.role === "instructor";
  const tabs = instr ? ["Home", "Quizzes", "Students", "Grades"]
    : ["Home", "Quizzes", "Grades", "Needs review"];
  const [tab, setTab] = useState("Home");
  return (
    <div>
      <button className="btn" style={{ padding: "4px 10px", marginBottom: 12 }} onClick={onBack}>← Courses</button>
      <h2 style={{ color: ink, marginBottom: 4 }}>{course.name}</h2>
      <div style={{ display: "flex", gap: 4, borderBottom: "2px solid #ece8fb", marginBottom: 18 }}>
        {tabs.map((t) => (
          <button key={t} onClick={() => setTab(t)} style={{ border: "none", background: "none",
            cursor: "pointer", padding: "8px 14px", fontSize: 14, fontWeight: tab === t ? 700 : 500,
            color: tab === t ? ink : "#6b6585",
            borderBottom: tab === t ? `2px solid ${ink}` : "2px solid transparent",
            marginBottom: -2 }}>{t}</button>
        ))}
      </div>
      {tab === "Home" && <Home course={course} instr={instr} />}
      {tab === "Quizzes" && (instr ? <QuizzesInstructor course={course} />
        : <QuizzesStudent course={course} />)}
      {tab === "Students" && <Students course={course} />}
      {tab === "Grades" && <GradesTab course={course} />}
      {tab === "Needs review" && <NeedsReview course={course} />}
    </div>
  );
}

function Home({ course, instr }: { course: SageCourseSummary; instr: boolean }) {
  return (
    <Card>
      <h3 style={{ marginTop: 0 }}>Welcome to {course.name}</h3>
      {instr ? (
        <p style={{ color: "#444" }}>
          Share the join code <b style={{ color: ink }}>{course.join_code}</b> with your students.
          Add quizzes under the Quizzes tab — when a student misses a concept, LMS Bridge
          automatically builds a guided practice session for them.
        </p>
      ) : (
        <p style={{ color: "#444" }}>
          Take the quizzes under the Quizzes tab. If you slip on something, you'll find a guided
          practice session waiting under <b>Needs review</b>.
        </p>
      )}
    </Card>
  );
}

// ----------------------------------------------------------------- Quizzes (instructor)
function QuizzesInstructor({ course }: { course: SageCourseSummary }) {
  const [quizzes, setQuizzes] = useState<SageQuizListItem[]>([]);
  const [build, setBuild] = useState(false);
  const load = () => sageApi.quizzes(course.id).then(setQuizzes).catch(() => setQuizzes([]));
  useEffect(() => { load(); }, [course.id]);
  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12 }}>
        <h3 style={{ margin: 0 }}>Quizzes</h3>
        <button className="btn" style={{ background: ink, color: "#fff" }}
          onClick={() => setBuild((b) => !b)}>{build ? "Cancel" : "New quiz"}</button>
      </div>
      {build && <QuizBuilder courseId={course.id} onDone={() => { setBuild(false); load(); }} />}
      {quizzes.length === 0 && !build && <p style={{ color: "#6b6585" }}>No quizzes yet.</p>}
      {quizzes.map((q) => (
        <Card key={q.id}>
          <div style={{ display: "flex", justifyContent: "space-between" }}>
            <b>{q.title}</b>
            <span style={{ color: "#6b6585", fontSize: 13 }}>
              {q.question_count} questions · {q.submission_count ?? 0} submissions
            </span>
          </div>
        </Card>
      ))}
    </div>
  );
}

function QuizBuilder({ courseId, onDone }: { courseId: number; onDone: () => void }) {
  const blank = (): SageQuestionDraft => ({ prompt: "", choices: ["", ""], correct: "", concept: "" });
  const [title, setTitle] = useState("");
  const [qs, setQs] = useState<SageQuestionDraft[]>([blank()]);
  const [err, setErr] = useState<string | null>(null); const [busy, setBusy] = useState(false);

  function upd(i: number, patch: Partial<SageQuestionDraft>) {
    setQs((arr) => arr.map((q, j) => j === i ? { ...q, ...patch } : q));
  }
  function setChoice(i: number, c: number, v: string) {
    setQs((arr) => arr.map((q, j) => j === i
      ? { ...q, choices: q.choices.map((x, k) => k === c ? v : x) } : q));
  }
  async function save() {
    setErr(null);
    if (!title.trim()) { setErr("Add a quiz title."); return; }
    for (const q of qs) {
      const choices = q.choices.map((c) => c.trim()).filter(Boolean);
      if (!q.prompt.trim() || choices.length < 2 || !q.correct || !q.concept.trim()) {
        setErr("Each question needs a prompt, 2+ choices, a correct answer, and a concept."); return;
      }
    }
    setBusy(true);
    try {
      await sageApi.createQuiz(courseId, title, qs.map((q) => ({
        ...q, choices: q.choices.map((c) => c.trim()).filter(Boolean) })));
      onDone();
    } catch (e) { setErr((e as Error).message); } finally { setBusy(false); }
  }
  return (
    <Card style={{ background: "#f7f5ff" }}>
      <input placeholder="Quiz title" value={title} onChange={(e) => setTitle(e.target.value)}
        style={{ marginBottom: 12 }} />
      {qs.map((q, i) => (
        <div key={i} style={{ borderTop: "1px solid #ece8fb", paddingTop: 12, marginBottom: 8 }}>
          <input placeholder={`Question ${i + 1}`} value={q.prompt}
            onChange={(e) => upd(i, { prompt: e.target.value })} style={{ marginBottom: 6 }} />
          {q.choices.map((c, ci) => (
            <div key={ci} style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 4 }}>
              <input type="radio" name={`correct-${i}`} checked={q.correct === c && !!c}
                onChange={() => upd(i, { correct: c })} title="Mark correct" />
              <input placeholder={`Choice ${ci + 1}`} value={c}
                onChange={(e) => setChoice(i, ci, e.target.value)} style={{ flex: 1 }} />
            </div>
          ))}
          <div style={{ display: "flex", gap: 8, marginTop: 6 }}>
            <button className="btn" style={{ padding: "2px 10px", fontSize: 12 }}
              onClick={() => upd(i, { choices: [...q.choices, ""] })}>+ choice</button>
            <input placeholder="Concept (e.g. Binary arithmetic)" value={q.concept}
              onChange={(e) => upd(i, { concept: e.target.value })} style={{ flex: 1 }} />
          </div>
        </div>
      ))}
      <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
        <button className="btn" onClick={() => setQs((a) => [...a, blank()])}>+ question</button>
        <button className="btn" style={{ background: ink, color: "#fff" }} disabled={busy}
          onClick={save}>{busy ? "Saving…" : "Save quiz"}</button>
      </div>
      {err && <div className="error">{err}</div>}
    </Card>
  );
}

// ----------------------------------------------------------------- Quizzes (student)
function QuizzesStudent({ course }: { course: SageCourseSummary }) {
  const [quizzes, setQuizzes] = useState<SageQuizListItem[]>([]);
  const [taking, setTaking] = useState<SageTakeQuiz | null>(null);
  const [result, setResult] = useState<SageSubmitResult | null>(null);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const load = () => sageApi.quizzes(course.id).then(setQuizzes).catch(() => setQuizzes([]));
  useEffect(() => { load(); }, [course.id]);

  async function open(id: number) {
    setResult(null); setAnswers({});
    setTaking(await sageApi.takeQuiz(id));
  }
  async function submit() {
    if (!taking) return;
    const payload = taking.questions.map((q) => ({ question_id: q.id, choice: answers[q.id] || "" }));
    setResult(await sageApi.submitQuiz(taking.id, payload));
    load();
  }

  if (taking && result) {
    return (
      <Card>
        <h3 style={{ marginTop: 0 }}>{taking.title} — {Math.round(result.score * 100)}%</h3>
        <p style={{ color: "#444" }}>You got {result.correct} of {result.total} correct.
          {result.remediation_created > 0 &&
            <b style={{ color: "#b4530c" }}> A guided practice session was created — see “Needs review”.</b>}
        </p>
        {taking.questions.map((q) => {
          const r = result.review.find((x) => x.question_id === q.id);
          return (
            <div key={q.id} style={{ padding: "6px 0", borderTop: "1px solid #f0eef8" }}>
              <div style={{ fontWeight: 600, fontSize: 14 }}>
                {r?.is_correct ? "✓ " : "✗ "}{q.prompt}
              </div>
              {!r?.is_correct && <div style={{ fontSize: 13, color: "#6b6585" }}>
                Correct answer: {r?.correct}</div>}
            </div>
          );
        })}
        <button className="btn" style={{ marginTop: 12 }} onClick={() => setTaking(null)}>Back to quizzes</button>
      </Card>
    );
  }
  if (taking) {
    return (
      <Card>
        <h3 style={{ marginTop: 0 }}>{taking.title}</h3>
        {taking.questions.map((q, i) => (
          <div key={q.id} style={{ padding: "8px 0", borderTop: "1px solid #f0eef8" }}>
            <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 6 }}>{i + 1}. {q.prompt}</div>
            {q.choices.map((c) => (
              <label key={c} style={{ display: "flex", gap: 8, fontSize: 14, padding: "2px 0" }}>
                <input type="radio" name={`q-${q.id}`} checked={answers[q.id] === c}
                  onChange={() => setAnswers((a) => ({ ...a, [q.id]: c }))} />{c}
              </label>
            ))}
          </div>
        ))}
        <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
          <button className="btn" onClick={() => setTaking(null)}>Cancel</button>
          <button className="btn" style={{ background: ink, color: "#fff" }} onClick={submit}>Submit</button>
        </div>
      </Card>
    );
  }
  return (
    <div>
      <h3>Quizzes</h3>
      {quizzes.length === 0 && <p style={{ color: "#6b6585" }}>No quizzes yet.</p>}
      {quizzes.map((q) => (
        <Card key={q.id}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <b>{q.title}</b>
              <div style={{ color: "#6b6585", fontSize: 13 }}>
                {q.question_count} questions
                {q.my_score != null && ` · last score ${Math.round(q.my_score * 100)}%`}
              </div>
            </div>
            <button className="btn" style={{ background: ink, color: "#fff" }}
              onClick={() => open(q.id)}>{q.my_score != null ? "Retake" : "Take quiz"}</button>
          </div>
        </Card>
      ))}
    </div>
  );
}

// ----------------------------------------------------------------- Students
function Students({ course }: { course: SageCourseSummary }) {
  const [students, setStudents] = useState<SageStudent[]>([]);
  useEffect(() => { sageApi.students(course.id).then(setStudents).catch(() => setStudents([])); }, [course.id]);
  return (
    <Card>
      <h3 style={{ marginTop: 0 }}>Students ({students.length})</h3>
      <p style={{ color: "#6b6585", fontSize: 13 }}>Share join code <b style={{ color: ink }}>{course.join_code}</b>.</p>
      {students.length === 0 && <p style={{ color: "#6b6585" }}>No students yet.</p>}
      {students.map((s) => (
        <div key={s.id} style={{ padding: "6px 0", borderTop: "1px solid #f0eef8" }}>
          <b>{s.full_name}</b> <span style={{ color: "#6b6585", fontSize: 13 }}>{s.email}</span>
        </div>
      ))}
    </Card>
  );
}

// ----------------------------------------------------------------- Grades
function GradesTab({ course }: { course: SageCourseSummary }) {
  const [g, setG] = useState<SageGrades | null>(null);
  useEffect(() => { sageApi.grades(course.id).then(setG).catch(() => setG(null)); }, [course.id]);
  if (!g) return <p>Loading…</p>;
  const pct = (v?: number) => v == null ? "—" : `${Math.round(v * 100)}%`;
  if (g.is_instructor) {
    return (
      <Card>
        <h3 style={{ marginTop: 0 }}>Grades</h3>
        <table style={{ width: "100%", fontSize: 13 }}>
          <thead><tr style={{ textAlign: "left", color: "#6b6585" }}>
            <th>Student</th>{g.quizzes.map((q) => <th key={q.id}>{q.title}</th>)}<th>Needs review</th>
          </tr></thead>
          <tbody>
            {(g.rows || []).map((r) => (
              <tr key={r.student_id} style={{ borderTop: "1px solid #f0eef8" }}>
                <td style={{ fontWeight: 600 }}>{r.full_name}</td>
                {g.quizzes.map((q) => <td key={q.id}>{pct(r.scores[String(q.id)])}</td>)}
                <td>{r.open_remediation > 0
                  ? <b style={{ color: "#b4530c" }}>{r.open_remediation}</b> : "0"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {(g.rows || []).length === 0 && <p style={{ color: "#6b6585" }}>No students yet.</p>}
      </Card>
    );
  }
  return (
    <Card>
      <h3 style={{ marginTop: 0 }}>My grades</h3>
      {g.quizzes.length === 0 && <p style={{ color: "#6b6585" }}>No quizzes yet.</p>}
      {g.quizzes.map((q) => (
        <div key={q.id} style={{ display: "flex", justifyContent: "space-between",
          padding: "6px 0", borderTop: "1px solid #f0eef8" }}>
          <span>{q.title}</span><b>{pct(g.scores?.[String(q.id)])}</b>
        </div>
      ))}
      {(g.open_remediation || 0) > 0 && <p style={{ color: "#b4530c", marginTop: 12 }}>
        You have {g.open_remediation} guided practice session(s) under “Needs review”.</p>}
    </Card>
  );
}

// ----------------------------------------------------------------- Needs review (student)
function NeedsReview({ course }: { course: SageCourseSummary }) {
  const [mods, setMods] = useState<RemediationModule[]>([]);
  const nav = useNavigate();
  useEffect(() => {
    api.myModules().then((m) => setMods(m.filter((x) => x.course_id === course.id)))
      .catch(() => setMods([]));
  }, [course.id]);
  const open = mods.filter((m) => m.status !== "completed");
  return (
    <div>
      <h3>Needs review</h3>
      {open.length === 0 && <p style={{ color: "#6b6585" }}>
        Nothing to review right now — keep taking quizzes.</p>}
      {open.map((m) => (
        <Card key={m.id}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <b>{m.title}</b>
              {m.rationale && <div style={{ color: "#6b6585", fontSize: 13 }}>{m.rationale}</div>}
            </div>
            <button className="btn" style={{ background: ink, color: "#fff" }}
              onClick={() => nav(`/modules/${m.id}`)}>Start practice</button>
          </div>
        </Card>
      ))}
    </div>
  );
}
