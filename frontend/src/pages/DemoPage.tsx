import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";
import LanguageSwitcher from "../components/LanguageSwitcher";
import LmsFrame, { LMS_CONFIG, type LmsId, type LmsPage } from "../components/LmsFrame";
import SimPage from "../components/SimPage";
import StudentDashboard from "./StudentDashboard";
import InstructorDashboard from "./InstructorDashboard";
import ModuleView from "./ModuleView";

const LMS_IDS: LmsId[] = ["canvas", "blackboard", "moodle", "brightspace"];
type Role = "student" | "instructor";
// Cycled in the integration bar to make the AI feel alive and show what LMS Bridge does.
const ACTS = ["actReadingGrades", "actReadingRubrics", "actMappingOutcomes",
  "actDetecting", "actGenerating", "actReady"];

export default function DemoPage() {
  const [params, setParams] = useSearchParams();
  const { auth, adoptToken } = useAuth();
  const { t } = useTranslation();
  const [err, setErr] = useState<string | null>(null);
  const [resetting, setResetting] = useState(false);
  const [act, setAct] = useState(0);

  useEffect(() => {
    const id = setInterval(() => setAct((a) => (a + 1) % ACTS.length), 1700);
    return () => clearInterval(id);
  }, []);

  const lms = (LMS_IDS.includes(params.get("lms") as LmsId)
    ? params.get("lms") : "canvas") as LmsId;
  const role: Role = params.get("role") === "instructor" ? "instructor" : "student";

  // Load the active LMS's web font (Lato / Open Sans) so the chrome matches more closely.
  useEffect(() => {
    const fam = LMS_CONFIG[lms].font.replace(/ /g, "+");
    const id = "lms-demo-font-" + fam;
    if (!document.getElementById(id)) {
      const link = document.createElement("link");
      link.id = id; link.rel = "stylesheet";
      link.href = `https://fonts.googleapis.com/css2?family=${fam}:wght@400;700;800&display=swap`;
      document.head.appendChild(link);
    }
  }, [lms]);

  // Sign in (password-less) as the seeded demo account for the chosen role.
  useEffect(() => {
    let cancel = false;
    if (auth?.role === role) return;
    api.demoLogin(role)
      .then((t) => { if (!cancel) adoptToken(t); })
      .catch(() => { if (!cancel) setErr(t("demo.wakingUp")); });
    return () => { cancel = true; };
  }, [role, auth?.role, adoptToken]);

  // Open a tutor session inside the demo (so it stays within the simulated LMS frame),
  // rather than routing to /modules/:id which would leave the frame.
  const moduleId = Number(params.get("module")) || null;
  const activePage = (params.get("page") || "tool") as LmsPage;
  function demoUrl(over: Record<string, string | number | null>): string {
    const next = new URLSearchParams(params);
    Object.entries(over).forEach(([k, v]) =>
      v == null ? next.delete(k) : next.set(k, String(v)));
    return `/demo?${next.toString()}`;
  }
  // Navigate the simulated LMS nav: "tool" clears page+module; other pages set ?page=...
  function linkFor(p: LmsPage): string {
    return p === "tool"
      ? demoUrl({ page: null, module: null })
      : demoUrl({ page: p, module: null });
  }
  function set(key: "lms" | "role" | "module" | "page", value: string | null) {
    const next = new URLSearchParams(params);
    if (value == null) next.delete(key); else next.set(key, value);
    if (key === "lms" || key === "role") { next.delete("page"); next.delete("module"); }
    setParams(next, { replace: true });
  }

  async function resetDemo() {
    if (resetting) return;
    setResetting(true);
    try {
      await api.demoReset();
      window.location.reload(); // re-fetch the freshly seeded state
    } catch {
      setErr("Couldn't reset the demo just now — try again in a moment.");
      setResetting(false);
    }
  }

  // Where "Exit demo" goes: the marketing/landing home. The marketing site passes its own
  // origin as ?home=...; otherwise derive it (app.lmsbridge.app -> lmsbridge.app), else root.
  function platformHome(): string {
    const fromParam = params.get("home");
    if (fromParam) return fromParam;
    if (typeof window === "undefined") return "/";
    const { protocol, hostname, port } = window.location;
    if (hostname.startsWith("app.")) {
      return `${protocol}//${hostname.slice(4)}${port ? ":" + port : ""}`;
    }
    return "/";
  }
  const ready = auth?.role === role;
  const guide = role === "instructor"
    ? [t("demo.guideInstr1"), t("demo.guideInstr2"), t("demo.guideInstr3")]
    : [t("demo.guideStudent1"), t("demo.guideStudent2"), t("demo.guideStudent3")];

  return (
    <div>
      <style>{"@keyframes lmsbPulse{0%,100%{opacity:1}50%{opacity:.25}}"}</style>

      {/* Slim, branded control bar */}
      <div style={{ background: "#3C3489", color: "#fff", display: "flex", flexWrap: "wrap",
        alignItems: "center", gap: "8px 14px", padding: "7px 16px" }}>
        <span style={{ display: "inline-flex", alignItems: "baseline", gap: 7 }}>
          <span style={{ fontWeight: 800, fontSize: 15.5 }}>LMS Bridge</span>
          <span style={{ fontSize: 11, opacity: .7, textTransform: "uppercase", letterSpacing: ".6px" }}>
            {t("demo.brandTag")}</span>
        </span>
        <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
          <span style={{ fontSize: 11, opacity: .65 }}>{t("demo.worksWith")}</span>
          {LMS_IDS.map((id) => (
            <button key={id} onClick={() => set("lms", id)}
              style={{ fontSize: 12.5, padding: "4px 11px", borderRadius: 999, cursor: "pointer",
                border: "1px solid rgba(255,255,255,.3)",
                background: id === lms ? "#fff" : "transparent",
                color: id === lms ? "#3C3489" : "#fff", fontWeight: id === lms ? 700 : 400 }}>
              {LMS_CONFIG[id].label}
            </button>
          ))}
        </span>
        <span style={{ display: "inline-flex", gap: 6 }}>
          {(["student", "instructor"] as Role[]).map((r) => (
            <button key={r} onClick={() => set("role", r)}
              style={{ fontSize: 12.5, padding: "4px 11px", borderRadius: 999, cursor: "pointer",
                border: "1px solid rgba(255,255,255,.3)",
                background: r === role ? "#fff" : "transparent",
                color: r === role ? "#3C3489" : "#fff", fontWeight: r === role ? 700 : 400 }}>
              {t("demo." + r)}
            </button>
          ))}
        </span>
        <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 12 }}>
          <LanguageSwitcher dark />
          <button onClick={resetDemo} disabled={resetting}
            style={{ fontSize: 12.5, padding: "4px 10px", borderRadius: 7,
              cursor: resetting ? "default" : "pointer",
              border: "1px solid rgba(255,255,255,.45)", background: "transparent", color: "#fff" }}>
            {resetting ? t("demo.resetting") : t("demo.reset")}
          </button>
          <a href={platformHome()} style={{ color: "#fff", fontSize: 12.5,
            textDecoration: "underline" }}>{t("demo.exit")}</a>
        </div>
      </div>

      {/* Integration bar: makes the "bridge" visible + shows live AI activity */}
      <div style={{ background: "#F3F1FB", borderBottom: "1px solid #E0DCF3", padding: "8px 16px",
        display: "flex", flexWrap: "wrap", alignItems: "center", gap: "8px 16px" }}>
        <div style={{ display: "inline-flex", alignItems: "center", gap: 8, fontSize: 12.5 }}>
          <span style={{ color: "#4A4F9E", fontWeight: 600 }}>{LMS_CONFIG[lms].label}</span>
          <span style={{ color: "#9A97C4" }}>→</span>
          <span style={{ color: "#fff", background: "#3C3489", fontWeight: 700, padding: "2px 9px",
            borderRadius: 999 }}>{t("demo.flowBridge")}</span>
          <span style={{ color: "#9A97C4" }}>→</span>
          <span style={{ color: "#4A4F9E", fontWeight: 600 }}>{t("demo.flowInsights")}</span>
        </div>
        <div style={{ display: "inline-flex", alignItems: "center", gap: 7, fontSize: 12.5,
          color: "#3C3489" }}>
          <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#2F9D5B",
            animation: "lmsbPulse 1.4s infinite" }} />
          <span style={{ opacity: .7 }}>{t("demo.liveActivity")}:</span>
          <span style={{ fontWeight: 600 }}>{t("demo." + ACTS[act])}…</span>
        </div>
        <div style={{ marginLeft: "auto", display: "inline-flex", alignItems: "center", gap: 10,
          fontSize: 12, color: "#6A66A0", flexWrap: "wrap" }}>
          <span style={{ fontWeight: 600 }}>{t("demo.tryThese")}:</span>
          {guide.map((g, i) => (
            <span key={i}>{["①", "②", "③"][i]} {g}</span>
          ))}
        </div>
      </div>

      {/* Prominent "this is a simulation" banner */}
      <div style={{ background: "#E5F5EC", borderBottom: "1px solid #C4E6CD", padding: "7px 16px",
        fontSize: 12.5, color: "#22603C", display: "flex", alignItems: "center", gap: 8 }}>
        <span style={{ width: 9, height: 9, borderRadius: "50%", background: "#2F9D5B", flex: "none" }} />
        {t("demo.simBanner", { lms: LMS_CONFIG[lms].label })}
      </div>

      {err ? (
        <div style={{ padding: 24 }}><div className="error">{err}</div></div>
      ) : !ready ? (
        <div style={{ padding: 24, color: "#5f6b76" }}>{t("demo.loadingCourse")}</div>
      ) : (
        <LmsFrame lms={lms} role={role} activePage={activePage} linkFor={linkFor}>
          {activePage !== "tool" ? (
            <SimPage page={activePage} lms={lms} toolHref={linkFor("tool")} />
          ) : role === "instructor" ? (
            <InstructorDashboard scoped />
          ) : moduleId ? (
            <ModuleView moduleId={moduleId} onBack={() => set("module", null)} />
          ) : (
            <StudentDashboard moduleLink={(id) => demoUrl({ module: id })} />
          )}
        </LmsFrame>
      )}
    </div>
  );
}
