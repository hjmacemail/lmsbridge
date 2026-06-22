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

const C = {
  brand: "#3C3489", primary: "#534AB7", accentBg: "#EEEDFE", accentInk: "#3C3489",
  pageBg: "#faf9ff", line: "#e7e3f5", ink: "#2b2740", muted: "#6b6585",
  success: "#15803d", successBg: "#e9f8ef", danger: "#c0392b", dangerBg: "#fdecea",
  info: "#2563eb", infoBg: "#eaf1fe", soft: "#f5f3fc",
};

function loadUser(): SageAuth | null {
  const raw = sessionStorage.getItem(USER_KEY);
  return raw ? (JSON.parse(raw) as SageAuth) : null;
}
function persist(a: SageAuth) {
  saveToken({ access_token: a.access_token, token_type: a.token_type,
    role: a.role, user_id: a.user_id, full_name: a.full_name } as Parameters<typeof saveToken>[0]);
  sessionStorage.setItem(USER_KEY, JSON.stringify(a));
}
function initials(name: string) {
  return name.trim().split(/\s+/).slice(0, 2).map((w) => w[0]?.toUpperCase() || "").join("") || "?";
}

// --- tiny inline icon set (no external dependency) ---
function Icon({ name, size = 18, color = "currentColor" }: { name: string; size?: number; color?: string }) {
  const p: Record<string, string> = {
    school: "M12 3 1 9l11 6 9-4.9V17h2V9L12 3zM5 13.2V17l7 3.8 7-3.8v-3.8l-7 3.8-7-3.8z",
    key: "M21 10h-8.35A5.99 5.99 0 0 0 7 6a6 6 0 1 0 0 12 5.99 5.99 0 0 0 5.65-4H13l2 2 2-2 2 2 3-3-2-3zM7 14a2 2 0 1 1 0-4 2 2 0 0 1 0 4z",
    copy: "M16 1H4a2 2 0 0 0-2 2v12h2V3h12V1zm3 4H8a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h11a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2zm0 16H8V7h11v14z",
    play: "M8 5v14l11-7L8 5z",
    check: "M9 16.2 4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2z",
    circle: "M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm0 18a8 8 0 1 1 0-16 8 8 0 0 1 0 16z",
    alert: "M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z",
    plus: "M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z",
    spark: "M12 2l1.9 5.1L19 9l-5.1 1.9L12 16l-1.9-5.1L5 9l5.1-1.9L12 2z",
    arrow: "M10 17l5-5-5-5v10z",
    back: "M15 18l-6-6 6-6",
    logout: "M16 17v-2h-6v-2h6V11l3 3-3 3zM4 5h8V3H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h8v-2H4V5z",
  };
  const fillStroke = name === "back" ? { fill: "none", stroke: color, strokeWidth: 2, strokeLinecap: "round" as const, strokeLinejoin: "round" as const } : { fill: color };
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" style={{ flexShrink: 0 }}>
      <path d={p[name]} {...fillStroke} />
    </svg>
  );
}

function Card({ children, style }: { children: React.ReactNode; style?: React.CSSProperties }) {
  return <div style={{ background: "#fff", border: `1px solid ${C.line}`, borderRadius: 14,
    padding: "18px 20px", ...style }}>{children}</div>;
}
function PrimaryBtn({ children, onClick, disabled, type }:
  { children: React.ReactNode; onClick?: () => void; disabled?: boolean; type?: "submit" | "button" }) {
  return <button type={type || "button"} onClick={onClick} disabled={disabled}
    style={{ background: C.primary, color: "#fff", border: "none", borderRadius: 10,
      padding: "10px 18px", fontSize: 14, fontWeight: 600, cursor: disabled ? "default" : "pointer",
      opacity: disabled ? 0.6 : 1, display: "inline-flex", alignItems: "center", gap: 7 }}>{children}</button>;
}
function GhostBtn({ children, onClick }: { children: React.ReactNode; onClick?: () => void }) {
  return <button onClick={onClick} style={{ background: "#fff", color: C.ink, border: `1px solid ${C.line}`,
    borderRadius: 10, padding: "8px 14px", fontSize: 14, cursor: "pointer",
    display: "inline-flex", alignItems: "center", gap: 6 }}>{children}</button>;
}
const inputStyle: React.CSSProperties = { width: "100%", padding: "11px 13px", border: `1px solid ${C.line}`,
  borderRadius: 10, fontSize: 14.5, fontFamily: "inherit", boxSizing: "border-box", background: "#fff" };

