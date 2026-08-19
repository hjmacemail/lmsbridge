import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import LanguageSwitcher from "../components/LanguageSwitcher";
import {
  api, sageApi, saveToken, clearToken, loadToken,
  type SageAuth, type SageCourseSummary, type SageCourseDetail, type SageQuizListItem,
  type SageTakeQuiz, type SageSubmitResult, type SageStudent,
  type SageGrades, type SageQuestionDraft, type SageMaterial, type SageProfile,
  type SageQType, type SageAnswerIn, type SageAnnouncement, type SageQuizAttempt,
  type SageQuizForEdit, type SageAssignment, type SageSubmission,
  type SageSubmissionsView, type SageSubmissionRow,
} from "../api/client";
import type { RemediationModule, InstructorAnalytics, AuthToken, Role } from "../types";
import { useAuth } from "../context/AuthContext";
import ModuleView from "./ModuleView";
import { renderMarkdown, highlightCode } from "../lib/richtext";
import MarkdownEditor from "../components/MarkdownEditor";
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
    chart: "M4 21V10h4v11H4zm6 0V3h4v18h-4zm6 0v-7h4v7h-4z",
    dots: "M12 8a2 2 0 1 0 0-4 2 2 0 0 0 0 4zm0 2a2 2 0 1 0 0 4 2 2 0 0 0 0-4zm0 6a2 2 0 1 0 0 4 2 2 0 0 0 0-4z",
    eye: "M12 5C5 5 2 12 2 12s3 7 10 7 10-7 10-7-3-7-10-7zm0 12a5 5 0 110-10 5 5 0 010 10zm0-2a3 3 0 100-6 3 3 0 000 6z",
  };
  const fillStroke = name === "back" ? { fill: "none", stroke: color, strokeWidth: 2, strokeLinecap: "round" as const, strokeLinejoin: "round" as const } : { fill: color };
  // Directional icons must mirror in right-to-left languages (e.g. "back" points the other way).
  const directional = name === "back" || name === "arrow";
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" aria-hidden="true"
      className={directional ? "dir-flip" : undefined} style={{ flexShrink: 0 }}>
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
function GhostBtn({ children, onClick, disabled }: {
  children: React.ReactNode; onClick?: () => void; disabled?: boolean;
}) {
  return <button onClick={onClick} disabled={disabled} style={{ background: "#fff", color: C.ink,
    border: `1px solid ${C.line}`, borderRadius: 10, padding: "8px 14px", fontSize: 14,
    cursor: disabled ? "not-allowed" : "pointer", opacity: disabled ? 0.55 : 1,
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
  // Create/Join course dialog (opened from the sidebar) + a counter that refreshes the list.
  const [courseDialog, setCourseDialog] = useState<"create" | "join" | null>(null);
  const [coursesReload, setCoursesReload] = useState(0);
  const { t } = useTranslation();
  // Keep the shared AuthContext in sync so the LMS Bridge tutor route (/modules/:id,
  // a Protected route) recognises the Sage session instead of bouncing to /login.
  const { adoptToken, logout: ctxLogout } = useAuth();

  function onAuth(a: SageAuth) {
    persist(a);
    adoptToken({ access_token: a.access_token, token_type: a.token_type,
      role: a.role as Role, user_id: a.user_id, full_name: a.full_name } as AuthToken);
    setUser(a); setView("courses");
  }
  function signOut() {
    clearToken(); sessionStorage.removeItem(USER_KEY); ctxLogout(); setUser(null); setView("auth");
  }
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
            alignItems: "center", gap: 9, justifyContent: "space-between" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 9, minWidth: 0, flexWrap: "wrap" }}>
              <span style={{ display: "flex", alignItems: "center", gap: 8, fontWeight: 800, fontSize: 18,
                whiteSpace: "nowrap" }}>
                {BRAND.logoUrl ? <img src={BRAND.logoUrl} alt={BRAND.name} style={{ height: 22 }} />
                  : <Icon name="school" size={20} />} {BRAND.name}</span>
              <a href={LMSBRIDGE_HOME} target="_blank" rel="noreferrer"
                style={{ opacity: 0.75, fontWeight: 400, fontSize: 12.5, color: "#fff",
                  whiteSpace: "nowrap", textDecoration: "underline", textUnderlineOffset: 3 }}>· {BRAND.attribution}</a>
            </div>
            <LanguageSwitcher dark />
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
    ? ["Home", "Quizzes", "Assignments", "Students", "Grades", "Analytics", "Materials", "Syllabus"]
    : ["Home", "Quizzes", "Assignments", "Grades", "Needs review", "Materials", "Syllabus"];

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
                padding: "4px 11px 10px" }}><Icon name="back" size={14} /> {t("sage.allCourses")}</button>
              <div style={{ padding: "0 11px 10px", fontWeight: 700, fontSize: 13.5, color: C.ink,
                whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{course!.name}</div>
              {courseTabs.map((tName) => (
                <SideLink key={tName} icon={TAB_ICON[tName] || "note"} label={t("sage.tab." + tName)}
                  active={courseTab === tName} onClick={() => setCourseTab(tName)} />
              ))}
            </>
          ) : (
            <>
              <SideLink icon="school" label={t("sage.tab.Courses")} active={view === "courses"} onClick={() => setView("courses")} />
              <SideLink icon="note" label={t("sage.tab.Profile")} active={view === "profile"} onClick={() => setView("profile")} />
              <div style={{ display: "grid", gap: 7, marginTop: 14, padding: "0 3px" }}>
                <button onClick={() => { setView("courses"); setCourseDialog("create"); }}
                  style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 7,
                    background: C.primary, color: "#fff", border: "none", borderRadius: 10,
                    padding: "9px 12px", fontSize: 13.5, fontWeight: 600, cursor: "pointer" }}>
                  <Icon name="plus" size={16} color="#fff" /> {t("sage.courses.createBtn")}
                </button>
                <button onClick={() => { setView("courses"); setCourseDialog("join"); }}
                  style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 7,
                    background: "#fff", color: C.accentInk, border: `1px solid ${C.line}`, borderRadius: 10,
                    padding: "9px 12px", fontSize: 13.5, fontWeight: 600, cursor: "pointer" }}>
                  <Icon name="key" size={15} color={C.accentInk} /> {t("sage.courses.joinTitle")}
                </button>
              </div>
            </>
          )}
        </nav>

        <div style={{ borderTop: `1px solid ${C.line}`, paddingTop: 10, marginTop: 8 }}>
          <div style={{ padding: "2px 8px 8px" }}><LanguageSwitcher /></div>
          <button onClick={() => setView("profile")} style={{ display: "flex", alignItems: "center", gap: 9,
            width: "100%", background: "none", border: "none", cursor: "pointer", padding: "6px 8px",
            marginBottom: 4 }}>
            <span style={{ width: 30, height: 30, borderRadius: "50%", background: C.accentBg, color: C.accentInk,
              display: "flex", alignItems: "center", justifyContent: "center", fontSize: 12, fontWeight: 700,
              flexShrink: 0 }}>{initials(user.full_name)}</span>
            <span style={{ fontSize: 13, color: C.ink, fontWeight: 600, overflow: "hidden",
              textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{user.full_name}</span>
          </button>
          <SideLink icon="logout" label={t("common.signOut")} onClick={signOut} />
        </div>
      </aside>

      {/* content */}
      <div style={{ flex: 1, minWidth: 0, padding: "28px 32px 56px", maxWidth: 1120 }}>
        {view === "profile" && <Profile onName={(n) => user && setUser({ ...user, full_name: n })}
          onBack={() => setView("courses")} />}
        {view === "courses" && <Courses key={coursesReload} userName={user.full_name} onOpen={openCourse} />}
        {inCourse && <CourseView course={course!} tab={courseTab} detail={detail}
          reloadDetail={() => sageApi.courseDetail(course!.id).then(setDetail).catch(() => setDetail(null))} />}
      </div>

      {courseDialog && (
        <CourseDialog mode={courseDialog} onClose={() => setCourseDialog(null)}
          onDone={() => setCoursesReload((n) => n + 1)} />
      )}
    </div>
  );
}

// --------------------------------------------------------------- Auth
function Auth({ onAuth }: { onAuth: (a: SageAuth) => void }) {
  const { t } = useTranslation();
  const [mode, setMode] = useState<"pick" | "signup" | "join" | "login">("pick");
  const [name, setName] = useState(""); const [email, setEmail] = useState("");
  const [pw, setPw] = useState(""); const [code, setCode] = useState("");
  const [err, setErr] = useState<string | null>(null); const [busy, setBusy] = useState(false);

  async function go(e: React.FormEvent) {
    e.preventDefault(); setErr(null);
    // Friendly client-side checks so the user isn't bounced by a server validation error.
    if (mode === "join" && !code.trim()) { setErr(t("sage.auth.errCode")); return; }
    if (mode !== "login" && !name.trim()) { setErr(t("sage.auth.errName")); return; }
    if (!email.trim()) { setErr(t("sage.auth.errEmail")); return; }
    if (!pw) { setErr(t("sage.auth.errPw")); return; }
    if (mode !== "login" && pw.length < 6) { setErr(t("sage.auth.errPwLen")); return; }
    setBusy(true);
    try {
      if (mode === "signup") onAuth(await sageApi.signup(name.trim(), email.trim(), pw));
      else if (mode === "login") {
        const tok = await sageApi.login(email, pw);
        // Persist the token first so the authenticated profile call is authorized,
        // then populate the real identity instead of hard-coding role/name/id.
        saveToken(tok);
        const me = await api.me();
        onAuth({ access_token: tok.access_token, token_type: tok.token_type,
          user_id: me.id, full_name: me.full_name, role: me.role });
      } else {
        // Student "join" now creates a DURABLE account (email + password) via /sage/join, so a
        // returning student can log back in and keep their grades and remediation — instead of an
        // ephemeral guest that's lost when the tab closes.
        onAuth(await sageApi.joinSignup(code.trim().toUpperCase(), name.trim(), email.trim(), pw));
      }
    } catch (e) { setErr((e as Error).message); } finally { setBusy(false); }
  }

  // Low-friction fallback: try a course as a temporary guest (no durable account).
  async function goGuest() {
    setErr(null);
    if (!code.trim()) { setErr(t("sage.auth.errCode")); return; }
    if (!name.trim()) { setErr(t("sage.auth.errName")); return; }
    setBusy(true);
    try { onAuth(await sageApi.guestJoin(code.trim().toUpperCase(), name.trim())); }
    catch (e) { setErr((e as Error).message); } finally { setBusy(false); }
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
        <h1 style={{ color: C.ink, marginBottom: 8, fontSize: 30 }}>{t("sage.auth.welcome", { name: BRAND.name })}</h1>
        <p style={{ color: C.muted, marginTop: 0, fontSize: 15, lineHeight: 1.55, maxWidth: 460,
          margin: "0 auto 22px" }}>{t("sage.auth.tagline", { defaultValue: BRAND.tagline })}</p>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
          {roleCard({ icon: "edit", title: t("sage.auth.instructor"), sub: t("sage.auth.instructorSub"),
            onClick: () => { setMode("signup"); setErr(null); } })}
          {roleCard({ icon: "school", title: t("sage.auth.student"), sub: t("sage.auth.studentSub"),
            onClick: () => { setMode("join"); setErr(null); } })}
        </div>
        <p style={{ color: C.muted, fontSize: 13.5, marginTop: 20 }}>
          {t("sage.auth.haveAccount")}{" "}
          <button onClick={() => { setMode("login"); setErr(null); }} style={{ background: "none",
            border: "none", color: C.primary, fontWeight: 600, cursor: "pointer", fontSize: 13.5,
            padding: 0 }}>{t("sage.auth.login")}</button>
        </p>
        <p style={{ color: C.muted, fontSize: 12.5, marginTop: 24 }}>
          {t("sage.auth.noLms")}
        </p>
      </div>
    );
  }

  const heading = mode === "signup" ? t("sage.auth.signupHead")
    : mode === "login" ? t("sage.auth.loginHead") : t("sage.auth.joinHead");
  const subhead = mode === "signup" ? t("sage.auth.signupSub", { name: BRAND.name })
    : mode === "login" ? t("sage.auth.loginSub") : t("sage.auth.joinSub");
  return (
    <div style={{ maxWidth: 420, margin: "24px auto" }}>
      <button onClick={() => { setMode("pick"); setErr(null); }} style={{ display: "inline-flex",
        alignItems: "center", gap: 6, background: "none", border: "none", cursor: "pointer",
        color: C.muted, fontSize: 13, marginBottom: 10 }}><Icon name="back" size={15} /> {t("sage.back")}</button>
      <Card>
        <h1 style={{ textAlign: "center", color: C.ink, margin: "2px 0 4px", fontSize: 23 }}>{heading}</h1>
        <p style={{ textAlign: "center", color: C.muted, marginTop: 0, marginBottom: 18, fontSize: 14 }}>{subhead}</p>
        <form onSubmit={go} style={{ display: "grid", gap: 11 }}>
          {mode === "join" && <input style={inputStyle} placeholder={t("sage.auth.phCode")}
            value={code} onChange={(e) => setCode(e.target.value)} />}
          {mode !== "login" && <input style={inputStyle} placeholder={t("sage.auth.phName")}
            value={name} onChange={(e) => setName(e.target.value)} />}
          <input style={inputStyle} placeholder={t("sage.auth.phEmail")} type="email"
            value={email} onChange={(e) => setEmail(e.target.value)} />
          <input style={inputStyle} placeholder={t("sage.auth.phPw")} type="password"
            value={pw} onChange={(e) => setPw(e.target.value)} />
          <PrimaryBtn type="submit" disabled={busy}>
            {busy ? "…" : mode === "signup" ? t("sage.auth.createBtn")
              : mode === "login" ? t("sage.auth.loginBtn") : t("sage.auth.joinBtn")}
          </PrimaryBtn>
          {err && <div style={{ color: C.danger, fontSize: 13 }}>{err}</div>}
        </form>
        {(mode === "signup" || mode === "join") && (
          <p style={{ textAlign: "center", color: C.muted, fontSize: 13, marginTop: 14, marginBottom: 0 }}>
            {t("sage.auth.haveAccount")}{" "}
            <button onClick={() => { setMode("login"); setErr(null); }} style={{ background: "none",
              border: "none", color: C.primary, fontWeight: 600, cursor: "pointer", fontSize: 13, padding: 0 }}>{t("sage.auth.login")}</button>
          </p>
        )}
        {mode === "join" && (
          <p style={{ textAlign: "center", color: C.muted, fontSize: 12.5, marginTop: 8, marginBottom: 0 }}>
            {t("sage.auth.guestPrompt", { defaultValue: "Just trying it out?" })}{" "}
            <button type="button" onClick={goGuest} disabled={busy} style={{ background: "none",
              border: "none", color: C.primary, fontWeight: 600, cursor: "pointer", fontSize: 12.5, padding: 0 }}>
              {t("sage.auth.guestBtn", { defaultValue: "Continue as guest" })}</button>
          </p>
        )}
        {mode === "login" && (
          <p style={{ textAlign: "center", color: C.muted, fontSize: 13, marginTop: 14, marginBottom: 0 }}>
            {t("sage.auth.noAccount")}{" "}
            <button onClick={() => { setMode("signup"); setErr(null); }} style={{ background: "none",
              border: "none", color: C.primary, fontWeight: 600, cursor: "pointer", fontSize: 13, padding: 0 }}>{t("sage.auth.createOne")}</button>
          </p>
        )}
        {mode === "join" && (
          <p style={{ textAlign: "center", color: C.muted, fontSize: 12.5, marginTop: 14, marginBottom: 0 }}>
            {t("sage.auth.joinNote")}
          </p>
        )}
      </Card>
    </div>
  );
}

