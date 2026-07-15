import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  api, sageApi, saveToken, clearToken, loadToken,
  type SageAuth, type SageCourseSummary, type SageCourseDetail, type SageQuizListItem,
  type SageTakeQuiz, type SageSubmitResult, type SageStudent,
  type SageGrades, type SageQuestionDraft, type SageMaterial, type SageProfile,
  type SageQType, type SageAnswerIn, type SageAnnouncement,
} from "../api/client";
import type { RemediationModule } from "../types";
import { renderMarkdown, highlightCode } from "../lib/richtext";
import { resolveBrand } from "../lib/brand";

const BRAND = resolveBrand();

const USER_KEY = "sage_user";

// LMS Bridge marketing homepage (override at deploy time via window.__LMSBRIDGE_HOME__).
const LMSBRIDGE_HOME =
  (typeof window !== "undefined" &&
    (window as unknown as { __LMSBRIDGE_HOME__?: string }).__LMSBRIDGE_HOME__) ||
  "https://www.lmsbridge.app";

const C = {
  brand: "#4f46e5", primary: "#6355e6", primaryDark: "#5346d6",
  accentBg: "#EEECFD", accentInk: "#4b3fce",
  pageBg: "#f4f4fb", line: "#e8e6f2", ink: "#1f2340", muted: "#6b7183",
  success: "#16a34a", successBg: "#e8f7ee", danger: "#dc2626", dangerBg: "#fdeaea",
  info: "#2563eb", infoBg: "#eaf1fe", soft: "#f5f4fc",
  sidebar: "#ffffff", shadow: "0 1px 2px rgba(31,35,64,.05), 0 6px 18px rgba(31,35,64,.05)",
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
function fmtDateTime(iso?: string | null) {
  if (!iso) return "";
  return new Date(iso).toLocaleString([], { dateStyle: "medium", timeStyle: "short" });
}
function toLocalInput(iso?: string | null) {
  if (!iso) return "";
  const d = new Date(iso); const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`;
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
    edit: "M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04a1 1 0 0 0 0-1.41l-2.34-2.34a1 1 0 0 0-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z",
    download: "M5 20h14v-2H5v2zM19 9h-4V3H9v6H5l7 7 7-7z",
    trash: "M6 19a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z",
    file: "M6 2a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6H6zm7 7V3.5L18.5 9H13z",
    note: "M3 5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5zm4 4h10V7H7v2zm0 4h10v-2H7v2zm0 4h7v-2H7v2z",
    code: "M9.4 16.6 4.8 12l4.6-4.6L8 6l-6 6 6 6 1.4-1.4zm5.2 0 4.6-4.6-4.6-4.6L16 6l6 6-6 6-1.4-1.4z",
  };
  const fillStroke = name === "back" ? { fill: "none", stroke: color, strokeWidth: 2, strokeLinecap: "round" as const, strokeLinejoin: "round" as const } : { fill: color };
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true" style={{ flexShrink: 0 }}>
      <path d={p[name]} {...fillStroke} />
    </svg>
  );
}

function Card({ children, style }: { children: React.ReactNode; style?: React.CSSProperties }) {
  return <div style={{ background: "#fff", border: `1px solid ${C.line}`, borderRadius: 16,
    padding: "18px 20px", boxShadow: C.shadow, ...style }}>{children}</div>;
}
function PrimaryBtn({ children, onClick, disabled, type }:
  { children: React.ReactNode; onClick?: () => void; disabled?: boolean; type?: "submit" | "button" }) {
  return <button type={type || "button"} onClick={onClick} disabled={disabled}
    style={{ background: C.primary, color: "#fff", border: "none", borderRadius: 10,
      padding: "10px 18px", fontSize: 14, fontWeight: 600, cursor: disabled ? "default" : "pointer",
      opacity: disabled ? 0.6 : 1, display: "inline-flex", alignItems: "center", gap: 7,
      boxShadow: "0 1px 2px rgba(99,85,230,.35)" }}>{children}</button>;
}
function GhostBtn({ children, onClick }: { children: React.ReactNode; onClick?: () => void }) {
  return <button onClick={onClick} style={{ background: "#fff", color: C.ink, border: `1px solid ${C.line}`,
    borderRadius: 10, padding: "8px 14px", fontSize: 14, cursor: "pointer",
    display: "inline-flex", alignItems: "center", gap: 6 }}>{children}</button>;
}
const inputStyle: React.CSSProperties = { width: "100%", padding: "11px 13px", border: `1px solid ${C.line}`,
  borderRadius: 10, fontSize: 14.5, fontFamily: "inherit", boxSizing: "border-box", background: "#fff" };

// Mastery/score visuals (matches the mockup's green/amber/red scale + progress bars).
function scoreColor(v: number) { return v <= 0.7 ? C.danger : v < 0.85 ? "#d97706" : C.success; }
function Bar({ v, width }: { v: number; width?: number | string }) {
  const p = Math.round(Math.max(0, Math.min(1, v)) * 100);
  return <div style={{ height: 7, width: width ?? "100%", background: C.soft, borderRadius: 999,
    overflow: "hidden", flexShrink: 0 }}>
    <div style={{ width: `${p}%`, height: "100%", background: scoreColor(v), borderRadius: 999 }} /></div>;
}
// A compact SVG donut for a single percentage (mockup's "practice impact" style).
function Donut({ v, size = 92 }: { v: number; size?: number }) {
  const p = Math.max(0, Math.min(1, v));
  const r = (size - 12) / 2, c = 2 * Math.PI * r;
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={C.soft} strokeWidth={10} />
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={C.primary} strokeWidth={10}
        strokeLinecap="round" strokeDasharray={c} strokeDashoffset={c * (1 - p)}
        transform={`rotate(-90 ${size / 2} ${size / 2})`} />
      <text x="50%" y="50%" dominantBaseline="central" textAnchor="middle"
        fontSize={size * 0.24} fontWeight={800} fill={C.ink}>{Math.round(p * 100)}%</text>
    </svg>
  );
}

function SideLink({ icon, label, active, onClick }:
  { icon: string; label: string; active?: boolean; onClick: () => void }) {
  return (
    <button onClick={onClick} style={{ display: "flex", alignItems: "center", gap: 11, width: "100%",
      textAlign: "left", cursor: "pointer", padding: "9px 11px", fontSize: 14, borderRadius: 9,
      border: "none", fontWeight: active ? 700 : 500, color: active ? C.primary : C.muted,
      background: active ? C.accentBg : "transparent" }}>
      <Icon name={icon} size={18} color={active ? C.primary : C.muted} /> {label}
    </button>
  );
}

export default function SageApp() {
  const [user, setUser] = useState<SageAuth | null>(loadUser());
  const [view, setView] = useState<"auth" | "courses" | "course" | "profile">(
    loadToken() && loadUser() ? "courses" : "auth");
  const [course, setCourse] = useState<SageCourseSummary | null>(null);
  const [courseTab, setCourseTab] = useState("Home");
  const [detail, setDetail] = useState<SageCourseDetail | null>(null);

  function onAuth(a: SageAuth) { persist(a); setUser(a); setView("courses"); }
  function signOut() { clearToken(); sessionStorage.removeItem(USER_KEY); setUser(null); setView("auth"); }
  function openCourse(c: SageCourseSummary) {
    setCourse(c); setCourseTab("Home"); setDetail(null);
    sageApi.courseDetail(c.id).then(setDetail).catch(() => setDetail(null));
    setView("course");
  }

  // Auth screens: no app sidebar — a slim brand bar over centered content.
  if (view === "auth" || !user) {
    return (
      <div style={{ minHeight: "100vh", background: C.pageBg, color: C.ink }}>
        <header style={{ background: BRAND.accent || C.brand, color: "#fff", padding: "13px 0" }}>
          <div style={{ maxWidth: 1120, margin: "0 auto", padding: "0 20px", display: "flex",
            alignItems: "center", gap: 9 }}>
            <span style={{ display: "flex", alignItems: "center", gap: 8, fontWeight: 800, fontSize: 18 }}>
              {BRAND.logoUrl ? <img src={BRAND.logoUrl} alt={BRAND.name} style={{ height: 22 }} />
                : <Icon name="school" size={20} />} {BRAND.name}</span>
            <a href={LMSBRIDGE_HOME} target="_blank" rel="noreferrer"
              style={{ opacity: 0.75, fontWeight: 400, fontSize: 12.5, color: "#fff",
                textDecoration: "underline", textUnderlineOffset: 3 }}>· {BRAND.attribution}</a>
          </div>
        </header>
        <div style={{ maxWidth: 1120, margin: "0 auto", padding: "24px 16px 56px" }}>
          <Auth onAuth={onAuth} />
        </div>
      </div>
    );
  }

  const inCourse = view === "course" && course;
  const courseTabs = course && course.role === "instructor"
    ? ["Home", "Syllabus", "Materials", "Quizzes", "Students", "Grades"]
    : ["Home", "Syllabus", "Materials", "Quizzes", "Grades", "Needs review"];

  return (
    <div style={{ minHeight: "100vh", background: C.pageBg, color: C.ink, display: "flex" }}>
      {/* persistent app sidebar */}
      <aside style={{ width: 232, flexShrink: 0, background: C.sidebar, borderRight: `1px solid ${C.line}`,
        display: "flex", flexDirection: "column", padding: "16px 12px", position: "sticky", top: 0,
        height: "100vh", boxSizing: "border-box" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 9, padding: "4px 8px 14px",
          borderBottom: `1px solid ${C.line}`, marginBottom: 10 }}>
          <span style={{ width: 30, height: 30, borderRadius: 9, background: C.primary, color: "#fff",
            display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
            {BRAND.logoUrl ? <img src={BRAND.logoUrl} alt="" style={{ height: 18 }} /> : <Icon name="school" size={18} color="#fff" />}
          </span>
          <div style={{ lineHeight: 1.15 }}>
            <div style={{ fontWeight: 800, fontSize: 16, color: C.ink }}>{BRAND.name}</div>
            <a href={LMSBRIDGE_HOME} target="_blank" rel="noreferrer"
              style={{ fontSize: 10.5, color: C.muted, textDecoration: "none" }}>· {BRAND.attribution}</a>
          </div>
        </div>

        <nav style={{ display: "grid", gap: 2, flex: 1, alignContent: "start" }}>
          {inCourse ? (
            <>
              <button onClick={() => setView("courses")} style={{ display: "flex", alignItems: "center", gap: 8,
                background: "none", border: "none", cursor: "pointer", color: C.muted, fontSize: 12.5,
                padding: "4px 11px 10px" }}><Icon name="back" size={14} /> All courses</button>
              <div style={{ padding: "0 11px 10px", fontWeight: 700, fontSize: 13.5, color: C.ink,
                whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{course!.name}</div>
              {courseTabs.map((tName) => (
                <SideLink key={tName} icon={TAB_ICON[tName] || "note"} label={tName}
                  active={courseTab === tName} onClick={() => setCourseTab(tName)} />
              ))}
            </>
          ) : (
            <>
              <SideLink icon="school" label="Courses" active={view === "courses"} onClick={() => setView("courses")} />
              <SideLink icon="note" label="Profile" active={view === "profile"} onClick={() => setView("profile")} />
            </>
          )}
        </nav>

        <div style={{ borderTop: `1px solid ${C.line}`, paddingTop: 10, marginTop: 8 }}>
          <button onClick={() => setView("profile")} style={{ display: "flex", alignItems: "center", gap: 9,
            width: "100%", background: "none", border: "none", cursor: "pointer", padding: "6px 8px",
            marginBottom: 4 }}>
            <span style={{ width: 30, height: 30, borderRadius: "50%", background: C.accentBg, color: C.accentInk,
              display: "flex", alignItems: "center", justifyContent: "center", fontSize: 12, fontWeight: 700,
              flexShrink: 0 }}>{initials(user.full_name)}</span>
            <span style={{ fontSize: 13, color: C.ink, fontWeight: 600, overflow: "hidden",
              textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{user.full_name}</span>
          </button>
          <SideLink icon="logout" label="Sign out" onClick={signOut} />
        </div>
      </aside>

      {/* content */}
      <div style={{ flex: 1, minWidth: 0, padding: "28px 32px 56px", maxWidth: 1120 }}>
        {view === "profile" && <Profile onName={(n) => user && setUser({ ...user, full_name: n })}
          onBack={() => setView("courses")} />}
        {view === "courses" && <Courses userName={user.full_name} onOpen={openCourse} />}
        {inCourse && <CourseView course={course!} tab={courseTab} detail={detail}
          reloadDetail={() => sageApi.courseDetail(course!.id).then(setDetail).catch(() => setDetail(null))} />}
      </div>
    </div>
  );
}

// --------------------------------------------------------------- Auth
function Auth({ onAuth }: { onAuth: (a: SageAuth) => void }) {
  const [mode, setMode] = useState<"pick" | "signup" | "join" | "login">("pick");
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

  // Role-picker landing.
  if (mode === "pick") {
    const roleCard = (opts: { icon: string; title: string; sub: string; onClick: () => void }) => (
      <button onClick={opts.onClick} style={{ textAlign: "left", cursor: "pointer", background: "#fff",
        border: `1px solid ${C.line}`, borderRadius: 14, padding: "18px 18px", boxShadow: C.shadow,
        display: "flex", gap: 13, alignItems: "center", width: "100%" }}>
        <div style={{ width: 44, height: 44, borderRadius: 12, background: C.accentBg, color: C.primary,
          display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
          <Icon name={opts.icon} size={22} color={C.primary} /></div>
        <div>
          <div style={{ fontWeight: 700, fontSize: 15.5, color: C.ink }}>{opts.title}</div>
          <div style={{ fontSize: 13, color: C.muted, marginTop: 2 }}>{opts.sub}</div>
        </div>
      </button>
    );
    return (
      <div style={{ maxWidth: 560, margin: "24px auto", textAlign: "center" }}>
        <h1 style={{ color: C.ink, marginBottom: 8, fontSize: 30 }}>Welcome to {BRAND.name}</h1>
        <p style={{ color: C.muted, marginTop: 0, fontSize: 15, lineHeight: 1.55, maxWidth: 460,
          margin: "0 auto 22px" }}>{BRAND.tagline}</p>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
          {roleCard({ icon: "edit", title: "I'm an instructor", sub: "Create a course",
            onClick: () => { setMode("signup"); setErr(null); } })}
          {roleCard({ icon: "school", title: "I'm a student", sub: "Join a course",
            onClick: () => { setMode("join"); setErr(null); } })}
        </div>
        <p style={{ color: C.muted, fontSize: 13.5, marginTop: 20 }}>
          Already have an account?{" "}
          <button onClick={() => { setMode("login"); setErr(null); }} style={{ background: "none",
            border: "none", color: C.primary, fontWeight: 600, cursor: "pointer", fontSize: 13.5,
            padding: 0 }}>Log in</button>
        </p>
        <p style={{ color: C.muted, fontSize: 12.5, marginTop: 24 }}>
          No LMS required. Just great teaching and learning.
        </p>
      </div>
    );
  }

  const heading = mode === "signup" ? "Create your instructor account"
    : mode === "login" ? "Welcome back" : "Join a course";
  const subhead = mode === "signup" ? `Start building courses with ${BRAND.name}.`
    : mode === "login" ? "Log in to continue." : "Enter the course code your instructor shared.";
  return (
    <div style={{ maxWidth: 420, margin: "24px auto" }}>
      <button onClick={() => { setMode("pick"); setErr(null); }} style={{ display: "inline-flex",
        alignItems: "center", gap: 6, background: "none", border: "none", cursor: "pointer",
        color: C.muted, fontSize: 13, marginBottom: 10 }}><Icon name="back" size={15} /> Back</button>
      <Card>
        <h1 style={{ textAlign: "center", color: C.ink, margin: "2px 0 4px", fontSize: 23 }}>{heading}</h1>
        <p style={{ textAlign: "center", color: C.muted, marginTop: 0, marginBottom: 18, fontSize: 14 }}>{subhead}</p>
        <form onSubmit={go} style={{ display: "grid", gap: 11 }}>
          {mode === "join" && <input style={inputStyle} placeholder="Course join code (e.g. 7QK4PD)"
            value={code} onChange={(e) => setCode(e.target.value)} />}
          {mode !== "login" && <input style={inputStyle} placeholder="Your name"
            value={name} onChange={(e) => setName(e.target.value)} />}
          {mode !== "join" && <input style={inputStyle} placeholder="Email" type="email"
            value={email} onChange={(e) => setEmail(e.target.value)} />}
          {mode !== "join" && <input style={inputStyle} placeholder="Password" type="password"
            value={pw} onChange={(e) => setPw(e.target.value)} />}
          <PrimaryBtn type="submit" disabled={busy}>
            {busy ? "…" : mode === "signup" ? "Create account"
              : mode === "login" ? "Log in" : "Join course"}
          </PrimaryBtn>
          {err && <div style={{ color: C.danger, fontSize: 13 }}>{err}</div>}
        </form>
        {mode === "signup" && (
          <p style={{ textAlign: "center", color: C.muted, fontSize: 13, marginTop: 14, marginBottom: 0 }}>
            Already have an account?{" "}
            <button onClick={() => { setMode("login"); setErr(null); }} style={{ background: "none",
              border: "none", color: C.primary, fontWeight: 600, cursor: "pointer", fontSize: 13, padding: 0 }}>Log in</button>
          </p>
        )}
        {mode === "login" && (
          <p style={{ textAlign: "center", color: C.muted, fontSize: 13, marginTop: 14, marginBottom: 0 }}>
            Don't have an account?{" "}
            <button onClick={() => { setMode("signup"); setErr(null); }} style={{ background: "none",
              border: "none", color: C.primary, fontWeight: 600, cursor: "pointer", fontSize: 13, padding: 0 }}>Create one</button>
          </p>
        )}
        {mode === "join" && (
          <p style={{ textAlign: "center", color: C.muted, fontSize: 12.5, marginTop: 14, marginBottom: 0 }}>
            No account or email required. Need a code? Ask your instructor.
          </p>
        )}
      </Card>
    </div>
  );
}

// --------------------------------------------------------------- Courses
function greeting() {
  const h = new Date().getHours();
  return h < 12 ? "Good morning" : h < 18 ? "Good afternoon" : "Good evening";
}

function Courses({ onOpen, userName }: { onOpen: (c: SageCourseSummary) => void; userName: string }) {
  const [courses, setCourses] = useState<SageCourseSummary[]>([]);
  const [name, setName] = useState(""); const [subject, setSubject] = useState("");
  const [code, setCode] = useState(""); const [msg, setMsg] = useState<string | null>(null);
  const load = () => sageApi.courses().then(setCourses).catch(() => setCourses([]));
  useEffect(() => { load(); }, []);

  const firstName = userName.trim().split(/\s+/)[0] || userName;
  const teaching = courses.filter((c) => c.role === "instructor");
  const totalStudents = teaching.reduce((s, c) => s + (c.student_count || 0), 0);
  const totalQuizzes = teaching.reduce((s, c) => s + (c.quiz_count || 0), 0);

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
      <div style={{ marginBottom: 20 }}>
        <h1 style={{ margin: 0, fontSize: 24, color: C.ink }}>{greeting()}, {firstName}</h1>
        <p style={{ margin: "4px 0 0", color: C.muted, fontSize: 14.5 }}>
          Here's what's happening in your courses.</p>
      </div>
      {teaching.length > 0 && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
          gap: 12, marginBottom: 20 }}>
          <Stat label="Courses" value={teaching.length} />
          <Stat label="Students" value={totalStudents} />
          <Stat label="Quizzes" value={totalQuizzes} />
        </div>
      )}
      <h2 style={{ color: C.ink, fontSize: 18, margin: "0 0 12px" }}>Your courses</h2>
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

const TAB_ICON: Record<string, string> = {
  Home: "spark", Syllabus: "note", Materials: "file", Quizzes: "check",
  Students: "school", Grades: "download", "Needs review": "alert",
};

function CourseView({ course, tab, detail, reloadDetail }:
  { course: SageCourseSummary; tab: string; detail: SageCourseDetail | null; reloadDetail: () => void }) {
  const instr = course.role === "instructor";
  return (
    <div style={{ minWidth: 0 }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between",
        flexWrap: "wrap", gap: 10, margin: "0 0 18px" }}>
        <h1 style={{ color: C.ink, margin: 0, fontSize: 23 }}>{tab === "Home" ? course.name : tab}</h1>
        {instr && <CopyChip code={course.join_code} />}
      </div>
      {tab === "Home" && <Home course={course} instr={instr} detail={detail} />}
      {tab === "Syllabus" && <Syllabus course={course} instr={instr} detail={detail} onSaved={reloadDetail} />}
      {tab === "Materials" && <Materials course={course} instr={instr} />}
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
    <div style={{ background: "#fff", border: `1px solid ${C.line}`, borderRadius: 14,
      padding: "16px 18px", boxShadow: C.shadow }}>
      <div style={{ fontSize: 30, fontWeight: 800, lineHeight: 1.05,
        color: danger ? C.danger : C.ink }}>{value}</div>
      <div style={{ fontSize: 13, marginTop: 5, color: danger ? C.danger : C.muted }}>{label}</div>
    </div>
  );
}

function Announcements({ course, instr }: { course: SageCourseSummary; instr: boolean }) {
  const [items, setItems] = useState<SageAnnouncement[]>([]);
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState(""); const [body, setBody] = useState("");
  const [busy, setBusy] = useState(false);
  const load = () => sageApi.announcements(course.id).then(setItems).catch(() => setItems([]));
  useEffect(() => { load(); }, [course.id]);
  async function post() {
    if (!title.trim()) return; setBusy(true);
    try { await sageApi.createAnnouncement(course.id, title.trim(), body); setTitle(""); setBody(""); setOpen(false); load(); }
    finally { setBusy(false); }
  }
  return (
    <Card>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 8 }}>
        <h3 style={{ marginTop: 0, marginBottom: 0, fontSize: 17 }}>Announcements</h3>
        {instr && <GhostBtn onClick={() => setOpen((o) => !o)}>
          <Icon name="plus" size={15} /> {open ? "Cancel" : "Post"}</GhostBtn>}
      </div>
      {open && (
        <div style={{ marginTop: 10, display: "grid", gap: 8 }}>
          <input style={inputStyle} placeholder="Title" value={title} onChange={(e) => setTitle(e.target.value)} />
          <textarea style={{ ...inputStyle, minHeight: 70, resize: "vertical" }} placeholder="Message (Markdown supported)"
            value={body} onChange={(e) => setBody(e.target.value)} />
          <div><PrimaryBtn onClick={post} disabled={busy}>{busy ? "Posting…" : "Post announcement"}</PrimaryBtn></div>
        </div>
      )}
      <div style={{ marginTop: 12 }}>
        {items.length === 0 && <p style={{ color: C.muted, margin: 0 }}>No announcements yet.</p>}
        {items.map((a) => (
          <div key={a.id} style={{ padding: "10px 0", borderTop: `1px solid ${C.line}` }}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
              <b style={{ fontSize: 14.5 }}>{a.title}</b>
              <span style={{ display: "flex", gap: 8, alignItems: "center" }}>
                <span style={{ color: C.muted, fontSize: 12 }}>{fmtDateTime(a.created_at)}</span>
                {instr && <button onClick={() => sageApi.deleteAnnouncement(a.id).then(load)} title="Delete"
                  style={{ background: "none", border: "none", color: C.danger, cursor: "pointer" }}>
                  <Icon name="trash" size={14} /></button>}
              </span>
            </div>
            {a.body && <div className="sage-md" style={{ fontSize: 13.5, marginTop: 4 }}
              dangerouslySetInnerHTML={{ __html: renderMarkdown(a.body) }} />}
          </div>
        ))}
      </div>
    </Card>
  );
}

function Home({ course, instr, detail }:
  { course: SageCourseSummary; instr: boolean; detail: SageCourseDetail | null }) {
  const ins = detail?.instructor;
  return (
    <div style={{ display: "grid", gap: 14 }}>
      {instr && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))", gap: 12 }}>
          <Stat label="Students" value={course.student_count} />
          <Stat label="Quizzes" value={course.quiz_count} />
        </div>
      )}
      <Announcements course={course} instr={instr} />
      {ins && (ins.title || ins.bio || ins.full_name) && (
        <Card style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
          <div style={{ width: 42, height: 42, borderRadius: "50%", background: C.accentBg, color: C.accentInk,
            display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700, flexShrink: 0 }}>
            {initials(ins.full_name)}</div>
          <div>
            <div style={{ fontSize: 12, color: C.muted }}>Taught by</div>
            <div style={{ fontWeight: 700 }}>{ins.full_name}</div>
            {ins.title && <div style={{ fontSize: 13.5, color: C.accentInk }}>{ins.title}</div>}
            {ins.bio && <div style={{ fontSize: 13.5, color: "#444", marginTop: 4, lineHeight: 1.5 }}>{ins.bio}</div>}
          </div>
        </Card>
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
  const [editId, setEditId] = useState<number | null>(null);
  const [initial, setInitial] = useState<
    { title: string; questions: SageQuestionDraft[]; due_at?: string | null } | null>(null);
  const load = () => sageApi.quizzes(course.id).then(setQuizzes).catch(() => setQuizzes([]));
  useEffect(() => { load(); }, [course.id]);

  function startNew() { setInitial(null); setEditId(null); setBuild(true); }
  async function startEdit(id: number) {
    const q = await sageApi.quizForEdit(id);
    setInitial({ title: q.title, questions: q.questions, due_at: q.due_at });
    setEditId(id); setBuild(true);
  }
  async function dup(id: number) { await sageApi.duplicateQuiz(id); load(); }
  async function del(id: number) {
    if (!window.confirm("Delete this quiz? Student results for it will also be removed.")) return;
    await sageApi.deleteQuiz(id); load();
  }
  return (
    <div style={{ display: "grid", gap: 12 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h3 style={{ margin: 0, fontSize: 17 }}>Quizzes</h3>
        {!build && <PrimaryBtn onClick={startNew}><Icon name="plus" size={16} /> New quiz</PrimaryBtn>}
      </div>
      {build && <QuizBuilder courseId={course.id} editId={editId} initial={initial}
        onCancel={() => setBuild(false)} onDone={() => { setBuild(false); load(); }} />}
      {quizzes.length === 0 && !build && (
        <Card style={{ textAlign: "center", color: C.muted, background: C.soft, border: "none" }}>
          No quizzes yet. Click <b>New quiz</b> to build one — multiple choice, true/false, multiple
          answers, or short answer.
        </Card>
      )}
      {!build && quizzes.map((q) => {
        const pct = q.submission_count != null && course.student_count
          ? Math.round((q.submission_count / course.student_count) * 100) : 0;
        return (
          <Card key={q.id}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
              <div>
                <b style={{ fontSize: 15 }}>{q.title}</b>
                <div style={{ color: C.muted, fontSize: 13 }}>
                  {q.question_count} questions · {q.submission_count ?? 0} submitted
                  {q.due_at && <> · due {fmtDateTime(q.due_at)}</>}</div>
              </div>
              <div style={{ display: "flex", gap: 6 }}>
                <GhostBtn onClick={() => startEdit(q.id)}><Icon name="edit" size={15} /> Edit</GhostBtn>
                <GhostBtn onClick={() => dup(q.id)}><Icon name="copy" size={15} /> Duplicate</GhostBtn>
                <button onClick={() => del(q.id)} title="Delete" style={{ background: "none", border: "none",
                  cursor: "pointer", color: C.danger, padding: 6 }}><Icon name="trash" size={16} /></button>
              </div>
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

const QTYPE_LABELS: { value: SageQType; label: string }[] = [
  { value: "mcq", label: "Multiple choice" },
  { value: "true_false", label: "True / False" },
  { value: "multi", label: "Multiple answers" },
  { value: "short", label: "Short answer" },
];

function QuizBuilder({ courseId, editId, initial, onDone, onCancel }: {
  courseId: number; editId: number | null;
  initial: { title: string; questions: SageQuestionDraft[]; due_at?: string | null } | null;
  onDone: () => void; onCancel: () => void;
}) {
  const blank = (): SageQuestionDraft =>
    ({ prompt: "", qtype: "mcq", choices: ["", ""], correct: [], concept: "" });
  const [title, setTitle] = useState(initial?.title || "");
  const [dueAt, setDueAt] = useState(toLocalInput(initial?.due_at));
  const [qs, setQs] = useState<SageQuestionDraft[]>(
    initial?.questions?.length ? initial.questions : [blank()]);
  const [err, setErr] = useState<string | null>(null); const [busy, setBusy] = useState(false);

  function upd(i: number, patch: Partial<SageQuestionDraft>) {
    setQs((arr) => arr.map((q, j) => j === i ? { ...q, ...patch } : q));
  }
  function setType(i: number, qtype: SageQType) {
    setQs((arr) => arr.map((q, j) => {
      if (j !== i) return q;
      if (qtype === "true_false") return { ...q, qtype, choices: ["True", "False"], correct: [] };
      if (qtype === "short") return { ...q, qtype, choices: [], correct: q.correct };
      return { ...q, qtype, choices: q.choices.length >= 2 ? q.choices : ["", ""], correct: [] };
    }));
  }
  function setChoice(i: number, ci: number, v: string) {
    setQs((arr) => arr.map((q, j) => {
      if (j !== i) return q;
      const old = q.choices[ci];
      const choices = q.choices.map((x, k) => k === ci ? v : x);
      const correct = q.correct.map((c) => c === old ? v : c);
      return { ...q, choices, correct };
    }));
  }
  function toggleCorrect(i: number, choice: string, single: boolean) {
    setQs((arr) => arr.map((q, j) => {
      if (j !== i) return q;
      if (single) return { ...q, correct: [choice] };
      const has = q.correct.includes(choice);
      return { ...q, correct: has ? q.correct.filter((c) => c !== choice) : [...q.correct, choice] };
    }));
  }
  async function save() {
    setErr(null);
    if (!title.trim()) { setErr("Add a quiz title."); return; }
    const payload: SageQuestionDraft[] = [];
    for (const q of qs) {
      if (!q.prompt.trim() || !q.concept.trim()) { setErr("Each question needs a prompt and a concept."); return; }
      let choices = q.choices.map((c) => c.trim()).filter(Boolean);
      let correct = q.correct.map((c) => c.trim()).filter(Boolean);
      if (q.qtype === "true_false") choices = ["True", "False"];
      if (q.qtype === "short") { choices = []; if (!correct.length) { setErr(`Add accepted answer(s) for: ${q.prompt}`); return; } }
      else {
        if (choices.length < 2) { setErr(`Add at least 2 choices for: ${q.prompt}`); return; }
        correct = correct.filter((c) => choices.includes(c));
        if ((q.qtype === "mcq" || q.qtype === "true_false") && correct.length !== 1) {
          setErr(`Mark exactly one correct answer for: ${q.prompt}`); return;
        }
        if (q.qtype === "multi" && correct.length < 1) { setErr(`Mark the correct answers for: ${q.prompt}`); return; }
      }
      payload.push({ ...q, choices, correct });
    }
    const due = dueAt ? new Date(dueAt).toISOString() : null;
    setBusy(true);
    try {
      if (editId != null) await sageApi.updateQuiz(editId, title, payload, due);
      else await sageApi.createQuiz(courseId, title, payload, due);
      onDone();
    } catch (e) { setErr((e as Error).message); } finally { setBusy(false); }
  }
  return (
    <Card style={{ background: C.soft, border: `1px solid ${C.line}` }}>
      <input style={{ ...inputStyle, marginBottom: 10, fontWeight: 600 }} placeholder="Quiz title (e.g. Binary basics)"
        value={title} onChange={(e) => setTitle(e.target.value)} />
      <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 14, flexWrap: "wrap" }}>
        <label style={{ fontSize: 13, color: C.muted }}>Due date (optional)</label>
        <input type="datetime-local" style={{ ...inputStyle, width: "auto" }} value={dueAt}
          onChange={(e) => setDueAt(e.target.value)} />
        {dueAt && <GhostBtn onClick={() => setDueAt("")}>Clear</GhostBtn>}
      </div>
      {qs.map((q, i) => (
        <div key={i} style={{ background: "#fff", border: `1px solid ${C.line}`, borderRadius: 12, padding: 14, marginBottom: 10 }}>
          <div style={{ display: "flex", gap: 8, marginBottom: 8, alignItems: "center" }}>
            <span style={{ fontSize: 13, color: C.muted, fontWeight: 600 }}>Q{i + 1}</span>
            <select value={q.qtype} onChange={(e) => setType(i, e.target.value as SageQType)}
              style={{ ...inputStyle, width: "auto", padding: "7px 10px" }}>
              {QTYPE_LABELS.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
            {qs.length > 1 && <button onClick={() => setQs((a) => a.filter((_, j) => j !== i))}
              title="Remove question" style={{ marginLeft: "auto", background: "none", border: "none",
                color: C.danger, cursor: "pointer" }}><Icon name="trash" size={15} /></button>}
          </div>
          <input style={{ ...inputStyle, marginBottom: 8 }} placeholder="Question prompt"
            value={q.prompt} onChange={(e) => upd(i, { prompt: e.target.value })} />

          {q.qtype === "short" ? (
            <input style={inputStyle} placeholder="Accepted answer(s), comma-separated"
              value={q.correct.join(", ")}
              onChange={(e) => upd(i, { correct: e.target.value.split(",").map((s) => s.trim()) })} />
          ) : (
            <>
              <div style={{ fontSize: 12, color: C.muted, marginBottom: 6 }}>
                {q.qtype === "multi" ? "Check every correct answer." : "Select the one correct answer."}</div>
              {(q.qtype === "true_false" ? ["True", "False"] : q.choices).map((c, ci) => (
                <div key={ci} style={{ display: "flex", gap: 9, alignItems: "center", marginBottom: 6 }}>
                  <input type={q.qtype === "multi" ? "checkbox" : "radio"} name={`correct-${i}`}
                    checked={q.correct.includes(c) && !!c}
                    onChange={() => toggleCorrect(i, c, q.qtype !== "multi")}
                    style={{ accentColor: C.primary }} title="Mark correct" />
                  {q.qtype === "true_false"
                    ? <span style={{ fontSize: 14 }}>{c}</span>
                    : <input style={inputStyle} placeholder={`Choice ${ci + 1}`} value={c}
                        onChange={(e) => setChoice(i, ci, e.target.value)} />}
                </div>
              ))}
              {q.qtype !== "true_false" && (
                <GhostBtn onClick={() => upd(i, { choices: [...q.choices, ""] })}>+ choice</GhostBtn>
              )}
            </>
          )}
          <input style={{ ...inputStyle, marginTop: 8 }} placeholder="Concept (e.g. Binary arithmetic)"
            value={q.concept} onChange={(e) => upd(i, { concept: e.target.value })} />
        </div>
      ))}
      <div style={{ display: "flex", gap: 8, marginTop: 6, flexWrap: "wrap" }}>
        <GhostBtn onClick={() => setQs((a) => [...a, blank()])}><Icon name="plus" size={15} /> Add question</GhostBtn>
        <PrimaryBtn onClick={save} disabled={busy}>{busy ? "Saving…" : editId != null ? "Save changes" : "Save quiz"}</PrimaryBtn>
        <GhostBtn onClick={onCancel}>Cancel</GhostBtn>
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
  const [answers, setAnswers] = useState<Record<number, { choice?: string; choices?: string[] }>>({});
  const load = () => sageApi.quizzes(course.id).then(setQuizzes).catch(() => setQuizzes([]));
  useEffect(() => { load(); }, [course.id]);

  async function open(id: number) { setResult(null); setAnswers({}); setTaking(await sageApi.takeQuiz(id)); }
  function setChoice(qid: number, choice: string) { setAnswers((a) => ({ ...a, [qid]: { choice } })); }
  function toggleMulti(qid: number, choice: string) {
    setAnswers((a) => {
      const cur = a[qid]?.choices || [];
      const has = cur.includes(choice);
      return { ...a, [qid]: { choices: has ? cur.filter((c) => c !== choice) : [...cur, choice] } };
    });
  }
  function isAnswered(qid: number) {
    const v = answers[qid];
    return !!v && (!!v.choice?.trim() || (v.choices && v.choices.length > 0));
  }
  async function submit() {
    if (!taking) return;
    const payload: SageAnswerIn[] = taking.questions.map((q) => ({ question_id: q.id, ...answers[q.id] }));
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
    const answered = taking.questions.filter((q) => isAnswered(q.id)).length;
    return (
      <Card>
        <h3 style={{ marginTop: 0, fontSize: 17 }}>{taking.title}</h3>
        <div style={{ fontSize: 13, color: C.muted, marginBottom: 6 }}>{answered} of {taking.questions.length} answered</div>
        {taking.questions.map((q, i) => (
          <div key={q.id} style={{ padding: "12px 0", borderTop: `1px solid ${C.line}` }}>
            <div style={{ fontWeight: 600, fontSize: 14.5, marginBottom: 8 }}>
              {i + 1}. {q.prompt}
              {q.qtype === "multi" && <span style={{ color: C.muted, fontWeight: 400, fontSize: 12 }}> (select all that apply)</span>}
            </div>
            {q.qtype === "short" ? (
              <input style={inputStyle} placeholder="Type your answer" value={answers[q.id]?.choice || ""}
                onChange={(e) => setChoice(q.id, e.target.value)} />
            ) : (q.choices.map((c) => {
              const multi = q.qtype === "multi";
              const sel = multi ? !!answers[q.id]?.choices?.includes(c) : answers[q.id]?.choice === c;
              return (
                <label key={c} style={{ display: "flex", gap: 9, alignItems: "center", fontSize: 14,
                  padding: "9px 12px", marginBottom: 6, borderRadius: 10, cursor: "pointer",
                  border: `1px solid ${sel ? C.primary : C.line}`, background: sel ? C.soft : "#fff" }}>
                  <input type={multi ? "checkbox" : "radio"} name={`q-${q.id}`} checked={sel}
                    onChange={() => multi ? toggleMulti(q.id, c) : setChoice(q.id, c)}
                    style={{ accentColor: C.primary }} />{c}
                </label>
              );
            }))}
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
                  {q.due_at && (() => {
                    const overdue = new Date(q.due_at) < new Date();
                    return <span style={{ color: overdue && !taken ? C.danger : C.muted }}>
                      {" · "}{overdue ? "was due" : "due"} {fmtDateTime(q.due_at)}</span>;
                  })()}
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
function StudentDrill({ course, studentId, onClose }:
  { course: SageCourseSummary; studentId: number; onClose: () => void }) {
  const [d, setD] = useState<import("../api/client").SageStudentDetail | null>(null);
  const nav = useNavigate();
  useEffect(() => { sageApi.studentDetail(course.id, studentId).then(setD).catch(() => setD(null)); }, [course.id, studentId]);
  if (!d) return <Card><p style={{ color: C.muted, margin: 0 }}>Loading…</p></Card>;
  const open = d.remediation.filter((m) => m.status !== "completed");
  return (
    <Card style={{ borderColor: "#c9c2f0" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div><b style={{ fontSize: 16 }}>{d.full_name}</b>
          <div style={{ color: C.muted, fontSize: 13 }}>{d.email}</div></div>
        <GhostBtn onClick={onClose}>Close</GhostBtn>
      </div>
      <h4 style={{ margin: "14px 0 6px", fontSize: 14 }}>Quiz attempts</h4>
      {d.quizzes.length === 0 && <p style={{ color: C.muted }}>No quizzes.</p>}
      {d.quizzes.map((q) => (
        <div key={q.id} style={{ display: "flex", justifyContent: "space-between",
          padding: "7px 0", borderTop: `1px solid ${C.line}`, fontSize: 14 }}>
          <span>{q.title} <span style={{ color: C.muted, fontSize: 12 }}>· {q.attempts} attempt(s)</span></span>
          <b>{q.best_score == null ? "—" : `${Math.round(q.best_score * 100)}%`}</b>
        </div>
      ))}
      <h4 style={{ margin: "14px 0 6px", fontSize: 14 }}>Needs review ({open.length})</h4>
      {open.length === 0 && <p style={{ color: C.muted, margin: 0 }}>None open.</p>}
      {open.map((m) => (
        <div key={m.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center",
          padding: "7px 0", borderTop: `1px solid ${C.line}` }}>
          <span style={{ fontSize: 14 }}>{m.concept || m.title}</span>
          <GhostBtn onClick={() => nav(`/modules/${m.id}`)}>View session</GhostBtn>
        </div>
      ))}
    </Card>
  );
}

function GradesTab({ course }: { course: SageCourseSummary }) {
  const [g, setG] = useState<SageGrades | null>(null);
  const [drill, setDrill] = useState<number | null>(null);
  useEffect(() => { sageApi.grades(course.id).then(setG).catch(() => setG(null)); }, [course.id]);
  if (!g) return <p style={{ color: C.muted }}>Loading…</p>;
  const pct = (v?: number) => v == null ? "—" : `${Math.round(v * 100)}%`;
  if (g.is_instructor) {
    return (
      <div style={{ display: "grid", gap: 12 }}>
        {drill != null && <StudentDrill course={course} studentId={drill} onClose={() => setDrill(null)} />}
        <Card>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 8 }}>
            <h3 style={{ marginTop: 0, marginBottom: 0, fontSize: 17 }}>Grades</h3>
            <GhostBtn onClick={() => api.authedDownload(`/sage/courses/${course.id}/grades.csv`, "sage-grades.csv")}>
              <Icon name="download" size={15} /> Download CSV</GhostBtn>
          </div>
          <p style={{ color: C.muted, fontSize: 12.5, margin: "4px 0 10px" }}>Click a student to drill in.</p>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", fontSize: 13.5, borderCollapse: "collapse", minWidth: 360 }}>
              <thead><tr style={{ textAlign: "left", color: C.muted }}>
                <th style={{ padding: "6px 8px" }}>Student</th>
                {g.quizzes.map((q) => <th key={q.id} style={{ padding: "6px 8px" }}>{q.title}</th>)}
                <th style={{ padding: "6px 8px" }}>Needs review</th>
              </tr></thead>
              <tbody>
                {(g.rows || []).map((r) => (
                  <tr key={r.student_id} style={{ borderTop: `1px solid ${C.line}`, cursor: "pointer" }}
                    onClick={() => setDrill(r.student_id)}>
                    <td style={{ padding: "8px", fontWeight: 600, color: C.accentInk }}>{r.full_name}</td>
                    {g.quizzes.map((q) => {
                      const v = r.scores[String(q.id)];
                      return <td key={q.id} style={{ padding: "8px", fontWeight: 600,
                        color: v == null ? C.muted : scoreColor(v) }}>{pct(v)}</td>;
                    })}
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
      </div>
    );
  }
  const scored = g.quizzes
    .map((q) => g.scores?.[String(q.id)])
    .filter((v): v is number => v != null);
  const overall = scored.length ? scored.reduce((a, b) => a + b, 0) / scored.length : null;
  return (
    <div style={{ display: "grid", gap: 14 }}>
      {overall != null && (
        <Card style={{ display: "flex", alignItems: "center", gap: 20 }}>
          <Donut v={overall} />
          <div>
            <div style={{ fontSize: 12.5, color: C.muted }}>Overall mastery</div>
            <div style={{ fontSize: 15, color: C.ink, marginTop: 2 }}>
              across {scored.length} quiz{scored.length === 1 ? "" : "zes"}</div>
          </div>
        </Card>
      )}
      <Card>
        <h3 style={{ marginTop: 0, fontSize: 17 }}>My grades</h3>
        {g.quizzes.length === 0 && <p style={{ color: C.muted }}>No quizzes yet.</p>}
        {g.quizzes.map((q) => {
          const v = g.scores?.[String(q.id)];
          return (
            <div key={q.id} style={{ display: "flex", alignItems: "center", gap: 12,
              padding: "11px 0", borderTop: `1px solid ${C.line}` }}>
              <span style={{ flex: 1, minWidth: 0 }}>{q.title}</span>
              {v != null && <Bar v={v} width={110} />}
              <b style={{ minWidth: 42, textAlign: "right",
                color: v == null ? C.muted : scoreColor(v) }}>{pct(v)}</b>
            </div>
          );
        })}
        {(g.open_remediation || 0) > 0 && (
          <div style={{ background: C.infoBg, color: C.info, borderRadius: 10, padding: "10px 14px",
            marginTop: 12, fontSize: 14 }}>
            You have {g.open_remediation} guided practice session(s) waiting under “Needs review”.</div>
        )}
      </Card>
    </div>
  );
}

// --------------------------------------------------------------- Profile
function Profile({ onName, onBack }: { onName: (n: string) => void; onBack: () => void }) {
  const [p, setP] = useState<SageProfile | null>(null);
  const [name, setName] = useState(""); const [title, setTitle] = useState(""); const [bio, setBio] = useState("");
  const [busy, setBusy] = useState(false); const [msg, setMsg] = useState<string | null>(null);
  useEffect(() => {
    sageApi.profile().then((pr) => { setP(pr); setName(pr.full_name); setTitle(pr.title || ""); setBio(pr.bio || ""); })
      .catch(() => {});
  }, []);
  async function save(e: React.FormEvent) {
    e.preventDefault(); setBusy(true); setMsg(null);
    try { const r = await sageApi.updateProfile({ full_name: name.trim(), title, bio }); onName(r.full_name); setMsg("Saved."); }
    catch (e) { setMsg((e as Error).message); } finally { setBusy(false); }
  }
  const lbl: React.CSSProperties = { fontSize: 13, fontWeight: 600, color: C.muted };
  return (
    <div style={{ maxWidth: 520, margin: "0 auto" }}>
      <GhostBtn onClick={onBack}><Icon name="back" size={16} /> Back</GhostBtn>
      <h2 style={{ color: C.brand, fontSize: 22, marginTop: 12 }}>Your profile</h2>
      <p style={{ color: C.muted, fontSize: 14, marginTop: 0 }}>
        A few details your students will see on the course page.</p>
      <Card>
        <form onSubmit={save} style={{ display: "grid", gap: 6 }}>
          <label style={lbl}>Name</label>
          <input style={inputStyle} value={name} onChange={(e) => setName(e.target.value)} />
          <label style={lbl}>Title (optional)</label>
          <input style={inputStyle} placeholder="e.g. Professor of CS, NYU" value={title}
            onChange={(e) => setTitle(e.target.value)} />
          <label style={lbl}>About you (optional)</label>
          <textarea style={{ ...inputStyle, minHeight: 80, resize: "vertical" }} value={bio}
            placeholder="A sentence or two — what you teach, office hours, anything friendly."
            onChange={(e) => setBio(e.target.value)} />
          <div style={{ marginTop: 8 }}><PrimaryBtn type="submit" disabled={busy}>{busy ? "Saving…" : "Save profile"}</PrimaryBtn></div>
          {msg && <div style={{ fontSize: 13, color: msg === "Saved." ? C.success : C.danger }}>{msg}</div>}
          {p && <div style={{ fontSize: 12, color: C.muted }}>Signed in as {p.email}</div>}
        </form>
      </Card>
    </div>
  );
}

// --------------------------------------------------------------- Syllabus
function Syllabus({ course, instr, detail, onSaved }:
  { course: SageCourseSummary; instr: boolean; detail: SageCourseDetail | null; onSaved: () => void }) {
  const [edit, setEdit] = useState(false);
  const [text, setText] = useState(""); const [busy, setBusy] = useState(false);
  useEffect(() => { setText(detail?.syllabus || ""); }, [detail]);
  async function save() {
    setBusy(true);
    try { await sageApi.updateSyllabus(course.id, text); setEdit(false); onSaved(); } finally { setBusy(false); }
  }
  if (instr && edit) {
    return (
      <Card>
        <textarea style={{ ...inputStyle, minHeight: 240, resize: "vertical", fontFamily: "inherit" }}
          value={text} onChange={(e) => setText(e.target.value)}
          placeholder="Course overview, schedule, grading, policies…" />
        <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
          <PrimaryBtn onClick={save} disabled={busy}>{busy ? "Saving…" : "Save syllabus"}</PrimaryBtn>
          <GhostBtn onClick={() => { setEdit(false); setText(detail?.syllabus || ""); }}>Cancel</GhostBtn>
        </div>
      </Card>
    );
  }
  return (
    <Card>
      {detail?.syllabus
        ? <div className="sage-md" style={{ fontSize: 14.5 }}
            dangerouslySetInnerHTML={{ __html: renderMarkdown(detail.syllabus) }} />
        : <div style={{ color: C.muted }}>{instr
            ? "No syllabus yet — add one so students know what the course covers."
            : "No syllabus posted yet."}</div>}
      {instr && <div style={{ marginTop: 14 }}>
        <GhostBtn onClick={() => setEdit(true)}><Icon name="edit" size={15} /> {detail?.syllabus ? "Edit syllabus" : "Add syllabus"}</GhostBtn>
      </div>}
    </Card>
  );
}

// --------------------------------------------------------------- Materials
function Materials({ course, instr }: { course: SageCourseSummary; instr: boolean }) {
  const [mats, setMats] = useState<SageMaterial[]>([]);
  const [form, setForm] = useState<null | "note" | "code" | "file">(null);
  const load = () => sageApi.materials(course.id).then(setMats).catch(() => setMats([]));
  useEffect(() => { load(); }, [course.id]);
  return (
    <div style={{ display: "grid", gap: 12 }}>
      {instr && (
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <GhostBtn onClick={() => setForm(form === "note" ? null : "note")}><Icon name="note" size={16} /> Add note</GhostBtn>
          <GhostBtn onClick={() => setForm(form === "code" ? null : "code")}><Icon name="code" size={16} /> Add code</GhostBtn>
          <GhostBtn onClick={() => setForm(form === "file" ? null : "file")}><Icon name="file" size={16} /> Upload file</GhostBtn>
        </div>
      )}
      {form && <MaterialForm courseId={course.id} kind={form} onDone={() => { setForm(null); load(); }} />}
      {mats.length === 0 && !form && (
        <Card style={{ textAlign: "center", color: C.muted, background: C.soft, border: "none" }}>
          No materials yet.{instr ? " Add notes, code snippets, or upload files for your students." : " Check back soon."}
        </Card>
      )}
      {mats.map((m) => <MaterialRow key={m.id} m={m} instr={instr} onChange={load} />)}
    </div>
  );
}

function MaterialForm({ courseId, kind, onDone }:
  { courseId: number; kind: "note" | "code" | "file"; onDone: () => void }) {
  const [title, setTitle] = useState(""); const [body, setBody] = useState("");
  const [language, setLanguage] = useState(""); const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false); const [err, setErr] = useState<string | null>(null);
  async function save() {
    setErr(null);
    if (!title.trim()) { setErr("Add a title."); return; }
    setBusy(true);
    try {
      if (kind === "file") {
        if (!file) { setErr("Choose a file."); setBusy(false); return; }
        await sageApi.uploadCourseFile(courseId, file, title.trim());
      } else {
        if (!body.trim()) { setErr("Add some content."); setBusy(false); return; }
        await sageApi.addTextMaterial(courseId, { kind, title: title.trim(), body, language: language || undefined });
      }
      onDone();
    } catch (e) { setErr((e as Error).message); } finally { setBusy(false); }
  }
  return (
    <Card style={{ background: C.soft }}>
      <input style={{ ...inputStyle, marginBottom: 8 }}
        placeholder={kind === "code" ? "File name (e.g. adder.py)" : "Title"}
        value={title} onChange={(e) => setTitle(e.target.value)} />
      {kind === "file" ? (
        <input type="file" onChange={(e) => setFile(e.target.files?.[0] || null)} />
      ) : (
        <>
          {kind === "code" && <input style={{ ...inputStyle, marginBottom: 8 }} placeholder="Language (e.g. python)"
            value={language} onChange={(e) => setLanguage(e.target.value)} />}
          <textarea style={{ ...inputStyle, minHeight: 140, resize: "vertical",
            fontFamily: kind === "code" ? "var(--font-mono, monospace)" : "inherit" }}
            placeholder={kind === "code" ? "Paste code here…"
              : "Write your note here…  (Markdown: # heading, **bold**, - list, `code`)"}
            value={body} onChange={(e) => setBody(e.target.value)} />
        </>
      )}
      <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
        <PrimaryBtn onClick={save} disabled={busy}>{busy ? "Saving…" : "Add"}</PrimaryBtn>
      </div>
      {err && <div style={{ color: C.danger, fontSize: 13, marginTop: 8 }}>{err}</div>}
    </Card>
  );
}

function fmtSize(n: number) {
  return n < 1024 ? `${n} B` : n < 1048576 ? `${Math.round(n / 1024)} KB` : `${(n / 1048576).toFixed(1)} MB`;
}

function MaterialRow({ m, instr, onChange }: { m: SageMaterial; instr: boolean; onChange: () => void }) {
  const [body, setBody] = useState<string | null>(null);
  const [openB, setOpenB] = useState(false);
  const isText = m.kind === "note" || m.kind === "code";
  async function view() {
    if (!openB && body === null) { const d = await sageApi.material(m.id); setBody(d.body || ""); }
    setOpenB((o) => !o);
  }
  return (
    <Card>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 11 }}>
          <Icon name={m.kind === "code" ? "code" : m.kind === "file" ? "file" : "note"} size={20} color={C.accentInk} />
          <div>
            <b style={{ fontSize: 14.5 }}>{m.title}</b>
            <div style={{ color: C.muted, fontSize: 12.5 }}>
              {m.kind}{m.language ? ` · ${m.language}` : ""}{m.kind === "file" ? ` · ${fmtSize(m.size_bytes)}` : ""}
            </div>
          </div>
        </div>
        <div style={{ display: "flex", gap: 6 }}>
          {isText && <GhostBtn onClick={view}>{openB ? "Hide" : "View"}</GhostBtn>}
          {m.kind === "file" && <GhostBtn onClick={() => api.authedDownload(`/sage/materials/${m.id}/download`, m.filename)}>
            <Icon name="download" size={15} /> Download</GhostBtn>}
          {instr && <button onClick={() => sageApi.deleteMaterial(m.id).then(onChange)}
            title="Delete" style={{ background: "none", border: "none", cursor: "pointer", color: C.danger,
              display: "inline-flex", alignItems: "center", padding: 6 }}><Icon name="trash" size={16} /></button>}
        </div>
      </div>
      {openB && isText && body !== null && (
        m.kind === "code" ? (
          <pre style={{ marginTop: 12, padding: 12, background: "#1e1b2e", color: "#e6e3f5",
            borderRadius: 10, overflowX: "auto", fontSize: 13.5, lineHeight: 1.55,
            fontFamily: "var(--font-mono, monospace)" }}>
            <code dangerouslySetInnerHTML={{ __html: highlightCode(body) }} />
          </pre>
        ) : (
          <div className="sage-md" style={{ marginTop: 12, padding: "12px 14px", background: C.soft,
            color: C.ink, borderRadius: 10, fontSize: 14, overflowX: "auto" }}
            dangerouslySetInnerHTML={{ __html: renderMarkdown(body) }} />
        )
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