export default function SageApp() {
  const [user, setUser] = useState<SageAuth | null>(loadUser());
  const [view, setView] = useState<"auth" | "courses" | "course">(
    loadToken() && loadUser() ? "courses" : "auth");
  const [course, setCourse] = useState<SageCourseSummary | null>(null);

  function onAuth(a: SageAuth) { persist(a); setUser(a); setView("courses"); }
  function signOut() { clearToken(); sessionStorage.removeItem(USER_KEY); setUser(null); setView("auth"); }

  return (
    <div style={{ minHeight: "100vh", background: C.pageBg, color: C.ink }}>
      <header style={{ background: C.brand, color: "#fff", padding: "14px 0" }}>
        <div style={{ maxWidth: 940, margin: "0 auto", padding: "0 16px", display: "flex",
          justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ cursor: "pointer", fontWeight: 800, fontSize: 19, display: "flex", alignItems: "center", gap: 9 }}
            onClick={() => setView(user ? "courses" : "auth")}>
            <Icon name="school" size={22} /> Sage
            <span style={{ opacity: 0.65, fontWeight: 400, fontSize: 12.5 }}>· by LMS Bridge</span>
          </div>
          {user && (
            <div style={{ display: "flex", gap: 12, alignItems: "center", fontSize: 13.5 }}>
              <div style={{ width: 30, height: 30, borderRadius: "50%", background: "#7F77DD",
                display: "flex", alignItems: "center", justifyContent: "center", fontSize: 12, fontWeight: 600 }}>
                {initials(user.full_name)}</div>
              <button onClick={signOut} style={{ background: "rgba(255,255,255,.14)", color: "#fff",
                border: "none", borderRadius: 8, padding: "6px 12px", cursor: "pointer", display: "inline-flex",
                alignItems: "center", gap: 6 }}><Icon name="logout" size={15} /> Sign out</button>
            </div>
          )}
        </div>
      </header>
      <div style={{ maxWidth: 940, margin: "0 auto", padding: "24px 16px 56px" }}>
        {view === "auth" && <Auth onAuth={onAuth} />}
        {view === "courses" && <Courses onOpen={(c) => { setCourse(c); setView("course"); }} />}
        {view === "course" && course &&
          <CourseView course={course} onBack={() => setView("courses")} />}
      </div>
    </div>
  );
}