// --------------------------------------------------------------- Courses
function greetingKey() {
  const h = new Date().getHours();
  return h < 12 ? "morning" : h < 18 ? "afternoon" : "evening";
}

// Compact "Join code: XXXX  [Copy]" with clipboard feedback (used in the course row meta).
function JoinCodeInline({ code }: { code: string | null }) {
  const { t } = useTranslation();
  const [done, setDone] = useState(false);
  if (!code) return null;
  return (
    <>
      {" · "}{t("sage.joinCode")}{" "}
      <b style={{ color: C.accentInk, letterSpacing: 1 }}>{code}</b>{" "}
      <button type="button"
        onClick={(e) => { e.stopPropagation();
          navigator.clipboard?.writeText(code); setDone(true); setTimeout(() => setDone(false), 1500); }}
        style={{ display: "inline-flex", alignItems: "center", gap: 5, background: "#fff",
          border: `1px solid ${C.line}`, color: done ? C.success : C.accentInk, borderRadius: 7,
          padding: "3px 9px", fontSize: 12, fontWeight: 600, cursor: "pointer", verticalAlign: "middle" }}>
        <Icon name={done ? "check" : "copy"} size={13} />
        {done ? t("sage.copied") : t("sage.copy", { defaultValue: "Copy" })}
      </button>
    </>
  );
}

// A "⋮" overflow menu for a course row — keeps destructive actions out of the way (a cleaner
// pattern than a bare trash icon). Closes on outside-click or Escape.
function CourseMenu({ onRename, onDelete }: { onRename?: () => void; onDelete: () => void }) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false); };
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setOpen(false); };
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => { document.removeEventListener("mousedown", onDoc); document.removeEventListener("keydown", onKey); };
  }, [open]);
  return (
    <div ref={ref} style={{ position: "relative", flexShrink: 0 }}>
      <button type="button" aria-haspopup="menu" aria-expanded={open}
        aria-label={t("sage.courses.menu", { defaultValue: "Course options" })}
        onClick={(e) => { e.stopPropagation(); setOpen((o) => !o); }}
        style={{ background: open ? C.soft : "none", border: "none", cursor: "pointer",
          color: C.muted, display: "flex", alignItems: "center", padding: 6, borderRadius: 8 }}>
        <Icon name="dots" size={18} color={C.muted} />
      </button>
      {open && (
        <div role="menu" style={{ position: "absolute", insetInlineEnd: 0, top: "calc(100% + 4px)",
          background: "#fff", border: `1px solid ${C.line}`, borderRadius: 10, boxShadow: C.shadow,
          padding: 4, minWidth: 170, zIndex: 20 }}>
          {onRename && (
            <button type="button" role="menuitem"
              onClick={(e) => { e.stopPropagation(); setOpen(false); onRename(); }}
              style={{ display: "flex", alignItems: "center", gap: 9, width: "100%", textAlign: "start",
                background: "none", border: "none", cursor: "pointer", color: C.ink,
                padding: "9px 11px", borderRadius: 7, fontSize: 13.5, fontWeight: 500 }}>
              <Icon name="edit" size={15} color={C.muted} />
              {t("sage.courses.rename", { defaultValue: "Rename course" })}
            </button>
          )}
          <button type="button" role="menuitem"
            onClick={(e) => { e.stopPropagation(); setOpen(false); onDelete(); }}
            style={{ display: "flex", alignItems: "center", gap: 9, width: "100%", textAlign: "start",
              background: "none", border: "none", cursor: "pointer", color: C.danger,
              padding: "9px 11px", borderRadius: 7, fontSize: 13.5, fontWeight: 500 }}>
            <Icon name="trash" size={15} color={C.danger} />
            {t("sage.courses.delete", { defaultValue: "Delete course" })}
          </button>
        </div>
      )}
    </div>
  );
}

// Centered modal dialog (click-outside / Escape to close).
function Modal({ title, onClose, children }: { title: string; onClose: () => void; children: React.ReactNode }) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);
  return (
    <div onClick={onClose} style={{ position: "fixed", inset: 0, background: "rgba(20,20,40,.45)",
      display: "flex", alignItems: "center", justifyContent: "center", zIndex: 100, padding: 16 }}>
      <div onClick={(e) => e.stopPropagation()} role="dialog" aria-modal="true"
        style={{ background: "#fff", borderRadius: 16, boxShadow: C.shadow, width: "100%", maxWidth: 430,
          padding: 22, maxHeight: "90vh", overflowY: "auto" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
          <h3 style={{ margin: 0, fontSize: 18, color: C.ink }}>{title}</h3>
          <button onClick={onClose} aria-label="Close"
            style={{ background: "none", border: "none", cursor: "pointer", color: C.muted, fontSize: 22, lineHeight: 1 }}>×</button>
        </div>
        {children}
      </div>
    </div>
  );
}

// The Create-course / Join-course forms, in a dialog opened from the sidebar. `onDone` refreshes
// the course list on success.
function CourseDialog({ mode, onClose, onDone }: {
  mode: "create" | "join"; onClose: () => void; onDone: () => void;
}) {
  const { t } = useTranslation();
  const [tab, setTab] = useState<"create" | "join">(mode);
  const [name, setName] = useState(""); const [subject, setSubject] = useState(""); const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false); const [err, setErr] = useState<string | null>(null);
  async function submit(e: React.FormEvent) {
    e.preventDefault(); setErr(null);
    if (tab === "create" && !name.trim()) { setErr(t("sage.auth.errName")); return; }
    if (tab === "join" && !code.trim()) { setErr(t("sage.auth.errCode")); return; }
    setBusy(true);
    try {
      if (tab === "create") await sageApi.createCourse(name.trim(), subject.trim());
      else await sageApi.joinExisting(code.trim().toUpperCase());
      onDone(); onClose();
    } catch (e) { setErr((e as Error).message); } finally { setBusy(false); }
  }
  const tabBtn = (which: "create" | "join", label: string) => (
    <button type="button" onClick={() => { setTab(which); setErr(null); }}
      style={{ flex: 1, padding: "8px 10px", fontSize: 13.5, fontWeight: 600, cursor: "pointer",
        borderRadius: 9, border: `1px solid ${tab === which ? C.primary : C.line}`,
        background: tab === which ? C.primary : "#fff", color: tab === which ? "#fff" : C.muted }}>{label}</button>
  );
  return (
    <Modal title={t(tab === "create" ? "sage.courses.createTitle" : "sage.courses.joinTitle")} onClose={onClose}>
      <div style={{ display: "flex", gap: 6, marginBottom: 16 }}>
        {tabBtn("create", t("sage.courses.createTitle"))}
        {tabBtn("join", t("sage.courses.joinTitle"))}
      </div>
      <form onSubmit={submit} style={{ display: "grid", gap: 10 }}>
        {tab === "create" ? (
          <>
            <input style={inputStyle} placeholder={t("sage.courses.phName")} autoFocus
              value={name} onChange={(e) => setName(e.target.value)} />
            <input style={inputStyle} placeholder={t("sage.courses.phSubject")}
              value={subject} onChange={(e) => setSubject(e.target.value)} />
          </>
        ) : (
          <input style={inputStyle} placeholder={t("sage.courses.phJoin")} autoFocus
            value={code} onChange={(e) => setCode(e.target.value)} />
        )}
        <PrimaryBtn type="submit" disabled={busy}>
          {busy ? "…" : tab === "create"
            ? <><Icon name="plus" size={16} /> {t("sage.courses.createBtn")}</>
            : t("sage.courses.joinBtn")}
        </PrimaryBtn>
        {err && <div style={{ color: C.danger, fontSize: 13 }}>{err}</div>}
      </form>
    </Modal>
  );
}

// Rename dialog for a course (instructor-only). Prefilled with the current name.
function RenameCourseDialog({ course, onClose, onDone }: {
  course: SageCourseSummary; onClose: () => void; onDone: () => void;
}) {
  const { t } = useTranslation();
  const [name, setName] = useState(course.name);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) { setErr(t("sage.auth.errName")); return; }
    setBusy(true); setErr(null);
    try { await sageApi.renameCourse(course.id, name.trim()); onDone(); }
    catch (e) { setErr((e as Error).message); } finally { setBusy(false); }
  }
  return (
    <Modal title={t("sage.courses.rename", { defaultValue: "Rename course" })} onClose={onClose}>
      <form onSubmit={submit} style={{ display: "grid", gap: 12 }}>
        <input style={inputStyle} placeholder={t("sage.courses.phName")} autoFocus
          value={name} onChange={(e) => setName(e.target.value)} />
        <div style={{ display: "flex", gap: 8 }}>
          <PrimaryBtn type="submit" disabled={busy}>{t("sage.save", { defaultValue: "Save" })}</PrimaryBtn>
          <GhostBtn onClick={onClose}>{t("sage.cancel", { defaultValue: "Cancel" })}</GhostBtn>
        </div>
        {err && <div style={{ color: C.danger, fontSize: 13 }}>{err}</div>}
      </form>
    </Modal>
  );
}