// --------------------------------------------------------------- Auth
function Auth({ onAuth }: { onAuth: (a: SageAuth) => void }) {
  const [mode, setMode] = useState<"signup" | "join" | "login">("signup");
  const [name, setName] = useState(""); const [email, setEmail] = useState("");
  const [pw, setPw] = useState(""); const [code, setCode] = useState("");
  const [err, setErr] = useState<string | null>(null); const [busy, setBusy] = useState(false);

  async function go(e: React.FormEvent) {
    e.preventDefault(); setErr(null);
    // Friendly client-side checks so the user isn't bounced by a server validation error.
    if (mode === "join" && !code.trim()) { setErr("Enter the course join code."); return; }
    if (mode !== "login" && !name.trim()) { setErr("Please enter your name."); return; }
    if (mode !== "join") {
      if (!email.trim()) { setErr("Enter your email address."); return; }
      if (!pw) { setErr("Enter a password."); return; }
      if (mode === "signup" && pw.length < 6) {
        setErr("Password must be at least 6 characters."); return;
      }
    }
    setBusy(true);
    try {
      if (mode === "signup") onAuth(await sageApi.signup(name.trim(), email.trim(), pw));
      else if (mode === "login") {
        const t = await sageApi.login(email, pw);
        onAuth({ access_token: t.access_token, token_type: t.token_type,
          user_id: 0, full_name: email, role: "instructor" });
      } else onAuth(await sageApi.guestJoin(code.trim().toUpperCase(), name));
    } catch (e) { setErr((e as Error).message); } finally { setBusy(false); }
  }
  const tab = (m: typeof mode, label: string) => (
    <button onClick={() => { setMode(m); setErr(null); }} style={{ flex: 1, padding: "9px 0",
      border: "none", cursor: "pointer", background: mode === m ? C.brand : "transparent",
      color: mode === m ? "#fff" : C.accentInk, borderRadius: 9, fontWeight: 600, fontSize: 14 }}>{label}</button>
  );
  return (
    <div style={{ maxWidth: 440, margin: "16px auto" }}>
      <h1 style={{ textAlign: "center", color: C.brand, marginBottom: 6, fontSize: 28 }}>Welcome to Sage</h1>
      <p style={{ textAlign: "center", color: C.muted, marginTop: 0, fontSize: 14.5, lineHeight: 1.5 }}>
        Your own mini class platform — create a course, add quizzes, and let LMS Bridge guide
        students through what they miss. No LMS needed.
      </p>
      <Card style={{ marginTop: 18 }}>
        <div style={{ display: "flex", gap: 6, marginBottom: 16, background: C.soft, padding: 5, borderRadius: 11 }}>
          {tab("signup", "Teach")}{tab("join", "Join a course")}{tab("login", "Log in")}
        </div>
        <form onSubmit={go} style={{ display: "grid", gap: 10 }}>
          {mode === "join" && <input style={inputStyle} placeholder="Course join code (e.g. 7QK4PD)"
            value={code} onChange={(e) => setCode(e.target.value)} />}
          {mode !== "login" && <input style={inputStyle} placeholder="Your name"
            value={name} onChange={(e) => setName(e.target.value)} />}
          {mode !== "join" && <input style={inputStyle} placeholder="Email" type="email"
            value={email} onChange={(e) => setEmail(e.target.value)} />}
          {mode !== "join" && <input style={inputStyle} placeholder="Password" type="password"
            value={pw} onChange={(e) => setPw(e.target.value)} />}
          <PrimaryBtn type="submit" disabled={busy}>
            {busy ? "…" : mode === "signup" ? "Create instructor account"
              : mode === "login" ? "Log in" : "Join course"}
          </PrimaryBtn>
          {err && <div style={{ color: C.danger, fontSize: 13 }}>{err}</div>}
        </form>
      </Card>
      <p style={{ textAlign: "center", color: C.muted, fontSize: 12.5, marginTop: 14 }}>
        Joining a class? Just pick “Join a course” — no account or email required.
      </p>
    </div>
  );
}

// --------------------------------------------------------------- Courses
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
      <h2 style={{ color: C.brand, fontSize: 22 }}>Your courses</h2>
      {courses.length === 0 && (
        <Card style={{ textAlign: "center", color: C.muted, background: C.soft, border: "none" }}>
          No courses yet — create your first one below, or join one with a code.
        </Card>
      )}
      <div style={{ display: "grid", gap: 12 }}>
        {courses.map((c) => (
          <Card key={c.id} style={{ cursor: "pointer", display: "flex", justifyContent: "space-between",
            alignItems: "center", gap: 12 }}>
            <div onClick={() => onOpen(c)} style={{ flex: 1 }}>
              <div style={{ fontWeight: 700, fontSize: 16.5 }}>{c.name}</div>
              <div style={{ color: C.muted, fontSize: 13, marginTop: 2 }}>
                {c.student_count} students · {c.quiz_count} quizzes
                {c.role === "instructor" && <> · join code <b style={{ color: C.accentInk, letterSpacing: 1 }}>{c.join_code}</b></>}
              </div>
            </div>
            <span style={{ fontSize: 12, fontWeight: 600, background: C.accentBg, color: C.accentInk,
              padding: "4px 11px", borderRadius: 999 }}>{c.role}</span>
            <Icon name="arrow" color={C.muted} />
          </Card>
        ))}
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
        gap: 14, marginTop: 16 }}>
        <Card>
          <h3 style={{ marginTop: 0, fontSize: 16 }}>Create a course</h3>
          <form onSubmit={create} style={{ display: "grid", gap: 9 }}>
            <input style={inputStyle} placeholder="Course name" value={name} onChange={(e) => setName(e.target.value)} />
            <input style={inputStyle} placeholder="Subject (optional)" value={subject}
              onChange={(e) => setSubject(e.target.value)} />
            <PrimaryBtn type="submit"><Icon name="plus" size={16} /> Create course</PrimaryBtn>
          </form>
        </Card>
        <Card>
          <h3 style={{ marginTop: 0, fontSize: 16 }}>Join a course</h3>
          <form onSubmit={join} style={{ display: "grid", gap: 9 }}>
            <input style={inputStyle} placeholder="Join code" value={code} onChange={(e) => setCode(e.target.value)} />
            <GhostBtn><span>Join with code</span></GhostBtn>
          </form>
        </Card>
      </div>
      {msg && <div style={{ color: C.danger, fontSize: 13, marginTop: 10 }}>{msg}</div>}
    </div>
  );
}

// --------------------------------------------------------------- Course shell
function CopyChip({ code }: { code: string | null }) {
  const [done, setDone] = useState(false);
  if (!code) return null;
  return (
    <button onClick={() => { navigator.clipboard?.writeText(code); setDone(true); setTimeout(() => setDone(false), 1500); }}
      style={{ display: "inline-flex", alignItems: "center", gap: 7, background: C.accentBg, color: C.accentInk,
        border: "none", padding: "7px 13px", borderRadius: 999, fontSize: 13, cursor: "pointer" }}>
      <Icon name="key" size={15} /> join code <b style={{ letterSpacing: 1 }}>{code}</b>
      <Icon name={done ? "check" : "copy"} size={15} />{done && <span>copied</span>}
    </button>
  );
}

function CourseView({ course, onBack }: { course: SageCourseSummary; onBack: () => void }) {
  const instr = course.role === "instructor";
  const tabs = instr ? ["Home", "Quizzes", "Students", "Grades"]
    : ["Home", "Quizzes", "Grades", "Needs review"];
  const [tab, setTab] = useState("Home");
  return (
    <div>
      <GhostBtn onClick={onBack}><Icon name="back" size={16} /> Courses</GhostBtn>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between",
        flexWrap: "wrap", gap: 10, margin: "12px 0 4px" }}>
        <h2 style={{ color: C.brand, margin: 0, fontSize: 22 }}>{course.name}</h2>
        {instr && <CopyChip code={course.join_code} />}
      </div>
      <div style={{ display: "flex", gap: 6, borderBottom: `2px solid ${C.line}`, marginBottom: 18,
        overflowX: "auto" }}>
        {tabs.map((t) => (
          <button key={t} onClick={() => setTab(t)} style={{ border: "none", background: "none",
            cursor: "pointer", padding: "9px 14px", fontSize: 14, whiteSpace: "nowrap",
            fontWeight: tab === t ? 700 : 500, color: tab === t ? C.brand : C.muted,
            borderBottom: tab === t ? `2px solid ${C.primary}` : "2px solid transparent", marginBottom: -2 }}>{t}</button>
        ))}
      </div>
      {tab === "Home" && <Home course={course} instr={instr} />}
      {tab === "Quizzes" && (instr ? <QuizzesInstructor course={course} /> : <QuizzesStudent course={course} />)}
      {tab === "Students" && <Students course={course} />}
      {tab === "Grades" && <GradesTab course={course} />}
      {tab === "Needs review" && <NeedsReview course={course} />}
    </div>
  );
}

function Stat({ label, value, tone }: { label: string; value: number; tone?: "danger" }) {
  const danger = tone === "danger" && value > 0;
  return (
    <div style={{ background: danger ? C.dangerBg : C.soft, borderRadius: 12, padding: "14px 16px" }}>
      <div style={{ fontSize: 13, color: danger ? C.danger : C.muted }}>{label}</div>
      <div style={{ fontSize: 26, fontWeight: 700, color: danger ? C.danger : C.ink }}>{value}</div>
    </div>
  );
}