// A labeled group of course cards ("Teaching" / "Enrolled as student"). The delete menu only
// appears when onDelete is provided (i.e. for courses you teach).
function CourseGroup({ label, count, courses, onOpen, onDelete, onRename }: {
  label: string; count: number; courses: SageCourseSummary[];
  onOpen: (c: SageCourseSummary) => void; onDelete?: (c: SageCourseSummary) => void;
  onRename?: (c: SageCourseSummary) => void;
}) {
  const { t } = useTranslation();
  return (
    <section style={{ marginBottom: 18 }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 8, margin: "2px 0 10px" }}>
        <h3 style={{ margin: 0, fontSize: 13, fontWeight: 700, color: C.muted,
          textTransform: "uppercase", letterSpacing: ".5px" }}>{label}</h3>
        <span style={{ fontSize: 12, fontWeight: 600, color: C.muted, background: C.soft,
          borderRadius: 999, padding: "1px 9px" }}>{count}</span>
      </div>
      <div style={{ display: "grid", gap: 12 }}>
        {courses.map((c) => (
          <Card key={c.id} style={{ cursor: "pointer", display: "flex", justifyContent: "space-between",
            alignItems: "center", gap: 12 }}>
            <div onClick={() => onOpen(c)} role="button" tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") { if (e.key === " ") e.preventDefault(); onOpen(c); }
              }}
              style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontWeight: 700, fontSize: 16.5 }}>{c.name}</div>
              <div style={{ color: C.muted, fontSize: 13, marginTop: 2 }}>
                {t("sage.courses.meta", { students: c.student_count, quizzes: c.quiz_count })}
                {c.role === "instructor" && <JoinCodeInline code={c.join_code} />}
              </div>
            </div>
            <button type="button" aria-label={t("sage.open", { defaultValue: "Open" })}
              onClick={(e) => { e.stopPropagation(); onOpen(c); }}
              style={{ background: "none", border: "none", cursor: "pointer", color: C.muted,
                display: "flex", alignItems: "center", padding: 6, flexShrink: 0 }}>
              <Icon name="arrow" color={C.muted} />
            </button>
            {onDelete && <CourseMenu onRename={onRename ? () => onRename(c) : undefined}
              onDelete={() => onDelete(c)} />}
          </Card>
        ))}
      </div>
    </section>
  );
}

function Courses({ onOpen, userName }: { onOpen: (c: SageCourseSummary) => void; userName: string }) {
  const { t } = useTranslation();
  const [courses, setCourses] = useState<SageCourseSummary[]>([]);
  const [msg, setMsg] = useState<string | null>(null);
  const [renaming, setRenaming] = useState<SageCourseSummary | null>(null);
  const load = () => sageApi.courses().then(setCourses).catch(() => setCourses([]));
  useEffect(() => { load(); }, []);

  const firstName = userName.trim().split(/\s+/)[0] || userName;
  // Roles are per-course: you can teach some courses and be enrolled as a student in others.
  const teaching = courses.filter((c) => c.role === "instructor");
  const enrolled = courses.filter((c) => c.role !== "instructor");
  const totalStudents = teaching.reduce((s, c) => s + (c.student_count || 0), 0);
  const totalQuizzes = teaching.reduce((s, c) => s + (c.quiz_count || 0), 0);

  async function removeCourse(c: SageCourseSummary) {
    if (!window.confirm(t("sage.courses.deleteConfirm", {
      defaultValue: "Delete “{{name}}” and everything in it (quizzes, results, roster)? This cannot be undone.",
      name: c.name,
    }))) return;
    try { await sageApi.deleteCourse(c.id); load(); }
    catch (e) { setMsg((e as Error).message); }
  }
  return (
    <div>
      <div style={{ marginBottom: 20 }}>
        <h1 style={{ margin: 0, fontSize: 24, color: C.ink }}>{t("sage.greeting." + greetingKey())}, {firstName}</h1>
        <p style={{ margin: "4px 0 0", color: C.muted, fontSize: 14.5 }}>
          {t("sage.courses.subtitle")}</p>
      </div>
      {teaching.length > 0 && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
          gap: 12, marginBottom: 20 }}>
          <Stat label={t("sage.stat.courses")} value={teaching.length} />
          <Stat label={t("sage.stat.students")} value={totalStudents} />
          <Stat label={t("sage.stat.quizzes")} value={totalQuizzes} />
        </div>
      )}
      <h2 style={{ color: C.ink, fontSize: 18, margin: "0 0 12px" }}>{t("sage.courses.title")}</h2>
      {courses.length === 0 && (
        <Card style={{ textAlign: "center", color: C.muted, background: C.soft, border: "none" }}>
          {t("sage.courses.empty")}
        </Card>
      )}
      {teaching.length > 0 && (
        <CourseGroup
          label={t("sage.courses.teaching", { defaultValue: "Teaching" })}
          count={teaching.length}
          courses={teaching} onOpen={onOpen} onDelete={removeCourse} onRename={setRenaming} />
      )}
      {renaming && (
        <RenameCourseDialog course={renaming} onClose={() => setRenaming(null)}
          onDone={() => { setRenaming(null); load(); }} />
      )}
      {enrolled.length > 0 && (
        <CourseGroup
          label={t("sage.courses.enrolled", { defaultValue: "Enrolled as student" })}
          count={enrolled.length}
          courses={enrolled} onOpen={onOpen} />
      )}
      {msg && <div style={{ color: C.danger, fontSize: 13, marginTop: 10 }}>{msg}</div>}
    </div>
  );
}

// --------------------------------------------------------------- Course shell
function CopyChip({ code }: { code: string | null }) {
  const { t } = useTranslation();
  const [done, setDone] = useState(false);
  if (!code) return null;
  return (
    <button onClick={() => { navigator.clipboard?.writeText(code); setDone(true); setTimeout(() => setDone(false), 1500); }}
      style={{ display: "inline-flex", alignItems: "center", gap: 7, background: C.accentBg, color: C.accentInk,
        border: "none", padding: "7px 13px", borderRadius: 999, fontSize: 13, cursor: "pointer" }}>
      <Icon name="key" size={15} /> {t("sage.joinCode")} <b style={{ letterSpacing: 1 }}>{code}</b>
      <Icon name={done ? "check" : "copy"} size={15} />{done && <span>{t("sage.copied")}</span>}
    </button>
  );
}

const TAB_ICON: Record<string, string> = {
  Home: "spark", Syllabus: "note", Materials: "file", Quizzes: "check",
  Assignments: "edit", Students: "school", Grades: "download",
  "Needs review": "alert", Analytics: "chart",
};

function CourseView({ course, tab, detail, reloadDetail }:
  { course: SageCourseSummary; tab: string; detail: SageCourseDetail | null; reloadDetail: () => void }) {
  const { t } = useTranslation();
  const instr = course.role === "instructor";
  return (
    <div style={{ minWidth: 0 }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between",
        flexWrap: "wrap", gap: 10, margin: "0 0 18px" }}>
        <h1 style={{ color: C.ink, margin: 0, fontSize: 23 }}>
          {tab === "Home" ? course.name : t(`sage.tab.${tab}`, { defaultValue: tab })}</h1>
        {instr && <CopyChip code={course.join_code} />}
      </div>
      {tab === "Home" && <Home course={course} instr={instr} detail={detail} />}
      {tab === "Syllabus" && <Syllabus course={course} instr={instr} detail={detail} onSaved={reloadDetail} />}
      {tab === "Materials" && <Materials course={course} instr={instr} />}
      {tab === "Quizzes" && (instr ? <QuizzesInstructor course={course} /> : <QuizzesStudent course={course} />)}
      {tab === "Assignments" && (instr ? <AssignmentsInstructor course={course} /> : <AssignmentsStudent course={course} />)}
      {tab === "Students" && <Students course={course} />}
      {tab === "Analytics" && <Analytics course={course} />}
      {tab === "Grades" && <GradesTab course={course} />}
      {tab === "Needs review" && <NeedsReview course={course} />}
    </div>
  );
}

// --------------------------------------------------------------- Analytics (real data)
function Analytics({ course }: { course: SageCourseSummary }) {
  const { t } = useTranslation();
  const [a, setA] = useState<InstructorAnalytics | null>(null);
  const [err, setErr] = useState(false);
  useEffect(() => { setA(null); setErr(false);
    api.analytics(course.id).then(setA).catch(() => setErr(true)); }, [course.id]);

  if (err) return (
    <Card><p style={{ margin: 0, color: C.muted }}>
      {t("sage.analytics.empty")}</p></Card>
  );
  if (!a) return <p style={{ color: C.muted }}>{t("sage.loading")}</p>;

  const risks = a.concept_risks;
  const avg = risks.length ? risks.reduce((s, r) => s + r.avg_mastery, 0) / risks.length : 0;
  const atRisk = risks.reduce((s, r) => Math.max(s, r.at_risk_count || 0), 0);
  const recovery = a.modules_generated ? a.modules_completed / a.modules_generated : 0;
  const pct = (v: number) => `${Math.round(v * 100)}%`;

  const tile = (value: string | number, label: string, tone?: "danger") => (
    <div style={{ background: "#fff", border: `1px solid ${C.line}`, borderRadius: 14,
      padding: "16px 18px", boxShadow: C.shadow }}>
      <div style={{ fontSize: 26, fontWeight: 800, lineHeight: 1.05,
        color: tone === "danger" ? C.danger : C.ink }}>{value}</div>
      <div style={{ fontSize: 12.5, marginTop: 5, color: C.muted }}>{label}</div>
    </div>
  );

  return (
    <div style={{ display: "grid", gap: 14 }}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: 12 }}>
        {tile(pct(avg), t("sage.analytics.avgMastery"))}
        {tile(a.enrolled_students, t("sage.analytics.students"))}
        {tile(a.modules_generated, t("sage.analytics.practiceSessions"))}
        {tile(atRisk, t("sage.analytics.atRisk"), atRisk > 0 ? "danger" : undefined)}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1.6fr 1fr", gap: 14 }}>
        <Card>
          <h3 style={{ marginTop: 0, fontSize: 16 }}>{t("sage.analytics.conceptMastery")}</h3>
          {risks.length === 0 && <p style={{ color: C.muted, margin: 0 }}>
            {t("sage.analytics.noConcepts")}</p>}
          {risks.map((r) => (
            <div key={r.concept_id} style={{ display: "flex", alignItems: "center", gap: 12,
              padding: "9px 0", borderTop: `1px solid ${C.line}` }}>
              <span style={{ flex: 1, minWidth: 0, fontSize: 13.5, whiteSpace: "nowrap",
                overflow: "hidden", textOverflow: "ellipsis" }}>{r.concept_name}</span>
              <Bar v={r.avg_mastery} width={150} />
              <b style={{ minWidth: 40, textAlign: "right", fontSize: 13.5,
                color: scoreColor(r.avg_mastery) }}>{pct(r.avg_mastery)}</b>
            </div>
          ))}
        </Card>
        <Card style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 10 }}>
          <h3 style={{ margin: 0, fontSize: 16, alignSelf: "flex-start" }}>{t("sage.analytics.practiceImpact")}</h3>
          <Donut v={recovery} size={128} />
          <div style={{ fontSize: 13, color: C.muted, textAlign: "center" }}>
            {t("sage.analytics.completedOf", { done: a.modules_completed, total: a.modules_generated })}
          </div>
        </Card>
      </div>
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
  const { t } = useTranslation();
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
  async function remove(id: number) {
    if (!window.confirm(t("sage.ann.deleteConfirm", { defaultValue: "Delete this announcement?" }))) return;
    try { await sageApi.deleteAnnouncement(id); load(); }
    catch (e) { window.alert((e as Error).message); }
  }
  return (
    <Card>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 8 }}>
        <h3 style={{ marginTop: 0, marginBottom: 0, fontSize: 17 }}>{t("sage.ann.title")}</h3>
        {instr && <GhostBtn onClick={() => setOpen((o) => !o)}>
          <Icon name="plus" size={15} /> {open ? t("sage.cancel") : t("sage.ann.post")}</GhostBtn>}
      </div>
      {open && (
        <div style={{ marginTop: 10, display: "grid", gap: 8 }}>
          <input style={inputStyle} placeholder={t("sage.ann.phTitle")} value={title} onChange={(e) => setTitle(e.target.value)} />
          <MarkdownEditor value={body} onChange={setBody} placeholder={t("sage.ann.phBody")}
            minHeight={90} ariaLabel={t("sage.ann.phBody")} />
          <div><PrimaryBtn onClick={post} disabled={busy}>{busy ? t("sage.ann.posting") : t("sage.ann.postBtn")}</PrimaryBtn></div>
        </div>
      )}
      <div style={{ marginTop: 12 }}>
        {items.length === 0 && <p style={{ color: C.muted, margin: 0 }}>{t("sage.ann.empty")}</p>}
        {items.map((a) => (
          <div key={a.id} style={{ padding: "10px 0", borderTop: `1px solid ${C.line}` }}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
              <b style={{ fontSize: 14.5 }}>{a.title}</b>
              <span style={{ display: "flex", gap: 8, alignItems: "center" }}>
                <span style={{ color: C.muted, fontSize: 12 }}>{fmtDateTime(a.created_at)}</span>
                {instr && <button onClick={() => remove(a.id)} title="Delete"
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
  const { t } = useTranslation();
  const ins = detail?.instructor;
  return (
    <div style={{ display: "grid", gap: 14 }}>
      {instr && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))", gap: 12 }}>
          <Stat label={t("sage.stat.students")} value={course.student_count} />
          <Stat label={t("sage.stat.quizzes")} value={course.quiz_count} />
        </div>
      )}
      <Announcements course={course} instr={instr} />
      {ins && (ins.title || ins.bio || ins.full_name) && (
        <Card style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
          <div style={{ width: 42, height: 42, borderRadius: "50%", background: C.accentBg, color: C.accentInk,
            display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700, flexShrink: 0 }}>
            {initials(ins.full_name)}</div>
          <div>
            <div style={{ fontSize: 12, color: C.muted }}>{t("sage.home.taughtBy")}</div>
            <div style={{ fontWeight: 700 }}>{ins.full_name}</div>
            {ins.title && <div style={{ fontSize: 13.5, color: C.accentInk }}>{ins.title}</div>}
            {ins.bio && <div style={{ fontSize: 13.5, color: "#444", marginTop: 4, lineHeight: 1.5 }}>{ins.bio}</div>}
          </div>
        </Card>
      )}
      <Card>
        <h3 style={{ marginTop: 0, fontSize: 17 }}>{t("sage.home.welcome", { name: course.name })}</h3>
        <p style={{ color: "#444", lineHeight: 1.6, margin: 0 }}>
          {instr ? t("sage.home.instrBlurb", { code: course.join_code }) : t("sage.home.studentBlurb")}
        </p>
      </Card>
    </div>
  );
}