function Home({ course, instr }: { course: SageCourseSummary; instr: boolean }) {
  return (
    <div style={{ display: "grid", gap: 14 }}>
      {instr && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))", gap: 12 }}>
          <Stat label="Students" value={course.student_count} />
          <Stat label="Quizzes" value={course.quiz_count} />
        </div>
      )}
      <Card>
        <h3 style={{ marginTop: 0, fontSize: 17 }}>Welcome to {course.name}</h3>
        {instr ? (
          <p style={{ color: "#444", lineHeight: 1.6, margin: 0 }}>
            Share the join code <b style={{ color: C.accentInk }}>{course.join_code}</b> with your students,
            then add quizzes under the <b>Quizzes</b> tab. When a student misses a concept, LMS Bridge
            automatically builds a guided practice session for them — you'll see who needs help under <b>Grades</b>.
          </p>
        ) : (
          <p style={{ color: "#444", lineHeight: 1.6, margin: 0 }}>
            Take the quizzes under the <b>Quizzes</b> tab. If you slip on something, a short guided
            practice session will be waiting for you under <b>Needs review</b> — no stress, that's how you learn.
          </p>
        )}
      </Card>
    </div>
  );
}

// --------------------------------------------------------------- Quizzes (instructor)
function QuizzesInstructor({ course }: { course: SageCourseSummary }) {
  const [quizzes, setQuizzes] = useState<SageQuizListItem[]>([]);
  const [build, setBuild] = useState(false);
  const load = () => sageApi.quizzes(course.id).then(setQuizzes).catch(() => setQuizzes([]));
  useEffect(() => { load(); }, [course.id]);
  return (
    <div style={{ display: "grid", gap: 12 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h3 style={{ margin: 0, fontSize: 17 }}>Quizzes</h3>
        <PrimaryBtn onClick={() => setBuild((b) => !b)}>
          <Icon name="plus" size={16} /> {build ? "Cancel" : "New quiz"}</PrimaryBtn>
      </div>
      {build && <QuizBuilder courseId={course.id} onDone={() => { setBuild(false); load(); }} />}
      {quizzes.length === 0 && !build && (
        <Card style={{ textAlign: "center", color: C.muted, background: C.soft, border: "none" }}>
          No quizzes yet. Click <b>New quiz</b> to build your first one — add questions, mark the correct
          answer, and tag each with a concept.
        </Card>
      )}
      {quizzes.map((q) => {
        const pct = q.submission_count != null && course.student_count
          ? Math.round((q.submission_count / course.student_count) * 100) : 0;
        return (
          <Card key={q.id}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 10 }}>
              <b style={{ fontSize: 15 }}>{q.title}</b>
              <span style={{ color: C.muted, fontSize: 13 }}>
                {q.question_count} questions · {q.submission_count ?? 0} submitted</span>
            </div>
            <div style={{ height: 7, borderRadius: 999, background: C.soft, marginTop: 10, overflow: "hidden" }}>
              <div style={{ width: `${pct}%`, height: "100%", background: C.primary }} />
            </div>
          </Card>
        );
      })}
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
        setErr("Each question needs a prompt, 2+ choices, a correct answer (the dot), and a concept."); return;
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
    <Card style={{ background: C.soft, border: `1px solid ${C.line}` }}>
      <input style={{ ...inputStyle, marginBottom: 14, fontWeight: 600 }} placeholder="Quiz title (e.g. Binary basics)"
        value={title} onChange={(e) => setTitle(e.target.value)} />
      {qs.map((q, i) => (
        <div key={i} style={{ background: "#fff", border: `1px solid ${C.line}`, borderRadius: 12,
          padding: 14, marginBottom: 10 }}>
          <input style={{ ...inputStyle, marginBottom: 8 }} placeholder={`Question ${i + 1}`}
            value={q.prompt} onChange={(e) => upd(i, { prompt: e.target.value })} />
          <div style={{ fontSize: 12, color: C.muted, marginBottom: 6 }}>Tap the dot to mark the correct answer.</div>
          {q.choices.map((c, ci) => (
            <div key={ci} style={{ display: "flex", gap: 9, alignItems: "center", marginBottom: 6 }}>
              <input type="radio" name={`correct-${i}`} checked={q.correct === c && !!c}
                onChange={() => upd(i, { correct: c })} title="Mark correct" style={{ accentColor: C.primary }} />
              <input style={inputStyle} placeholder={`Choice ${ci + 1}`} value={c}
                onChange={(e) => setChoice(i, ci, e.target.value)} />
            </div>
          ))}
          <div style={{ display: "flex", gap: 8, marginTop: 8, flexWrap: "wrap" }}>
            <GhostBtn onClick={() => upd(i, { choices: [...q.choices, ""] })}>+ choice</GhostBtn>
            <input style={{ ...inputStyle, flex: 1, minWidth: 160 }} placeholder="Concept (e.g. Binary arithmetic)"
              value={q.concept} onChange={(e) => upd(i, { concept: e.target.value })} />
          </div>
        </div>
      ))}
      <div style={{ display: "flex", gap: 8, marginTop: 6, flexWrap: "wrap" }}>
        <GhostBtn onClick={() => setQs((a) => [...a, blank()])}><Icon name="plus" size={15} /> Add question</GhostBtn>
        <PrimaryBtn onClick={save} disabled={busy}>{busy ? "Saving…" : "Save quiz"}</PrimaryBtn>
      </div>
      {err && <div style={{ color: C.danger, fontSize: 13, marginTop: 8 }}>{err}</div>}
    </Card>
  );
}

// --------------------------------------------------------------- Quizzes (student)
function QuizzesStudent({ course }: { course: SageCourseSummary }) {
  const [quizzes, setQuizzes] = useState<SageQuizListItem[]>([]);
  const [taking, setTaking] = useState<SageTakeQuiz | null>(null);
  const [result, setResult] = useState<SageSubmitResult | null>(null);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const load = () => sageApi.quizzes(course.id).then(setQuizzes).catch(() => setQuizzes([]));
  useEffect(() => { load(); }, [course.id]);

  async function open(id: number) { setResult(null); setAnswers({}); setTaking(await sageApi.takeQuiz(id)); }
  async function submit() {
    if (!taking) return;
    const payload = taking.questions.map((q) => ({ question_id: q.id, choice: answers[q.id] || "" }));
    setResult(await sageApi.submitQuiz(taking.id, payload)); load();
  }

  if (taking && result) {
    const pct = Math.round(result.score * 100);
    const good = pct >= 70;
    return (
      <Card>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ width: 56, height: 56, borderRadius: "50%", flexShrink: 0,
            background: good ? C.successBg : C.dangerBg, color: good ? C.success : C.danger,
            display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18, fontWeight: 700 }}>{pct}%</div>
          <div>
            <h3 style={{ margin: 0, fontSize: 17 }}>{taking.title}</h3>
            <div style={{ color: C.muted, fontSize: 14 }}>You got {result.correct} of {result.total} correct.</div>
          </div>
        </div>
        {result.remediation_created > 0 && (
          <div style={{ background: C.infoBg, color: C.info, borderRadius: 10, padding: "10px 14px",
            marginTop: 14, fontSize: 14, display: "flex", alignItems: "center", gap: 8 }}>
            <Icon name="spark" size={18} /> A guided practice session is ready for you under “Needs review”.</div>
        )}
        <div style={{ marginTop: 14 }}>
          {taking.questions.map((q) => {
            const r = result.review.find((x) => x.question_id === q.id);
            return (
              <div key={q.id} style={{ padding: "10px 0", borderTop: `1px solid ${C.line}`,
                display: "flex", gap: 10 }}>
                <Icon name={r?.is_correct ? "check" : "alert"} size={18}
                  color={r?.is_correct ? C.success : C.danger} />
                <div>
                  <div style={{ fontSize: 14, fontWeight: 500 }}>{q.prompt}</div>
                  {!r?.is_correct && <div style={{ fontSize: 13, color: C.muted }}>Correct answer: {r?.correct}</div>}
                </div>
              </div>
            );
          })}
        </div>
        <GhostBtn onClick={() => setTaking(null)}><Icon name="back" size={16} /> Back to quizzes</GhostBtn>
      </Card>
    );
  }
  if (taking) {
    const answered = taking.questions.filter((q) => answers[q.id]).length;
    return (
      <Card>
        <h3 style={{ marginTop: 0, fontSize: 17 }}>{taking.title}</h3>
        <div style={{ fontSize: 13, color: C.muted, marginBottom: 6 }}>{answered} of {taking.questions.length} answered</div>
        {taking.questions.map((q, i) => (
          <div key={q.id} style={{ padding: "12px 0", borderTop: `1px solid ${C.line}` }}>
            <div style={{ fontWeight: 600, fontSize: 14.5, marginBottom: 8 }}>{i + 1}. {q.prompt}</div>
            {q.choices.map((c) => {
              const sel = answers[q.id] === c;
              return (
                <label key={c} style={{ display: "flex", gap: 9, alignItems: "center", fontSize: 14,
                  padding: "9px 12px", marginBottom: 6, borderRadius: 10, cursor: "pointer",
                  border: `1px solid ${sel ? C.primary : C.line}`, background: sel ? C.soft : "#fff" }}>
                  <input type="radio" name={`q-${q.id}`} checked={sel}
                    onChange={() => setAnswers((a) => ({ ...a, [q.id]: c }))} style={{ accentColor: C.primary }} />{c}
                </label>
              );
            })}
          </div>
        ))}
        <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
          <GhostBtn onClick={() => setTaking(null)}>Cancel</GhostBtn>
          <PrimaryBtn onClick={submit}>Submit quiz</PrimaryBtn>
        </div>
      </Card>
    );
  }
  return (
    <div style={{ display: "grid", gap: 12 }}>
      <h3 style={{ margin: 0, fontSize: 17 }}>Quizzes</h3>
      {quizzes.length === 0 && (
        <Card style={{ textAlign: "center", color: C.muted, background: C.soft, border: "none" }}>
          No quizzes yet — check back soon.</Card>
      )}
      {quizzes.map((q) => {
        const taken = q.my_score != null;
        return (
          <Card key={q.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 11 }}>
              <Icon name={taken ? "check" : "circle"} size={22} color={taken ? C.success : "#b9b4cf"} />
              <div>
                <b style={{ fontSize: 15 }}>{q.title}</b>
                <div style={{ color: C.muted, fontSize: 13 }}>
                  {q.question_count} questions
                  {taken && <> · your score <b style={{ color: C.success }}>{Math.round((q.my_score || 0) * 100)}%</b></>}
                </div>
              </div>
            </div>
            <PrimaryBtn onClick={() => open(q.id)}>{taken ? "Retake" : "Take quiz"}</PrimaryBtn>
          </Card>
        );
      })}
    </div>
  );
}