// Read-only preview of a quiz for the instructor: questions, choices with the correct one(s)
// marked, accepted answers for short questions, and each question's concept tag.
function QuizPreview({ quiz, onClose }: { quiz: SageQuizForEdit; onClose: () => void }) {
  const { t } = useTranslation();
  return (
    <Modal title={quiz.title} onClose={onClose}>
      {quiz.due_at && (
        <div style={{ color: C.muted, fontSize: 13, marginBottom: 12 }}>
          {t("sage.quiz.due", { date: fmtDateTime(quiz.due_at) })}</div>
      )}
      <div style={{ display: "grid", gap: 14 }}>
        {quiz.questions.map((q, i) => (
          <div key={i} style={{ border: `1px solid ${C.line}`, borderRadius: 10, padding: 12 }}>
            <div style={{ display: "flex", gap: 8, alignItems: "baseline", marginBottom: 8 }}>
              <span style={{ fontWeight: 700, color: C.muted, fontSize: 13, flexShrink: 0 }}>Q{i + 1}</span>
              <span style={{ fontWeight: 600 }}>
                {q.prompt || <em style={{ color: C.muted }}>—</em>}</span>
            </div>
            {q.qtype === "short" ? (
              <div style={{ fontSize: 13.5 }}>
                <span style={{ color: C.muted }}>
                  {t("sage.quiz.acceptedLabel", { defaultValue: "Accepted answers:" })} </span>
                <b>{q.correct.join(" · ") || "—"}</b>
              </div>
            ) : (
              <div style={{ display: "grid", gap: 5 }}>
                {(q.qtype === "true_false" ? ["True", "False"] : q.choices).map((c, ci) => {
                  const ok = q.correct.includes(c);
                  return (
                    <div key={ci} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 14,
                      padding: "6px 10px", borderRadius: 8,
                      background: ok ? C.successBg : "transparent",
                      border: `1px solid ${ok ? C.success : C.line}` }}>
                      {ok ? <Icon name="check" size={15} color={C.success} />
                        : <span style={{ width: 15, flexShrink: 0 }} />}
                      <span style={{ color: ok ? C.success : C.ink, fontWeight: ok ? 600 : 400 }}>
                        {q.qtype === "true_false" ? tfLabel(q.qtype, c, t) : c}</span>
                    </div>
                  );
                })}
              </div>
            )}
            {q.concept && (
              <div style={{ marginTop: 9 }}>
                <span style={{ fontSize: 12, fontWeight: 600, background: C.accentBg, color: C.accentInk,
                  padding: "3px 10px", borderRadius: 999 }}>{q.concept}</span>
              </div>
            )}
          </div>
        ))}
      </div>
    </Modal>
  );
}