// --------------------------------------------------------------- Students
function Students({ course }: { course: SageCourseSummary }) {
  const [students, setStudents] = useState<SageStudent[]>([]);
  useEffect(() => { sageApi.students(course.id).then(setStudents).catch(() => setStudents([])); }, [course.id]);
  return (
    <Card>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 8 }}>
        <h3 style={{ marginTop: 0, marginBottom: 0, fontSize: 17 }}>Students ({students.length})</h3>
        <CopyChip code={course.join_code} />
      </div>
      <div style={{ marginTop: 8 }}>
        {students.length === 0 && <p style={{ color: C.muted }}>No students yet — share the join code to invite them.</p>}
        {students.map((s) => (
          <div key={s.id} style={{ display: "flex", alignItems: "center", gap: 11,
            padding: "10px 0", borderTop: `1px solid ${C.line}` }}>
            <div style={{ width: 34, height: 34, borderRadius: "50%", background: C.accentBg, color: C.accentInk,
              display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13, fontWeight: 600 }}>
              {initials(s.full_name)}</div>
            <div><b style={{ fontSize: 14.5 }}>{s.full_name}</b>
              <div style={{ color: C.muted, fontSize: 13 }}>{s.email}</div></div>
          </div>
        ))}
      </div>
    </Card>
  );
}

// --------------------------------------------------------------- Grades
function GradesTab({ course }: { course: SageCourseSummary }) {
  const [g, setG] = useState<SageGrades | null>(null);
  useEffect(() => { sageApi.grades(course.id).then(setG).catch(() => setG(null)); }, [course.id]);
  if (!g) return <p style={{ color: C.muted }}>Loading…</p>;
  const pct = (v?: number) => v == null ? "—" : `${Math.round(v * 100)}%`;
  if (g.is_instructor) {
    return (
      <Card>
        <h3 style={{ marginTop: 0, fontSize: 17 }}>Grades</h3>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", fontSize: 13.5, borderCollapse: "collapse", minWidth: 360 }}>
            <thead><tr style={{ textAlign: "left", color: C.muted }}>
              <th style={{ padding: "6px 8px" }}>Student</th>
              {g.quizzes.map((q) => <th key={q.id} style={{ padding: "6px 8px" }}>{q.title}</th>)}
              <th style={{ padding: "6px 8px" }}>Needs review</th>
            </tr></thead>
            <tbody>
              {(g.rows || []).map((r) => (
                <tr key={r.student_id} style={{ borderTop: `1px solid ${C.line}` }}>
                  <td style={{ padding: "8px", fontWeight: 600 }}>{r.full_name}</td>
                  {g.quizzes.map((q) => <td key={q.id} style={{ padding: "8px" }}>{pct(r.scores[String(q.id)])}</td>)}
                  <td style={{ padding: "8px" }}>{r.open_remediation > 0
                    ? <span style={{ background: C.dangerBg, color: C.danger, padding: "2px 9px",
                      borderRadius: 999, fontWeight: 600 }}>{r.open_remediation}</span> : "0"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {(g.rows || []).length === 0 && <p style={{ color: C.muted }}>No students yet.</p>}
      </Card>
    );
  }
  return (
    <Card>
      <h3 style={{ marginTop: 0, fontSize: 17 }}>My grades</h3>
      {g.quizzes.length === 0 && <p style={{ color: C.muted }}>No quizzes yet.</p>}
      {g.quizzes.map((q) => (
        <div key={q.id} style={{ display: "flex", justifyContent: "space-between",
          padding: "10px 0", borderTop: `1px solid ${C.line}` }}>
          <span>{q.title}</span><b>{pct(g.scores?.[String(q.id)])}</b>
        </div>
      ))}
      {(g.open_remediation || 0) > 0 && (
        <div style={{ background: C.infoBg, color: C.info, borderRadius: 10, padding: "10px 14px",
          marginTop: 12, fontSize: 14 }}>
          You have {g.open_remediation} guided practice session(s) waiting under “Needs review”.</div>
      )}
    </Card>
  );
}

// --------------------------------------------------------------- Needs review (student)
function NeedsReview({ course }: { course: SageCourseSummary }) {
  const [mods, setMods] = useState<RemediationModule[]>([]);
  const nav = useNavigate();
  useEffect(() => {
    api.myModules().then((m) => setMods(m.filter((x) => x.course_id === course.id)))
      .catch(() => setMods([]));
  }, [course.id]);
  const open = mods.filter((m) => m.status !== "completed");
  return (
    <div style={{ display: "grid", gap: 12 }}>
      <h3 style={{ margin: 0, fontSize: 17 }}>Needs review</h3>
      {open.length === 0 && (
        <Card style={{ textAlign: "center", color: C.muted, background: C.successBg, border: "none" }}>
          <Icon name="check" size={24} color={C.success} />
          <div style={{ marginTop: 6 }}>All caught up — nothing to review right now. Nice work!</div>
        </Card>
      )}
      {open.map((m) => (
        <Card key={m.id} style={{ borderColor: "#c9c2f0" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
            <div style={{ display: "flex", gap: 11, alignItems: "flex-start" }}>
              <Icon name="spark" size={20} color={C.primary} />
              <div>
                <b style={{ fontSize: 15 }}>{m.title}</b>
                {m.rationale && <div style={{ color: C.muted, fontSize: 13 }}>{m.rationale}</div>}
                <div style={{ color: C.muted, fontSize: 13 }}>A short guided practice, built for what you missed.</div>
              </div>
            </div>
            <PrimaryBtn onClick={() => nav(`/modules/${m.id}`)}><Icon name="play" size={16} /> Start practice</PrimaryBtn>
          </div>
        </Card>
      ))}
    </div>
  );
}