// --------------------------------------------------------------- Quizzes (instructor)
function QuizzesInstructor({ course }: { course: SageCourseSummary }) {
  const { t } = useTranslation();
  const [quizzes, setQuizzes] = useState<SageQuizListItem[]>([]);
  const [build, setBuild] = useState(false);
  const [editId, setEditId] = useState<number | null>(null);
  const [initial, setInitial] = useState<
    { title: string; questions: SageQuestionDraft[]; due_at?: string | null; locked?: boolean } | null>(null);
  const [preview, setPreview] = useState<SageQuizForEdit | null>(null);
  const load = () => sageApi.quizzes(course.id).then(setQuizzes).catch(() => setQuizzes([]));
  useEffect(() => { load(); }, [course.id]);

  function startNew() { setInitial(null); setEditId(null); setBuild(true); }
  function openPreview(id: number) {
    sageApi.quizForEdit(id).then(setPreview).catch((e) => window.alert((e as Error).message));
  }
  async function startEdit(id: number) {
    const q = await sageApi.quizForEdit(id);
    setInitial({ title: q.title, questions: q.questions, due_at: q.due_at, locked: q.has_submissions });
    setEditId(id); setBuild(true);
  }
  async function dup(id: number) {
    if (!window.confirm(t("sage.quiz.duplicateConfirm", { defaultValue: "Duplicate this quiz?" }))) return;
    try { await sageApi.duplicateQuiz(id); load(); }
    catch (e) { window.alert((e as Error).message); }
  }
  async function del(id: number) {
    if (!window.confirm(t("sage.quiz.deleteConfirm"))) return;
    await sageApi.deleteQuiz(id); load();
  }
  return (
    <div style={{ display: "grid", gap: 12 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h3 style={{ margin: 0, fontSize: 17 }}>{t("sage.tab.Quizzes")}</h3>
        {!build && <PrimaryBtn onClick={startNew}><Icon name="plus" size={16} /> {t("sage.quiz.new")}</PrimaryBtn>}
      </div>
      {build && <QuizBuilder courseId={course.id} editId={editId} initial={initial}
        onCancel={() => setBuild(false)} onDone={() => { setBuild(false); load(); }} />}
      {quizzes.length === 0 && !build && (
        <Card style={{ textAlign: "center", color: C.muted, background: C.soft, border: "none" }}>
          {t("sage.quiz.empty")}
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
                  {t("sage.quiz.metaInstr", { questions: q.question_count, submitted: q.submission_count ?? 0 })}
                  {q.due_at && <> · {t("sage.quiz.due", { date: fmtDateTime(q.due_at) })}</>}</div>
              </div>
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                <GhostBtn onClick={() => openPreview(q.id)}><Icon name="eye" size={15} /> {t("sage.quiz.preview", { defaultValue: "Preview" })}</GhostBtn>
                <GhostBtn onClick={() => startEdit(q.id)}><Icon name="edit" size={15} /> {t("sage.quiz.edit")}</GhostBtn>
                <GhostBtn onClick={() => dup(q.id)}><Icon name="copy" size={15} /> {t("sage.quiz.duplicate")}</GhostBtn>
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
      {preview && <QuizPreview quiz={preview} onClose={() => setPreview(null)} />}
    </div>
  );
}

const QTYPE_LABELS: { value: SageQType; label: string }[] = [
  { value: "mcq", label: "Multiple choice" },
  { value: "true_false", label: "True / False" },
  { value: "multi", label: "Multiple answers" },
  { value: "short", label: "Short answer" },
];

// True/False options are stored canonically as "True"/"False" (grading depends on it); only the
// DISPLAYED label is localized. Any other stored value is shown as-is.
function tfLabel(qtype: string, c: string, tr: (k: string) => string): string {
  if (qtype !== "true_false") return c;
  if (c === "True") return tr("sage.quiz.true");
  if (c === "False") return tr("sage.quiz.false");
  return c;
}

function QuizBuilder({ courseId, editId, initial, onDone, onCancel }: {
  courseId: number; editId: number | null;
  initial: { title: string; questions: SageQuestionDraft[]; due_at?: string | null; locked?: boolean } | null;
  onDone: () => void; onCancel: () => void;
}) {
  const { t } = useTranslation();
  const locked = !!initial?.locked;
  const blank = (): SageQuestionDraft =>
    ({ prompt: "", qtype: "mcq", choices: ["", ""], correct: [], concept: "" });
  const [title, setTitle] = useState(initial?.title || "");
  const [dueAt, setDueAt] = useState(toLocalInput(initial?.due_at));
  const [qs, setQs] = useState<SageQuestionDraft[]>(
    initial?.questions?.length ? initial.questions : [blank()]);
  const [err, setErr] = useState<string | null>(null); const [busy, setBusy] = useState(false);
  // Concepts already used in this course -> autocomplete; and per-question AI-suggest state.
  const [conceptOpts, setConceptOpts] = useState<string[]>([]);
  const [suggesting, setSuggesting] = useState<number | null>(null);
  useEffect(() => { sageApi.courseConcepts(courseId).then(setConceptOpts).catch(() => setConceptOpts([])); },
    [courseId]);

  async function suggestConcept(i: number) {
    const q = qs[i];
    if (!q.prompt.trim() || suggesting != null) return;
    setSuggesting(i);
    try {
      const choices = q.qtype === "short" ? [] : q.choices.filter(Boolean);
      const { concept } = await sageApi.suggestConcept(courseId, q.prompt.trim(), choices);
      if (concept) {
        upd(i, { concept });
        setConceptOpts((prev) => prev.includes(concept) ? prev : [...prev, concept]);
      } else {
        window.alert(t("sage.quiz.suggestNone", { defaultValue: "Couldn't suggest a concept — please type one." }));
      }
    } catch (e) { window.alert((e as Error).message); } finally { setSuggesting(null); }
  }

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
    if (!title.trim()) { setErr(t("sage.quiz.errTitle")); return; }
    const payload: SageQuestionDraft[] = [];
    for (const q of qs) {
      if (!q.prompt.trim() || !q.concept.trim()) { setErr(t("sage.quiz.errPromptConcept")); return; }
      let choices = q.choices.map((c) => c.trim()).filter(Boolean);
      let correct = q.correct.map((c) => c.trim()).filter(Boolean);
      if (q.qtype === "true_false") choices = ["True", "False"];
      if (q.qtype === "short") { choices = []; if (!correct.length) { setErr(t("sage.quiz.errShort", { p: q.prompt })); return; } }
      else {
        if (choices.length < 2) { setErr(t("sage.quiz.errChoices", { p: q.prompt })); return; }
        correct = correct.filter((c) => choices.includes(c));
        if ((q.qtype === "mcq" || q.qtype === "true_false") && correct.length !== 1) {
          setErr(t("sage.quiz.errOne", { p: q.prompt })); return;
        }
        if (q.qtype === "multi" && correct.length < 1) { setErr(t("sage.quiz.errMulti", { p: q.prompt })); return; }
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
      {locked && (
        <div style={{ background: C.infoBg, color: C.info, borderRadius: 10, padding: "10px 14px",
          marginBottom: 12, fontSize: 13.5, lineHeight: 1.5, display: "flex", alignItems: "flex-start", gap: 8 }}>
          <Icon name="alert" size={18} />
          <span>{t("sage.quiz.editLocked", { defaultValue: "This quiz already has submissions, so its questions are locked to keep past attempts consistent. You can still edit the title and due date — or use Duplicate to make an editable copy." })}</span>
        </div>
      )}
      <datalist id="sage-concept-list">
        {conceptOpts.map((c) => <option key={c} value={c} />)}
      </datalist>
      <input style={{ ...inputStyle, marginBottom: 10, fontWeight: 600 }} placeholder={t("sage.quiz.phTitle")}
        value={title} onChange={(e) => setTitle(e.target.value)} />
      <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 14, flexWrap: "wrap" }}>
        <label style={{ fontSize: 13, color: C.muted }}>{t("sage.quiz.dueDate")}</label>
        <input type="datetime-local" style={{ ...inputStyle, width: "auto" }} value={dueAt}
          onChange={(e) => setDueAt(e.target.value)} />
        {dueAt && <GhostBtn onClick={() => setDueAt("")}>{t("sage.quiz.clear")}</GhostBtn>}
      </div>
      {locked ? (
        qs.map((q, i) => (
          <div key={i} style={{ background: "#fff", border: `1px solid ${C.line}`, borderRadius: 12,
            padding: 14, marginBottom: 10 }}>
            <div style={{ display: "flex", gap: 8, marginBottom: 6, alignItems: "baseline" }}>
              <span style={{ fontSize: 13, color: C.muted, fontWeight: 600 }}>Q{i + 1}</span>
              <span style={{ fontSize: 14.5, fontWeight: 600 }}>{q.prompt}</span>
            </div>
            {q.qtype === "short" ? (
              <div style={{ fontSize: 13.5, color: C.muted }}>
                {t("sage.quiz.correctAns", { ans: q.correct.join(" / ") })}</div>
            ) : (
              <div style={{ display: "grid", gap: 4 }}>
                {(q.qtype === "true_false" ? ["True", "False"] : q.choices).map((c, ci) => {
                  const isCorrect = q.correct.includes(c);
                  return (
                    <div key={ci} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 14,
                      color: isCorrect ? C.success : C.ink }}>
                      <Icon name={isCorrect ? "check" : "circle"} size={15}
                        color={isCorrect ? C.success : "#b9b4cf"} />
                      <span>{tfLabel(q.qtype, c, t)}</span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        ))
      ) : qs.map((q, i) => (
        <div key={i} style={{ background: "#fff", border: `1px solid ${C.line}`, borderRadius: 12, padding: 14, marginBottom: 10 }}>
          <div style={{ display: "flex", gap: 8, marginBottom: 8, alignItems: "center" }}>
            <span style={{ fontSize: 13, color: C.muted, fontWeight: 600 }}>Q{i + 1}</span>
            <select value={q.qtype} onChange={(e) => setType(i, e.target.value as SageQType)}
              style={{ ...inputStyle, width: "auto", padding: "7px 10px" }}>
              {QTYPE_LABELS.map((qt) => <option key={qt.value} value={qt.value}>{t("sage.qtype." + qt.value)}</option>)}
            </select>
            {qs.length > 1 && <button onClick={() => setQs((a) => a.filter((_, j) => j !== i))}
              title={t("sage.quiz.removeQ")} style={{ marginLeft: "auto", background: "none", border: "none",
                color: C.danger, cursor: "pointer" }}><Icon name="trash" size={15} /></button>}
          </div>
          <input style={{ ...inputStyle, marginBottom: 8 }} placeholder={t("sage.quiz.phPrompt")}
            value={q.prompt} onChange={(e) => upd(i, { prompt: e.target.value })} />

          {q.qtype === "short" ? (
            <>
              <textarea style={{ ...inputStyle, minHeight: 64, resize: "vertical", fontFamily: "inherit" }}
                placeholder={t("sage.quiz.phShortAns")}
                value={q.correct.join("\n")}
                onChange={(e) => upd(i, { correct: e.target.value.split("\n").map((s) => s.trim()) })} />
              <div style={{ fontSize: 12, color: C.muted, marginTop: 4 }}>
                {t("sage.quiz.acceptedHint", { defaultValue: "One accepted answer per line — all are matched case-insensitively." })}</div>
            </>
          ) : (
            <>
              <div style={{ fontSize: 12, color: C.muted, marginBottom: 6 }}>
                {q.qtype === "multi" ? t("sage.quiz.checkAll") : t("sage.quiz.selectOne")}</div>
              {(q.qtype === "true_false" ? ["True", "False"] : q.choices).map((c, ci) => (
                <div key={ci} style={{ display: "flex", gap: 9, alignItems: "center", marginBottom: 6 }}>
                  <input type={q.qtype === "multi" ? "checkbox" : "radio"} name={`correct-${i}`}
                    checked={q.correct.includes(c) && !!c}
                    onChange={() => toggleCorrect(i, c, q.qtype !== "multi")}
                    style={{ accentColor: C.primary }} title={t("sage.quiz.markCorrect")} />
                  {q.qtype === "true_false"
                    ? <span style={{ fontSize: 14 }}>{tfLabel(q.qtype, c, t)}</span>
                    : <input style={inputStyle} placeholder={t("sage.quiz.choiceN", { n: ci + 1 })} value={c}
                        onChange={(e) => setChoice(i, ci, e.target.value)} />}
                </div>
              ))}
              {q.qtype !== "true_false" && (
                <GhostBtn onClick={() => upd(i, { choices: [...q.choices, ""] })}>{t("sage.quiz.addChoice")}</GhostBtn>
              )}
            </>
          )}
          <div style={{ display: "flex", gap: 8, marginTop: 8, alignItems: "stretch", flexWrap: "wrap" }}>
            <input style={{ ...inputStyle, flex: "1 1 200px", marginTop: 0 }}
              placeholder={t("sage.quiz.phConcept")} list="sage-concept-list"
              value={q.concept} onChange={(e) => upd(i, { concept: e.target.value })} />
            <GhostBtn onClick={() => suggestConcept(i)}
              disabled={suggesting != null || !q.prompt.trim()}>
              {suggesting === i
                ? t("sage.quiz.suggesting", { defaultValue: "Suggesting…" })
                : t("sage.quiz.suggestConcept", { defaultValue: "✨ Suggest" })}
            </GhostBtn>
          </div>
          <div style={{ fontSize: 12, color: C.muted, marginTop: 4 }}>
            {t("sage.quiz.conceptHint", { defaultValue: "The topic this question tests (e.g. “Binary arithmetic”). When a student gets it wrong, LMS Bridge uses this to build them targeted practice on that exact topic. Tap ✨ Suggest to have LMS Bridge infer it from the question, or start typing to reuse a concept already used in this course." })}
          </div>
        </div>
      ))}
      <div style={{ display: "flex", gap: 8, marginTop: 6, flexWrap: "wrap" }}>
        {!locked && <GhostBtn onClick={() => setQs((a) => [...a, blank()])}><Icon name="plus" size={15} /> {t("sage.quiz.addQ")}</GhostBtn>}
        <PrimaryBtn onClick={save} disabled={busy}>{busy ? t("sage.quiz.saving") : editId != null ? t("sage.quiz.saveChanges") : t("sage.quiz.saveQuiz")}</PrimaryBtn>
        <GhostBtn onClick={onCancel}>{t("sage.cancel")}</GhostBtn>
      </div>
      {err && <div style={{ color: C.danger, fontSize: 13, marginTop: 8 }}>{err}</div>}
    </Card>
  );
}

// --------------------------------------------------------------- Quizzes (student)
function QuizzesStudent({ course }: { course: SageCourseSummary }) {
  const { t } = useTranslation();
  const [quizzes, setQuizzes] = useState<SageQuizListItem[]>([]);
  const [taking, setTaking] = useState<SageTakeQuiz | null>(null);
  const [result, setResult] = useState<SageSubmitResult | null>(null);
  const [answers, setAnswers] = useState<Record<number, { choice?: string; choices?: string[] }>>({});
  const [busy, setBusy] = useState(false);
  const load = () => sageApi.quizzes(course.id).then(setQuizzes).catch(() => setQuizzes([]));
  useEffect(() => { load(); }, [course.id]);

  async function open(id: number) {
    setResult(null); setAnswers({});
    try { setTaking(await sageApi.takeQuiz(id)); }
    catch (e) { window.alert((e as Error).message); }
  }
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
    if (!taking || busy) return;
    const payload: SageAnswerIn[] = taking.questions.map((q) => ({ question_id: q.id, ...answers[q.id] }));
    setBusy(true);
    try { setResult(await sageApi.submitQuiz(taking.id, payload)); load(); }
    catch (e) { window.alert((e as Error).message); }
    finally { setBusy(false); }
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
            <div style={{ color: C.muted, fontSize: 14 }}>{t("sage.quiz.gotCorrect", { correct: result.correct, total: result.total })}</div>
          </div>
        </div>
        {result.remediation_created > 0 && (
          <div style={{ background: C.infoBg, color: C.info, borderRadius: 10, padding: "10px 14px",
            marginTop: 14, fontSize: 14, display: "flex", alignItems: "center", gap: 8 }}>
            <Icon name="spark" size={18} /> {t("sage.quiz.practiceReady")}</div>
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
                  {!r?.is_correct && <div style={{ fontSize: 13, color: C.muted }}>{t("sage.quiz.correctAns", { ans: r?.correct })}</div>}
                </div>
              </div>
            );
          })}
        </div>
        <GhostBtn onClick={() => setTaking(null)}><Icon name="back" size={16} /> {t("sage.quiz.backToQuizzes")}</GhostBtn>
      </Card>
    );
  }
  if (taking) {
    const answered = taking.questions.filter((q) => isAnswered(q.id)).length;
    return (
      <Card>
        <h3 style={{ marginTop: 0, fontSize: 17 }}>{taking.title}</h3>
        <div style={{ fontSize: 13, color: C.muted, marginBottom: 6 }}>{t("sage.quiz.answered", { answered, total: taking.questions.length })}</div>
        {taking.questions.map((q, i) => (
          <div key={q.id} style={{ padding: "12px 0", borderTop: `1px solid ${C.line}` }}>
            <div style={{ fontWeight: 600, fontSize: 14.5, marginBottom: 8 }}>
              {i + 1}. {q.prompt}
              {q.qtype === "multi" && <span style={{ color: C.muted, fontWeight: 400, fontSize: 12 }}> {t("sage.quiz.selectAll")}</span>}
            </div>
            {q.qtype === "short" ? (
              <input style={inputStyle} placeholder={t("sage.quiz.phAnswer")} value={answers[q.id]?.choice || ""}
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
                    style={{ accentColor: C.primary }} />{tfLabel(q.qtype, c, t)}
                </label>
              );
            }))}
          </div>
        ))}
        <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
          <GhostBtn onClick={() => setTaking(null)}>{t("sage.cancel")}</GhostBtn>
          <PrimaryBtn onClick={submit} disabled={busy}>
            {busy ? t("sage.quiz.submitting", { defaultValue: "Submitting…" }) : t("sage.quiz.submit")}</PrimaryBtn>
        </div>
      </Card>
    );
  }
  return (
    <div style={{ display: "grid", gap: 12 }}>
      <h3 style={{ margin: 0, fontSize: 17 }}>{t("sage.tab.Quizzes")}</h3>
      {quizzes.length === 0 && (
        <Card style={{ textAlign: "center", color: C.muted, background: C.soft, border: "none" }}>
          {t("sage.quiz.studentEmpty")}</Card>
      )}
      {quizzes.map((q) => {
        const taken = q.my_score != null;
        return (
          <Card key={q.id} style={{ display: "grid", gap: 10 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 11 }}>
                <Icon name={taken ? "check" : "circle"} size={22} color={taken ? C.success : "#b9b4cf"} />
                <div>
                  <b style={{ fontSize: 15 }}>{q.title}</b>
                  <div style={{ color: C.muted, fontSize: 13 }}>
                    {t("sage.quiz.questions", { count: q.question_count })}
                    {taken && <> · {t("sage.quiz.yourScore")} <b style={{ color: C.success }}>{Math.round((q.my_score || 0) * 100)}%</b></>}
                    {q.due_at && (() => {
                      const overdue = new Date(q.due_at) < new Date();
                      return <span style={{ color: overdue && !taken ? C.danger : C.muted }}>
                        {" · "}{overdue ? t("sage.quiz.wasDue") : t("sage.quiz.dueLabel")} {fmtDateTime(q.due_at)}</span>;
                    })()}
                  </div>
                </div>
              </div>
              <PrimaryBtn onClick={() => open(q.id)}>{taken ? t("sage.quiz.retake") : t("sage.quiz.take")}</PrimaryBtn>
            </div>
            {taken && <AttemptsPanel quizId={q.id} />}
          </Card>
        );
      })}
    </div>
  );
}

// Lazy-loaded per-quiz panel showing the student's own past attempts and their review.
function AttemptsPanel({ quizId }: { quizId: number }) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [attempts, setAttempts] = useState<SageQuizAttempt[]>([]);
  const [expanded, setExpanded] = useState<Record<number, boolean>>({});

  function toggle() {
    const next = !open;
    setOpen(next);
    if (next && !loaded && !loading) {
      setLoading(true);
      sageApi.quizAttempts(quizId)
        .then((a) => { setAttempts(a); setLoaded(true); })
        .catch(() => setAttempts([]))
        .finally(() => setLoading(false));
    }
  }
  return (
    <div>
      <GhostBtn onClick={toggle}>
        <Icon name="chart" size={15} /> {t("sage.quiz.pastAttempts", { defaultValue: "Past attempts" })}</GhostBtn>
      {open && (
        <div style={{ marginTop: 10, borderTop: `1px solid ${C.line}`, paddingTop: 10 }}>
          <h4 style={{ margin: "0 0 8px", fontSize: 14 }}>{t("sage.quiz.attemptsTitle", { defaultValue: "Your attempts" })}</h4>
          {loading && <p style={{ color: C.muted, margin: 0, fontSize: 13.5 }}>{t("sage.loading")}</p>}
          {!loading && attempts.length === 0 && (
            <p style={{ color: C.muted, margin: 0, fontSize: 13.5 }}>
              {t("sage.quiz.noAttempts", { defaultValue: "No attempts yet." })}</p>
          )}
          {!loading && attempts.map((a) => {
            const isOpen = !!expanded[a.id];
            return (
              <div key={a.id} style={{ borderTop: `1px solid ${C.line}`, padding: "8px 0" }}>
                <button onClick={() => setExpanded((m) => ({ ...m, [a.id]: !m[a.id] }))}
                  style={{ display: "flex", alignItems: "center", gap: 10, width: "100%", textAlign: "start",
                    background: "none", border: "none", cursor: "pointer", padding: 0, color: C.ink }}>
                  <Icon name="arrow" size={16} color={C.muted} />
                  <span style={{ fontSize: 13.5, color: C.muted }}>
                    {a.submitted_at ? new Date(a.submitted_at).toLocaleString() : "—"}</span>
                  <b style={{ fontSize: 14, color: scoreColor(a.score), marginInlineStart: "auto" }}>
                    {Math.round(a.score * 100)}%</b>
                  <span style={{ fontSize: 13, color: C.muted }}>{a.correct}/{a.total}</span>
                </button>
                {isOpen && (
                  <div style={{ marginTop: 8, display: "grid", gap: 8 }}>
                    {a.review.map((r, ri) => (
                      <div key={ri} style={{ display: "flex", gap: 9, alignItems: "flex-start" }}>
                        <Icon name={r.is_correct ? "check" : "alert"} size={16}
                          color={r.is_correct ? C.success : C.danger} />
                        <div style={{ fontSize: 13.5 }}>
                          <div style={{ fontWeight: 500 }}>{r.question}</div>
                          <div style={{ color: C.muted }}>
                            {t("sage.quiz.yourAnswer", { defaultValue: "Your answer: {{ans}}", ans: r.selected ?? "—" })}</div>
                          <div style={{ color: C.muted }}>
                            {t("sage.quiz.correctAns", { ans: r.correct })}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// A styled "button-like" label used for the hidden file <input> in submissions.
const ghostLike: React.CSSProperties = {
  background: "#fff", color: C.ink, border: `1px solid ${C.line}`, borderRadius: 10,
  padding: "8px 14px", fontSize: 14, display: "inline-flex", alignItems: "center", gap: 6,
};

function fmtBytes(n?: number) {
  if (!n) return "";
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${Math.round(n / 1024)} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

// Downloads a submission's file attachment (works for the student who owns it and the instructor).
function AttachmentLink({ sub }: { sub: SageSubmission }) {
  const { t } = useTranslation();
  if (!sub.has_file) return null;
  return (
    <button onClick={() => sageApi.downloadSubmissionFile(sub.id, sub.file_name || "attachment")}
      style={{ background: "none", border: "none", cursor: "pointer", color: C.primary, padding: 0,
        display: "inline-flex", alignItems: "center", gap: 6, fontSize: 13.5 }}
      title={t("sage.asg.download", { defaultValue: "Download attachment" })}>
      <Icon name="download" size={15} /> {sub.file_name}
      {sub.file_size ? <span style={{ color: C.muted }}>({fmtBytes(sub.file_size)})</span> : null}
    </button>
  );
}

// --------------------------------------------------------------- Assignments (instructor)
function AssignmentsInstructor({ course }: { course: SageCourseSummary }) {
  const { t } = useTranslation();
  const [items, setItems] = useState<SageAssignment[]>([]);
  const [form, setForm] = useState<SageAssignment | "new" | null>(null);
  const [grading, setGrading] = useState<number | null>(null);
  const load = () => sageApi.assignments(course.id).then(setItems).catch(() => setItems([]));
  useEffect(() => { load(); }, [course.id]);

  async function del(id: number) {
    if (!window.confirm(t("sage.asg.deleteConfirm", { defaultValue: "Delete this assignment and all its submissions?" }))) return;
    try { await sageApi.deleteAssignment(id); load(); }
    catch (e) { window.alert((e as Error).message); }
  }

  if (grading != null) {
    const a = items.find((x) => x.id === grading);
    return <GradingView assignmentId={grading} title={a?.title || ""}
      onBack={() => { setGrading(null); load(); }} />;
  }
  if (form) {
    return <AssignmentForm courseId={course.id} initial={form === "new" ? null : form}
      onCancel={() => setForm(null)} onDone={() => { setForm(null); load(); }} />;
  }

  return (
    <div style={{ display: "grid", gap: 12 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h3 style={{ margin: 0, fontSize: 17 }}>{t("sage.tab.Assignments", { defaultValue: "Assignments" })}</h3>
        <PrimaryBtn onClick={() => setForm("new")}><Icon name="plus" size={16} /> {t("sage.asg.new", { defaultValue: "New assignment" })}</PrimaryBtn>
      </div>
      {items.length === 0 && (
        <Card style={{ textAlign: "center", color: C.muted, background: C.soft, border: "none" }}>
          {t("sage.asg.empty", { defaultValue: "No assignments yet. Create one for your students to submit." })}
        </Card>
      )}
      {items.map((a) => {
        const total = a.submission_count ?? 0;
        const graded = a.graded_count ?? 0;
        const pct = course.student_count ? Math.round((total / course.student_count) * 100) : 0;
        return (
          <Card key={a.id}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
              <div>
                <b style={{ fontSize: 15 }}>{a.title}</b>
                <div style={{ color: C.muted, fontSize: 13 }}>
                  {t("sage.asg.metaInstr", { defaultValue: "{{points}} pts · {{submitted}} submitted · {{graded}} graded",
                    points: a.points, submitted: total, graded })}
                  {a.due_at && <> · {t("sage.quiz.due", { date: fmtDateTime(a.due_at) })}</>}
                </div>
              </div>
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                <GhostBtn onClick={() => setGrading(a.id)}><Icon name="check" size={15} /> {t("sage.asg.review", { defaultValue: "Submissions" })}</GhostBtn>
                <GhostBtn onClick={() => setForm(a)}><Icon name="edit" size={15} /> {t("sage.quiz.edit")}</GhostBtn>
                <button onClick={() => del(a.id)} title="Delete" style={{ background: "none", border: "none",
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

function AssignmentForm({ courseId, initial, onCancel, onDone }: {
  courseId: number; initial: SageAssignment | null; onCancel: () => void; onDone: () => void;
}) {
  const { t } = useTranslation();
  const [title, setTitle] = useState(initial?.title || "");
  const [points, setPoints] = useState(initial?.points ?? 100);
  const [dueAt, setDueAt] = useState(toLocalInput(initial?.due_at));
  const [instructions, setInstructions] = useState(initial?.instructions || "");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function save() {
    if (!title.trim()) { setErr(t("sage.asg.errTitle", { defaultValue: "Give the assignment a title." })); return; }
    setBusy(true); setErr(null);
    const payload = { title: title.trim(), instructions, points: Number(points) || 0,
      due_at: dueAt ? new Date(dueAt).toISOString() : null };
    try {
      if (initial) await sageApi.updateAssignment(initial.id, payload);
      else await sageApi.createAssignment(courseId, payload);
      onDone();
    } catch (e) { setErr((e as Error).message); } finally { setBusy(false); }
  }

  return (
    <Card>
      <h3 style={{ marginTop: 0, fontSize: 17 }}>
        {initial ? t("sage.asg.editTitle", { defaultValue: "Edit assignment" }) : t("sage.asg.new", { defaultValue: "New assignment" })}</h3>
      {err && <div style={{ color: C.danger, marginBottom: 10, fontSize: 13.5 }}>{err}</div>}
      <input style={{ ...inputStyle, marginBottom: 10, fontWeight: 600 }}
        placeholder={t("sage.asg.phTitle", { defaultValue: "Assignment title" })}
        value={title} onChange={(e) => setTitle(e.target.value)} />
      <div style={{ display: "flex", gap: 14, alignItems: "center", marginBottom: 12, flexWrap: "wrap" }}>
        <label style={{ fontSize: 13, color: C.muted, display: "inline-flex", alignItems: "center", gap: 7 }}>
          {t("sage.asg.points", { defaultValue: "Points" })}
          <input type="number" min={0} max={1000} value={points}
            onChange={(e) => setPoints(Number(e.target.value))}
            style={{ ...inputStyle, width: 90 }} />
        </label>
        <label style={{ fontSize: 13, color: C.muted, display: "inline-flex", alignItems: "center", gap: 7 }}>
          {t("sage.quiz.dueDate")}
          <input type="datetime-local" style={{ ...inputStyle, width: "auto" }} value={dueAt}
            onChange={(e) => setDueAt(e.target.value)} />
        </label>
        {dueAt && <GhostBtn onClick={() => setDueAt("")}>{t("sage.quiz.clear")}</GhostBtn>}
      </div>
      <label style={{ fontSize: 13, color: C.muted, display: "block", marginBottom: 6 }}>
        {t("sage.asg.instructions", { defaultValue: "Instructions" })}</label>
      <MarkdownEditor value={instructions} onChange={setInstructions} minHeight={160}
        placeholder={t("sage.asg.phInstructions", { defaultValue: "Describe what students should do…" })} />
      <div style={{ display: "flex", gap: 8, marginTop: 14 }}>
        <PrimaryBtn onClick={save} disabled={busy}>{t("sage.save", { defaultValue: "Save" })}</PrimaryBtn>
        <GhostBtn onClick={onCancel}>{t("sage.cancel", { defaultValue: "Cancel" })}</GhostBtn>
      </div>
    </Card>
  );
}

function GradingView({ assignmentId, title, onBack }: {
  assignmentId: number; title: string; onBack: () => void;
}) {
  const { t } = useTranslation();
  const [view, setView] = useState<SageSubmissionsView | null>(null);
  const load = () => sageApi.submissions(assignmentId).then(setView).catch(() => setView(null));
  useEffect(() => { load(); }, [assignmentId]);

  const points = view?.assignment.points ?? 100;
  return (
    <div style={{ display: "grid", gap: 12 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <GhostBtn onClick={onBack}><Icon name="back" size={16} /> {t("sage.asg.back", { defaultValue: "Back to assignments" })}</GhostBtn>
        <h3 style={{ margin: 0, fontSize: 17 }}>{title}</h3>
      </div>
      {view && view.rows.length === 0 && (
        <Card style={{ textAlign: "center", color: C.muted, background: C.soft, border: "none" }}>
          {t("sage.asg.noStudents", { defaultValue: "No students are enrolled yet." })}</Card>
      )}
      {view?.rows.map((r) => (
        <SubmissionRow key={r.student_id} row={r} points={points} onGraded={load} />
      ))}
    </div>
  );
}

function SubmissionRow({ row, points, onGraded }: {
  row: SageSubmissionRow; points: number; onGraded: () => void;
}) {
  const { t } = useTranslation();
  const sub = row.submission;
  const [grade, setGrade] = useState<string>(sub?.grade != null ? String(sub.grade) : "");
  const [feedback, setFeedback] = useState(sub?.feedback || "");
  const [busy, setBusy] = useState(false);
  const [open, setOpen] = useState(false);

  async function save() {
    if (!sub) return;
    setBusy(true);
    try { await sageApi.gradeSubmission(sub.id, Number(grade) || 0, feedback); onGraded(); }
    catch (e) { window.alert((e as Error).message); } finally { setBusy(false); }
  }

  return (
    <Card>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
        <div>
          <b style={{ fontSize: 15 }}>{row.full_name}</b>
          <div style={{ color: C.muted, fontSize: 13 }}>
            {!sub ? t("sage.asg.notSubmitted", { defaultValue: "Not submitted" })
              : sub.grade != null ? t("sage.asg.gradedPts", { defaultValue: "Graded: {{grade}}/{{points}}", grade: sub.grade, points })
              : t("sage.asg.submittedOn", { defaultValue: "Submitted {{date}}", date: fmtDateTime(sub.submitted_at) })}
          </div>
        </div>
        {sub && <GhostBtn onClick={() => setOpen((o) => !o)}>
          <Icon name="eye" size={15} /> {open ? t("sage.asg.hide", { defaultValue: "Hide" }) : t("sage.asg.viewGrade", { defaultValue: "View & grade" })}</GhostBtn>}
      </div>
      {sub && open && (
        <div style={{ marginTop: 12, borderTop: `1px solid ${C.line}`, paddingTop: 12 }}>
          {sub.body.trim() && (
            <div className="sage-md" style={{ fontSize: 14, marginBottom: 12,
              background: C.soft, borderRadius: 10, padding: "10px 14px" }}
              dangerouslySetInnerHTML={{ __html: renderMarkdown(sub.body) }} />
          )}
          {sub.has_file && <div style={{ marginBottom: 12 }}><AttachmentLink sub={sub} /></div>}
          <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap", marginBottom: 10 }}>
            <label style={{ fontSize: 13, color: C.muted, display: "inline-flex", alignItems: "center", gap: 7 }}>
              {t("sage.asg.grade", { defaultValue: "Grade" })}
              <input type="number" min={0} max={points} value={grade}
                onChange={(e) => setGrade(e.target.value)} style={{ ...inputStyle, width: 90 }} />
              <span style={{ color: C.muted }}>/ {points}</span>
            </label>
          </div>
          <textarea value={feedback} onChange={(e) => setFeedback(e.target.value)}
            placeholder={t("sage.asg.phFeedback", { defaultValue: "Feedback for the student (optional)…" })}
            style={{ ...inputStyle, minHeight: 70, resize: "vertical", marginBottom: 10 }} />
          <PrimaryBtn onClick={save} disabled={busy}>{t("sage.asg.saveGrade", { defaultValue: "Save grade" })}</PrimaryBtn>
        </div>
      )}
    </Card>
  );
}

// --------------------------------------------------------------- Assignments (student)
function AssignmentsStudent({ course }: { course: SageCourseSummary }) {
  const { t } = useTranslation();
  const [items, setItems] = useState<SageAssignment[]>([]);
  const load = () => sageApi.assignments(course.id).then(setItems).catch(() => setItems([]));
  useEffect(() => { load(); }, [course.id]);

  return (
    <div style={{ display: "grid", gap: 12 }}>
      <h3 style={{ margin: 0, fontSize: 17 }}>{t("sage.tab.Assignments", { defaultValue: "Assignments" })}</h3>
      {items.length === 0 && (
        <Card style={{ textAlign: "center", color: C.muted, background: C.soft, border: "none" }}>
          {t("sage.asg.emptyStudent", { defaultValue: "No assignments have been posted yet." })}</Card>
      )}
      {items.map((a) => <StudentAssignmentCard key={a.id} assignment={a} onChanged={load} />)}
    </div>
  );
}

function StudentAssignmentCard({ assignment, onChanged }: {
  assignment: SageAssignment; onChanged: () => void;
}) {
  const { t } = useTranslation();
  const sub = assignment.my_submission;
  const graded = sub?.grade != null;
  const [open, setOpen] = useState(false);
  const [body, setBody] = useState(sub?.body || "");
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function submit() {
    if (!body.trim() && !file && !sub?.has_file) {
      setErr(t("sage.asg.errBodyOrFile", { defaultValue: "Write a response or attach a file before submitting." }));
      return;
    }
    setBusy(true); setErr(null);
    try { await sageApi.submitAssignment(assignment.id, body, file); onChanged(); setOpen(false); }
    catch (e) { setErr((e as Error).message); } finally { setBusy(false); }
  }

  const status = graded
    ? t("sage.asg.gradedPts", { defaultValue: "Graded: {{grade}}/{{points}}", grade: sub!.grade, points: assignment.points })
    : sub ? t("sage.asg.submitted", { defaultValue: "Submitted — awaiting grade" })
    : t("sage.asg.pointsShort", { defaultValue: "{{points}} pts", points: assignment.points });

  return (
    <Card>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
        <div>
          <b style={{ fontSize: 15 }}>{assignment.title}</b>
          <div style={{ color: graded ? C.success : C.muted, fontSize: 13 }}>
            {status}{assignment.due_at && <> · {t("sage.quiz.due", { date: fmtDateTime(assignment.due_at) })}</>}
          </div>
        </div>
        <GhostBtn onClick={() => setOpen((o) => !o)}>
          {open ? t("sage.asg.hide", { defaultValue: "Hide" })
            : graded ? t("sage.asg.viewResult", { defaultValue: "View result" })
            : sub ? t("sage.asg.editSubmission", { defaultValue: "View / edit" })
            : t("sage.asg.open", { defaultValue: "Open" })}
        </GhostBtn>
      </div>
      {open && (
        <div style={{ marginTop: 12, borderTop: `1px solid ${C.line}`, paddingTop: 12 }}>
          {assignment.instructions.trim() && (
            <div className="sage-md" style={{ fontSize: 14, marginBottom: 14 }}
              dangerouslySetInnerHTML={{ __html: renderMarkdown(assignment.instructions) }} />
          )}
          {graded ? (
            <div>
              <div style={{ fontWeight: 600, marginBottom: 6 }}>{t("sage.asg.yourSubmission", { defaultValue: "Your submission" })}</div>
              {sub!.body.trim() && (
                <div className="sage-md" style={{ fontSize: 14, background: C.soft, borderRadius: 10,
                  padding: "10px 14px", marginBottom: 12 }}
                  dangerouslySetInnerHTML={{ __html: renderMarkdown(sub!.body) }} />
              )}
              {sub!.has_file && <div style={{ marginBottom: 12 }}><AttachmentLink sub={sub!} /></div>}
              {sub!.feedback && <>
                <div style={{ fontWeight: 600, marginBottom: 6 }}>{t("sage.asg.feedback", { defaultValue: "Instructor feedback" })}</div>
                <div className="sage-md" style={{ fontSize: 14, background: C.soft, borderRadius: 10, padding: "10px 14px" }}
                  dangerouslySetInnerHTML={{ __html: renderMarkdown(sub!.feedback) }} />
              </>}
            </div>
          ) : (
            <div>
              {err && <div style={{ color: C.danger, marginBottom: 10, fontSize: 13.5 }}>{err}</div>}
              <MarkdownEditor value={body} onChange={setBody} minHeight={140}
                placeholder={t("sage.asg.phResponse", { defaultValue: "Write your response…" })} />
              <div style={{ marginTop: 12, display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
                <label style={{ ...ghostLike, cursor: "pointer" }}>
                  <Icon name="file" size={15} /> {t("sage.asg.attachFile", { defaultValue: "Attach file" })}
                  <input type="file" style={{ display: "none" }}
                    onChange={(e) => setFile(e.target.files?.[0] || null)} />
                </label>
                {file ? <span style={{ fontSize: 13, color: C.muted }}>{file.name}</span>
                  : sub?.has_file ? <AttachmentLink sub={sub} />
                  : null}
              </div>
              <div style={{ marginTop: 12 }}>
                <PrimaryBtn onClick={submit} disabled={busy}>
                  {sub ? t("sage.asg.resubmit", { defaultValue: "Update submission" }) : t("sage.asg.submit", { defaultValue: "Submit" })}</PrimaryBtn>
              </div>
            </div>
          )}
        </div>
      )}
    </Card>
  );
}

// --------------------------------------------------------------- Students
function Students({ course }: { course: SageCourseSummary }) {
  const { t } = useTranslation();
  const [students, setStudents] = useState<SageStudent[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const load = () => sageApi.students(course.id).then(setStudents).catch(() => setStudents([]));
  useEffect(() => { load(); }, [course.id]);

  async function remove(e: React.MouseEvent, s: SageStudent) {
    e.stopPropagation();
    if (!window.confirm(t("sage.students.removeConfirm",
      { defaultValue: "Remove {{name}} from this course? Their past results are kept.", name: s.full_name }))) return;
    setErr(null);
    try { await sageApi.removeStudent(course.id, s.id); load(); }
    catch (e) { setErr((e as Error).message); }
  }
  return (
    <Card>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 8 }}>
        <h3 style={{ marginTop: 0, marginBottom: 0, fontSize: 17 }}>{t("sage.students.title", { count: students.length })}</h3>
        <CopyChip code={course.join_code} />
      </div>
      {err && <div style={{ color: C.danger, fontSize: 13, marginTop: 8 }}>{err}</div>}
      <div style={{ marginTop: 8 }}>
        {students.length === 0 && <p style={{ color: C.muted }}>{t("sage.students.empty")}</p>}
        {students.map((s) => (
          <div key={s.id} style={{ display: "flex", alignItems: "center", gap: 11,
            padding: "10px 0", borderTop: `1px solid ${C.line}` }}>
            <div style={{ width: 34, height: 34, borderRadius: "50%", background: C.accentBg, color: C.accentInk,
              display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13, fontWeight: 600 }}>
              {initials(s.full_name)}</div>
            <div style={{ flex: 1, minWidth: 0 }}><b style={{ fontSize: 14.5 }}>{s.full_name}</b>
              <div style={{ color: C.muted, fontSize: 13 }}>{s.email}</div></div>
            <button onClick={(e) => remove(e, s)}
              style={{ background: "none", border: "none", color: C.danger, cursor: "pointer",
                fontSize: 13, fontWeight: 600, padding: "6px 8px", flexShrink: 0 }}>
              {t("sage.students.remove", { defaultValue: "Remove" })}</button>
          </div>
        ))}
      </div>
    </Card>
  );
}

// --------------------------------------------------------------- Grades
function StudentDrill({ course, studentId, onClose }:
  { course: SageCourseSummary; studentId: number; onClose: () => void }) {
  const { t } = useTranslation();
  const [d, setD] = useState<import("../api/client").SageStudentDetail | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const nav = useNavigate();
  useEffect(() => { setD(null); setErr(null);
    sageApi.studentDetail(course.id, studentId).then(setD)
      .catch((e: Error) => setErr(e.message)); }, [course.id, studentId]);
  if (err) return <Card><p style={{ color: C.danger, margin: 0 }}>{err}</p></Card>;
  if (!d) return <Card><p style={{ color: C.muted, margin: 0 }}>{t("sage.loading")}</p></Card>;
  const open = d.remediation.filter((m) => m.status !== "completed");
  return (
    <Card style={{ borderColor: "#c9c2f0" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div><b style={{ fontSize: 16 }}>{d.full_name}</b>
          <div style={{ color: C.muted, fontSize: 13 }}>{d.email}</div></div>
        <GhostBtn onClick={onClose}>{t("sage.close")}</GhostBtn>
      </div>
      <h4 style={{ margin: "14px 0 6px", fontSize: 14 }}>{t("sage.grades.quizAttempts")}</h4>
      {d.quizzes.length === 0 && <p style={{ color: C.muted }}>{t("sage.grades.noAttempts")}</p>}
      {d.quizzes.map((q) => (
        <div key={q.id} style={{ display: "flex", justifyContent: "space-between",
          padding: "7px 0", borderTop: `1px solid ${C.line}`, fontSize: 14 }}>
          <span>{q.title} <span style={{ color: C.muted, fontSize: 12 }}>· {t("sage.grades.attempts", { count: q.attempts })}</span></span>
          <b>{q.best_score == null ? "—" : `${Math.round(q.best_score * 100)}%`}</b>
        </div>
      ))}
      <h4 style={{ margin: "14px 0 6px", fontSize: 14 }}>{t("sage.grades.needsOpen", { count: open.length })}</h4>
      {open.length === 0 && <p style={{ color: C.muted, margin: 0 }}>{t("sage.grades.noneOpen")}</p>}
      {open.map((m) => (
        <div key={m.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center",
          padding: "7px 0", borderTop: `1px solid ${C.line}` }}>
          <span style={{ fontSize: 14 }}>{m.concept || m.title}</span>
          <GhostBtn onClick={() => nav(`/modules/${m.id}?home=/sage`)}>{t("sage.grades.viewSession")}</GhostBtn>
        </div>
      ))}
    </Card>
  );
}

function GradesTab({ course }: { course: SageCourseSummary }) {
  const { t } = useTranslation();
  const [g, setG] = useState<SageGrades | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [drill, setDrill] = useState<number | null>(null);
  useEffect(() => { setG(null); setErr(null);
    sageApi.grades(course.id).then(setG).catch((e: Error) => setErr(e.message)); }, [course.id]);
  if (err) return <Card><p style={{ color: C.danger, margin: 0 }}>{err}</p></Card>;
  if (!g) return <p style={{ color: C.muted }}>{t("sage.loading")}</p>;
  const pct = (v?: number) => v == null ? "—" : `${Math.round(v * 100)}%`;
  if (g.is_instructor) {
    return (
      <div style={{ display: "grid", gap: 12 }}>
        {drill != null && <StudentDrill course={course} studentId={drill} onClose={() => setDrill(null)} />}
        <Card>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 8 }}>
            <h3 style={{ marginTop: 0, marginBottom: 0, fontSize: 17 }}>{t("sage.grades.title")}</h3>
            <GhostBtn onClick={() => api.authedDownload(`/sage/courses/${course.id}/grades.csv`, "sage-grades.csv")}>
              <Icon name="download" size={15} /> {t("sage.grades.downloadCsv")}</GhostBtn>
          </div>
          <p style={{ color: C.muted, fontSize: 12.5, margin: "4px 0 10px" }}>{t("sage.grades.clickDrill")}</p>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", fontSize: 13.5, borderCollapse: "collapse", minWidth: 360 }}>
              <thead><tr style={{ textAlign: "left", color: C.muted }}>
                <th style={{ padding: "6px 8px" }}>{t("sage.grades.thStudent")}</th>
                {g.quizzes.map((q) => <th key={`q${q.id}`} style={{ padding: "6px 8px" }}>{q.title}</th>)}
                {(g.assignments || []).map((a) => <th key={`a${a.id}`} style={{ padding: "6px 8px" }}>
                  <span style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
                    <Icon name="edit" size={12} /> {a.title}</span></th>)}
                <th style={{ padding: "6px 8px" }}>{t("sage.grades.thNeeds")}</th>
              </tr></thead>
              <tbody>
                {(g.rows || []).map((r) => (
                  <tr key={r.student_id} style={{ borderTop: `1px solid ${C.line}`, cursor: "pointer" }}
                    onClick={() => setDrill(r.student_id)}>
                    <td style={{ padding: "8px", fontWeight: 600, color: C.accentInk }}>{r.full_name}</td>
                    {g.quizzes.map((q) => {
                      const v = r.scores[String(q.id)];
                      return <td key={`q${q.id}`} style={{ padding: "8px", fontWeight: 600,
                        color: v == null ? C.muted : scoreColor(v) }}>{pct(v)}</td>;
                    })}
                    {(g.assignments || []).map((a) => {
                      const v = r.assignment_scores?.[String(a.id)];
                      return <td key={`a${a.id}`} style={{ padding: "8px", fontWeight: 600,
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
          {(g.rows || []).length === 0 && <p style={{ color: C.muted }}>{t("sage.grades.noStudents")}</p>}
        </Card>
      </div>
    );
  }
  const scored = [
    ...g.quizzes.map((q) => g.scores?.[String(q.id)]),
    ...(g.assignments || []).map((a) => g.assignment_scores?.[String(a.id)]),
  ].filter((v): v is number => v != null);
  const overall = scored.length ? scored.reduce((a, b) => a + b, 0) / scored.length : null;
  return (
    <div style={{ display: "grid", gap: 14 }}>
      {overall != null && (
        <Card style={{ display: "flex", alignItems: "center", gap: 20 }}>
          <Donut v={overall} />
          <div>
            <div style={{ fontSize: 12.5, color: C.muted }}>{t("sage.grades.overall")}</div>
            <div style={{ fontSize: 15, color: C.ink, marginTop: 2 }}>
              {t(scored.length === 1 ? "sage.grades.across_one" : "sage.grades.across", { count: scored.length })}</div>
          </div>
        </Card>
      )}
      <Card>
        <h3 style={{ marginTop: 0, fontSize: 17 }}>{t("sage.grades.my")}</h3>
        {g.quizzes.length === 0 && (g.assignments || []).length === 0
          && <p style={{ color: C.muted }}>{t("sage.grades.noQuizzes")}</p>}
        {g.quizzes.map((q) => {
          const v = g.scores?.[String(q.id)];
          return (
            <div key={`q${q.id}`} style={{ display: "flex", alignItems: "center", gap: 12,
              padding: "11px 0", borderTop: `1px solid ${C.line}` }}>
              <span style={{ flex: 1, minWidth: 0 }}>{q.title}</span>
              {v != null && <Bar v={v} width={110} />}
              <b style={{ minWidth: 42, textAlign: "right",
                color: v == null ? C.muted : scoreColor(v) }}>{pct(v)}</b>
            </div>
          );
        })}
        {(g.assignments || []).map((a) => {
          const v = g.assignment_scores?.[String(a.id)];
          return (
            <div key={`a${a.id}`} style={{ display: "flex", alignItems: "center", gap: 12,
              padding: "11px 0", borderTop: `1px solid ${C.line}` }}>
              <span style={{ flex: 1, minWidth: 0, display: "inline-flex", alignItems: "center", gap: 6 }}>
                <Icon name="edit" size={13} /> {a.title}</span>
              {v != null && <Bar v={v} width={110} />}
              <b style={{ minWidth: 42, textAlign: "right",
                color: v == null ? C.muted : scoreColor(v) }}>{pct(v)}</b>
            </div>
          );
        })}
        {(g.open_remediation || 0) > 0 && (
          <div style={{ background: C.infoBg, color: C.info, borderRadius: 10, padding: "10px 14px",
            marginTop: 12, fontSize: 14 }}>
            {t("sage.grades.waiting", { count: g.open_remediation })}</div>
        )}
      </Card>
    </div>
  );
}

// --------------------------------------------------------------- Profile
function Profile({ onName, onBack }: { onName: (n: string) => void; onBack: () => void }) {
  const { t } = useTranslation();
  const [p, setP] = useState<SageProfile | null>(null);
  const [name, setName] = useState(""); const [title, setTitle] = useState(""); const [bio, setBio] = useState("");
  const [busy, setBusy] = useState(false); const [msg, setMsg] = useState<string | null>(null);
  useEffect(() => {
    sageApi.profile().then((pr) => { setP(pr); setName(pr.full_name); setTitle(pr.title || ""); setBio(pr.bio || ""); })
      .catch(() => {});
  }, []);
  async function save(e: React.FormEvent) {
    e.preventDefault(); setBusy(true); setMsg(null);
    try { const r = await sageApi.updateProfile({ full_name: name.trim(), title, bio }); onName(r.full_name); setMsg(t("sage.profile.saved")); }
    catch (e) { setMsg((e as Error).message); } finally { setBusy(false); }
  }
  const lbl: React.CSSProperties = { fontSize: 13, fontWeight: 600, color: C.muted };
  return (
    <div style={{ maxWidth: 520, margin: "0 auto" }}>
      <GhostBtn onClick={onBack}><Icon name="back" size={16} /> {t("sage.back")}</GhostBtn>
      <h2 style={{ color: C.brand, fontSize: 22, marginTop: 12 }}>{t("sage.profile.title")}</h2>
      <p style={{ color: C.muted, fontSize: 14, marginTop: 0 }}>
        {t("sage.profile.subtitle")}</p>
      <Card>
        <form onSubmit={save} style={{ display: "grid", gap: 6 }}>
          <label style={lbl}>{t("sage.profile.name")}</label>
          <input style={inputStyle} value={name} onChange={(e) => setName(e.target.value)} />
          <label style={lbl}>{t("sage.profile.titleField")}</label>
          <input style={inputStyle} value={title}
            onChange={(e) => setTitle(e.target.value)} />
          <label style={lbl}>{t("sage.profile.bio")}</label>
          <textarea style={{ ...inputStyle, minHeight: 80, resize: "vertical" }} value={bio}
            onChange={(e) => setBio(e.target.value)} />
          <div style={{ marginTop: 8 }}><PrimaryBtn type="submit" disabled={busy}>{busy ? t("sage.profile.saving") : t("sage.profile.save")}</PrimaryBtn></div>
          {msg && <div style={{ fontSize: 13, color: msg === t("sage.profile.saved") ? C.success : C.danger }}>{msg}</div>}
          {p && <div style={{ fontSize: 12, color: C.muted }}>{p.email}</div>}
        </form>
      </Card>
    </div>
  );
}

// --------------------------------------------------------------- Syllabus
function Syllabus({ course, instr, detail, onSaved }:
  { course: SageCourseSummary; instr: boolean; detail: SageCourseDetail | null; onSaved: () => void }) {
  const { t } = useTranslation();
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
        <MarkdownEditor value={text} onChange={setText} minHeight={240}
          placeholder={t("sage.syllabus.phEdit")} ariaLabel={t("sage.syllabus.phEdit")} />
        <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
          <PrimaryBtn onClick={save} disabled={busy}>{busy ? t("sage.profile.saving") : t("sage.syllabus.save")}</PrimaryBtn>
          <GhostBtn onClick={() => { setEdit(false); setText(detail?.syllabus || ""); }}>{t("sage.cancel")}</GhostBtn>
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
            ? t("sage.syllabus.emptyInstr")
            : t("sage.syllabus.emptyStudent")}</div>}
      {instr && <div style={{ marginTop: 14 }}>
        <GhostBtn onClick={() => setEdit(true)}><Icon name="edit" size={15} /> {detail?.syllabus ? t("sage.syllabus.edit") : t("sage.syllabus.add")}</GhostBtn>
      </div>}
    </Card>
  );
}

// --------------------------------------------------------------- Materials
function Materials({ course, instr }: { course: SageCourseSummary; instr: boolean }) {
  const { t } = useTranslation();
  const [mats, setMats] = useState<SageMaterial[]>([]);
  const [form, setForm] = useState<null | "note" | "code" | "file">(null);
  const load = () => sageApi.materials(course.id).then(setMats).catch(() => setMats([]));
  useEffect(() => { load(); }, [course.id]);
  return (
    <div style={{ display: "grid", gap: 12 }}>
      {instr && (
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <GhostBtn onClick={() => setForm(form === "note" ? null : "note")}><Icon name="note" size={16} /> {t("sage.materials.addNote")}</GhostBtn>
          <GhostBtn onClick={() => setForm(form === "code" ? null : "code")}><Icon name="code" size={16} /> {t("sage.materials.addCode")}</GhostBtn>
          <GhostBtn onClick={() => setForm(form === "file" ? null : "file")}><Icon name="file" size={16} /> {t("sage.materials.upload")}</GhostBtn>
        </div>
      )}
      {form && <MaterialForm courseId={course.id} kind={form} onDone={() => { setForm(null); load(); }} />}
      {mats.length === 0 && !form && (
        <Card style={{ textAlign: "center", color: C.muted, background: C.soft, border: "none" }}>
          {t("sage.materials.empty")}
        </Card>
      )}
      {mats.map((m) => <MaterialRow key={m.id} m={m} instr={instr} onChange={load} />)}
    </div>
  );
}

function MaterialForm({ courseId, kind, onDone }:
  { courseId: number; kind: "note" | "code" | "file"; onDone: () => void }) {
  const { t } = useTranslation();
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
        placeholder={t("sage.materials.phTitle")}
        value={title} onChange={(e) => setTitle(e.target.value)} />
      {kind === "file" ? (
        <input type="file" onChange={(e) => setFile(e.target.files?.[0] || null)} />
      ) : (
        <>
          {kind === "code" && <input style={{ ...inputStyle, marginBottom: 8 }}
            placeholder={t("sage.materials.phLanguage", { defaultValue: "Language (e.g. python)" })}
            value={language} onChange={(e) => setLanguage(e.target.value)} />}
          {kind === "code" ? (
            <textarea style={{ ...inputStyle, minHeight: 140, resize: "vertical",
              fontFamily: "var(--font-mono, monospace)" }}
              placeholder={t("sage.materials.phCode")}
              value={body} onChange={(e) => setBody(e.target.value)} />
          ) : (
            <MarkdownEditor value={body} onChange={setBody} minHeight={160}
              placeholder={t("sage.materials.phNote")} ariaLabel={t("sage.materials.phNote")} />
          )}
        </>
      )}
      <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
        <PrimaryBtn onClick={save} disabled={busy}>{busy ? t("sage.materials.saving") : t("sage.materials.save")}</PrimaryBtn>
      </div>
      {err && <div style={{ color: C.danger, fontSize: 13, marginTop: 8 }}>{err}</div>}
    </Card>
  );
}

function fmtSize(n: number) {
  return n < 1024 ? `${n} B` : n < 1048576 ? `${Math.round(n / 1024)} KB` : `${(n / 1048576).toFixed(1)} MB`;
}

function MaterialRow({ m, instr, onChange }: { m: SageMaterial; instr: boolean; onChange: () => void }) {
  const { t } = useTranslation();
  const [body, setBody] = useState<string | null>(null);
  const [openB, setOpenB] = useState(false);
  const isText = m.kind === "note" || m.kind === "code";
  async function view() {
    if (!openB && body === null) { const d = await sageApi.material(m.id); setBody(d.body || ""); }
    setOpenB((o) => !o);
  }
  async function remove() {
    if (!window.confirm(t("sage.materials.deleteConfirm", { defaultValue: "Delete this material?" }))) return;
    try { await sageApi.deleteMaterial(m.id); onChange(); }
    catch (e) { window.alert((e as Error).message); }
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
            <Icon name="download" size={15} /> {t("sage.materials.download")}</GhostBtn>}
          {instr && <button onClick={remove}
            title={t("common.delete")} style={{ background: "none", border: "none", cursor: "pointer", color: C.danger,
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
  const { t, i18n } = useTranslation();
  const [mods, setMods] = useState<RemediationModule[]>([]);
  const [active, setActive] = useState<number | null>(null);
  const load = () => api.myModules(i18n.language).then((m) => setMods(m.filter((x) => x.course_id === course.id)))
    .catch(() => setMods([]));
  useEffect(() => { load(); setActive(null); }, [course.id, i18n.language]);

  // Launch the LMS Bridge tutor embedded inside Sage — the same way it appears inside
  // Canvas/Blackboard/Moodle — rather than navigating away to the standalone page.
  if (active != null) {
    return <ModuleView moduleId={active} onBack={() => { setActive(null); load(); }} />;
  }

  const open = mods.filter((m) => m.status !== "completed");
  return (
    <div style={{ display: "grid", gap: 12 }}>
      <h3 style={{ margin: 0, fontSize: 17 }}>{t("sage.needs.title")}</h3>
      {open.length === 0 && (
        <Card style={{ textAlign: "center", color: C.muted, background: C.successBg, border: "none" }}>
          <Icon name="check" size={24} color={C.success} />
          <div style={{ marginTop: 6 }}>{t("sage.needs.allCaught")}</div>
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
                <div style={{ color: C.muted, fontSize: 13 }}>{t("sage.needs.builtFor")}</div>
              </div>
            </div>
            <PrimaryBtn onClick={() => setActive(m.id)}><Icon name="play" size={16} /> {t("sage.needs.start")}</PrimaryBtn>
          </div>
        </Card>
      ))}
    </div>
  );
}
