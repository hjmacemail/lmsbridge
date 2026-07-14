import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";
import type { ClassBrief, ConceptOut, Course, InstructorAnalytics } from "../types";
import MaterialsPanel from "../components/MaterialsPanel";
import StudentsPanel from "../components/StudentsPanel";
import AssessmentsPanel from "../components/AssessmentsPanel";
import RemediationPanel from "../components/RemediationPanel";
import SettingsPanel from "../components/SettingsPanel";
import CourseSetupPanel from "../components/CourseSetupPanel";
import LmsConnectionsPanel from "../components/LmsConnectionsPanel";
import LeadsPanel from "../components/LeadsPanel";
import InstitutionPanel from "../components/InstitutionPanel";
import LicensesPanel from "../components/LicensesPanel";

type Persona = "instructor" | "institution" | "platform";
type Tab = "overview" | "students" | "assessments" | "materials"
  | "remediation" | "setup" | "usage" | "settings" | "lms" | "leads" | "licenses";

// `who` lists the personas that see a tab. `hideWhenLms` removes the manual course-setup
// path once an LMS is connected (courses then arrive automatically from LTI launches).
const TABS: { id: Tab; label: string; who: Persona[]; hideWhenLms?: boolean }[] = [
  { id: "overview", label: "Overview", who: ["instructor"] },
  { id: "students", label: "Students", who: ["instructor"] },
  { id: "assessments", label: "Assessments & Rubrics", who: ["instructor"] },
  { id: "materials", label: "Course Material", who: ["instructor"] },
  { id: "remediation", label: "Remediation", who: ["instructor"] },
  { id: "setup", label: "Course Setup", who: ["instructor"], hideWhenLms: true },
  { id: "usage", label: "Usage", who: ["institution", "platform"] },
  { id: "settings", label: "AI & Privacy", who: ["institution", "platform"] },
  { id: "lms", label: "LMS (LTI)", who: ["platform"] },
  { id: "licenses", label: "Licenses", who: ["platform"] },
  { id: "leads", label: "Leads", who: ["platform"] },
];

const TITLES: Record<Persona, string> = {
  instructor: "Instructor console",
  institution: "Institution admin",
  platform: "Platform console",
};

function CopilotBrief({ courseId }: { courseId: number }) {
  const [brief, setBrief] = useState<ClassBrief | null>(null);
  const [loading, setLoading] = useState(true);
  const load = () => {
    setLoading(true);
    api.classBrief(courseId).then(setBrief).catch(() => setBrief(null)).finally(() => setLoading(false));
  };
  useEffect(load, [courseId]);

  const accent = "#3C3489";
  return (
    <div style={{ background: "#EEF0FB", border: "1px solid #D5DAF3", borderRadius: 14,
      padding: "16px 18px", marginBottom: 22 }}>
      <div className="row" style={{ alignItems: "center", marginBottom: 8 }}>
        <div style={{ fontSize: 12, fontWeight: 700, letterSpacing: ".5px", textTransform: "uppercase",
          color: accent }}>✨ AI Copilot — what to do before your next class</div>
        <button onClick={load} disabled={loading}
          style={{ border: "1px solid #C7CCEF", background: "#fff", color: accent, borderRadius: 8,
            padding: "4px 12px", fontSize: 12.5, cursor: loading ? "default" : "pointer" }}>
          {loading ? "…" : "↻ Refresh"}</button>
      </div>
      {loading && !brief ? (
        <p className="muted" style={{ margin: 0 }}>Reading the class…</p>
      ) : !brief ? (
        <p className="muted" style={{ margin: 0 }}>Brief unavailable right now.</p>
      ) : (
        <>
          <div style={{ display: "flex", gap: 22, flexWrap: "wrap", alignItems: "baseline",
            marginBottom: 10 }}>
            {brief.health_pct != null && (
              <div>
                <div style={{ fontSize: 30, fontWeight: 800, color: accent, lineHeight: 1 }}>
                  {brief.health_pct}%</div>
                <div className="muted" style={{ fontSize: 11.5 }}>class health</div>
              </div>
            )}
            <div>
              <div style={{ fontSize: 30, fontWeight: 800, color: "#C0392B", lineHeight: 1 }}>
                {brief.needs_attention}</div>
              <div className="muted" style={{ fontSize: 11.5 }}>of {brief.students_total} need attention</div>
            </div>
            <div>
              <div style={{ fontSize: 30, fontWeight: 800, color: "#1E7A43", lineHeight: 1 }}>
                {brief.ai_completed}/{brief.ai_sessions}</div>
              <div className="muted" style={{ fontSize: 11.5 }}>AI sessions completed</div>
            </div>
          </div>
          <p style={{ margin: "0 0 10px", fontSize: 14.5, color: "#23264D", lineHeight: 1.55 }}>
            {brief.brief}</p>
          <div style={{ background: "#fff", border: "1px solid #D5DAF3", borderRadius: 10,
            padding: "10px 13px", display: "flex", gap: 10, alignItems: "center" }}>
            <span style={{ fontSize: 18 }}>🎯</span>
            <span style={{ fontSize: 14, fontWeight: 600, color: accent }}>{brief.recommendation}</span>
          </div>
          {brief.top_misconception && (
            <p className="muted" style={{ margin: "8px 0 0", fontSize: 12.5 }}>
              Likely misconception on <strong>{brief.top_concept}</strong>: {brief.top_misconception}
            </p>
          )}
        </>
      )}
    </div>
  );
}

function Overview({ courseId }: { courseId: number }) {
  const [analytics, setAnalytics] = useState<InstructorAnalytics | null>(null);
  useEffect(() => {
    api.analytics(courseId).then(setAnalytics).catch(() => setAnalytics(null));
  }, [courseId]);
  if (!analytics) return <p className="muted">Loading…</p>;

  return (
    <>
      <CopilotBrief courseId={courseId} />
      <div className="grid cols-3">
        <div className="card"><div className="muted">Enrolled students</div>
          <div className="kpi">{analytics.enrolled_students}</div></div>
        <div className="card"><div className="muted">Modules generated</div>
          <div className="kpi">{analytics.modules_generated}</div></div>
        <div className="card"><div className="muted">Modules completed</div>
          <div className="kpi">{analytics.modules_completed}</div></div>
      </div>
      <h2 style={{ marginTop: 26 }}>Concepts ranked by class risk</h2>
      <div className="card">
        <table>
          <thead><tr><th>Concept</th><th>Avg mastery</th><th>At risk</th><th></th></tr></thead>
          <tbody>
            {analytics.concept_risks.length === 0 &&
              <tr><td colSpan={4} className="muted">No mastery data yet. Run a sync.</td></tr>}
            {analytics.concept_risks.map((r) => (
              <tr key={r.concept_id}>
                <td style={{ fontWeight: 600 }}>{r.concept_name}</td>
                <td>
                  <div className="row" style={{ gap: 8 }}>
                    <div className="bar" style={{ width: 120 }}>
                      <span style={{ width: `${Math.round(r.avg_mastery * 100)}%`,
                        background: r.avg_mastery <= 0.7 ? "var(--at-risk)"
                          : r.avg_mastery < 0.85 ? "var(--developing)" : "var(--mastered)" }} />
                    </div>
                    {Math.round(r.avg_mastery * 100)}%
                  </div>
                </td>
                <td>{r.at_risk_count} / {r.total_students}</td>
                <td>{r.avg_mastery <= 0.7 &&
                  <span className="pill at_risk">needs attention</span>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

export default function InstructorDashboard({ scoped = false }: { scoped?: boolean }) {
  const [courses, setCourses] = useState<Course[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [concepts, setConcepts] = useState<ConceptOut[]>([]);
  const [tab, setTab] = useState<Tab>("overview");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [lmsConnected, setLmsConnected] = useState(false);
  const [community, setCommunity] = useState(true); // default to self-hosted community mode
  const { auth } = useAuth();
  const [params] = useSearchParams();
  // When the tool is launched LMS-wide via LTI, the instructor arrives in ONE course's
  // context (course_id in the launch redirect) — so we scope to that course and hide the
  // course picker / "+ New course". The demo passes `scoped` to lock to a single course too.
  const urlCourseId = Number(params.get("course_id")) || null;
  const courseScoped = scoped || urlCourseId != null;

  const isAdmin = auth?.role === "admin";
  // The platform-operator role only exists in hosted (multi-tenant) deployments.
  const isPlatformAdmin = !community && auth?.is_platform_admin === true;
  const persona: Persona = isAdmin
    ? (isPlatformAdmin ? "platform" : "institution")
    : "instructor";
  const isInstructor = persona === "instructor";

  const tabs = useMemo(
    () => TABS.filter((t) => {
      if (t.hideWhenLms && (lmsConnected || courseScoped)) return false;
      if (community) {
        // Single self-hosted institution: no sales/licensing surfaces; the admin manages
        // their own LMS registration.
        if (t.id === "licenses" || t.id === "leads") return false;
        if (t.id === "lms") return isAdmin;
        return t.who.includes(persona);
      }
      return t.who.includes(persona);
    }),
    [persona, lmsConnected, community, isAdmin, courseScoped],
  );

  const [newCourse, setNewCourse] =
    useState<{ code: string; title: string; term: string } | null>(null);

  // Keep the active tab valid for the current persona / LMS state.
  useEffect(() => {
    if (!tabs.some((t) => t.id === tab) && tabs.length) setTab(tabs[0].id);
  }, [tabs, tab]);

  useEffect(() => {
    api.ltiConfig().then((c) => {
      setLmsConnected(!!c.lms_connected);
      setCommunity(c.deployment_mode !== "hosted");
    }).catch(() => undefined);
  }, []);

  function loadCourses(selectId?: number) {
    api.courses().then((cs) => {
      setCourses(cs);
      if (selectId != null) setSelected(selectId);
      else if (cs.length && selected == null) setSelected(cs[0].id);
    }).catch((e) => setErr((e as Error).message));
  }

  useEffect(() => {
    if (!isInstructor) return;
    api.courses().then((cs) => {
      setCourses(cs);
      if (cs.length) {
        // Honor the launch context when present, else default to the first course.
        const pick = urlCourseId && cs.some((c) => c.id === urlCourseId)
          ? urlCourseId : cs[0].id;
        setSelected(pick);
      }
    }).catch((e) => setErr((e as Error).message));
  }, [isInstructor, urlCourseId]);

  async function createCourse() {
    if (!newCourse || !newCourse.code.trim() || !newCourse.title.trim()) return;
    setBusy(true); setErr(null);
    try {
      const c = await api.createCourse({
        code: newCourse.code.trim(), title: newCourse.title.trim(),
        term: newCourse.term.trim() || "2026SP",
      });
      setNewCourse(null);
      loadCourses(c.id);
      setTab("setup");
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    if (selected == null) return;
    api.course(selected).then((c) => setConcepts(c.concepts)).catch(() => setConcepts([]));
  }, [selected]);

  async function sync() {
    if (selected == null) return;
    setBusy(true); setErr(null);
    try {
      await api.syncCourse(selected);
      const s = selected; setSelected(null); setTimeout(() => setSelected(s), 0);
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function exportCsv() {
    if (selected == null) return;
    const course = courses.find((c) => c.id === selected);
    await api.authedDownload(
      `/analytics/courses/${selected}/export.csv`,
      `${(course?.code || "course").replace(/\s/g, "_")}_analytics.csv`,
    );
  }

  const showCourseControls = isInstructor;
  // Adding/picking courses only makes sense in a standalone (no-LMS) deployment with no
  // launch context. Under an LMS-wide launch the course is fixed by the launch itself.
  const canAddCourse = isInstructor && !lmsConnected && !courseScoped;
  const selectedCourse = courses.find((c) => c.id === selected);

  return (
    <div className="container">
      <div className="row">
        <h1>{TITLES[persona]}</h1>
        {showCourseControls && (
          <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
            {/* A dropdown only makes sense for a standalone (no-LMS) deployment that manages
                more than one course by hand. Under an LMS launch (or the demo) the course is
                fixed, so show it as a plain label. */}
            {!courseScoped && courses.length > 1 ? (
              <select value={selected ?? ""} onChange={(e) => setSelected(Number(e.target.value))}
                style={{ width: 260 }}>
                {courses.map((c) => <option key={c.id} value={c.id}>{c.code} — {c.title}</option>)}
              </select>
            ) : (
              <span style={{ fontWeight: 600, fontSize: 15, color: "var(--ink, #11161b)" }}>
                {selectedCourse ? `${selectedCourse.code} — ${selectedCourse.title}` : "Loading…"}
              </span>
            )}
            {canAddCourse && (
              <button className="btn secondary" onClick={() =>
                setNewCourse(newCourse ? null : { code: "", title: "", term: "2026SP" })}>
                + New course
              </button>
            )}
            {/* Under an LMS launch, results flow in automatically — a manual sync is only
                meaningful for a standalone (no-LMS) deployment. */}
            {!courseScoped && (
              <button className="btn secondary" onClick={sync} disabled={busy}>
                {busy ? "Syncing…" : "Sync"}
              </button>
            )}
            <button className="btn secondary" onClick={exportCsv}>Export CSV</button>
          </div>
        )}
      </div>
      {persona === "institution" && (
        <p className="muted" style={{ marginTop: 2, fontSize: 13 }}>
          Operations view: configure AI &amp; privacy and monitor institution-wide adoption.
          Course-level student data stays with instructors.
        </p>
      )}
      {err && <div className="error">{err}</div>}

      {canAddCourse && newCourse && (
        <div className="card" style={{ marginTop: 12, background: "var(--soft)" }}>
          <h3 style={{ marginTop: 0 }}>Create a course</h3>
          <div className="grid cols-3" style={{ alignItems: "end" }}>
            <div className="field" style={{ marginBottom: 0 }}><label>Code</label>
              <input value={newCourse.code}
                onChange={(e) => setNewCourse({ ...newCourse, code: e.target.value })}
                placeholder="e.g. CS-101" /></div>
            <div className="field" style={{ marginBottom: 0 }}><label>Title</label>
              <input value={newCourse.title}
                onChange={(e) => setNewCourse({ ...newCourse, title: e.target.value })}
                placeholder="e.g. Intro to Computer Science" /></div>
            <div className="field" style={{ marginBottom: 0 }}><label>Term</label>
              <input value={newCourse.term}
                onChange={(e) => setNewCourse({ ...newCourse, term: e.target.value })} /></div>
          </div>
          <button className="btn" style={{ marginTop: 14 }} onClick={createCourse} disabled={busy}>
            {busy ? "Creating…" : "Create course"}
          </button>
          <p className="muted" style={{ fontSize: 12, marginBottom: 0 }}>
            After creating, use the <strong>Course Setup</strong> tab to add concepts and assessments.
          </p>
        </div>
      )}

      <div className="tabs" style={{ margin: "18px 0 22px" }}>
        {tabs.map((t) => (
          <button key={t.id} className={`tab ${tab === t.id ? "active" : ""}`}
            onClick={() => setTab(t.id)}>{t.label}</button>
        ))}
      </div>

      {tab === "usage" ? (
        <InstitutionPanel />
      ) : tab === "settings" ? (
        <SettingsPanel />
      ) : tab === "lms" ? (
        <LmsConnectionsPanel />
      ) : tab === "licenses" ? (
        <LicensesPanel />
      ) : tab === "leads" ? (
        <LeadsPanel />
      ) : selected != null ? (
        <div key={selected}>
          {tab === "overview" && <Overview courseId={selected} />}
          {tab === "students" && <StudentsPanel courseId={selected} />}
          {tab === "assessments" && <AssessmentsPanel courseId={selected} />}
          {tab === "materials" && <MaterialsPanel courseId={selected} concepts={concepts} />}
          {tab === "setup" && <CourseSetupPanel courseId={selected} />}
          {tab === "remediation" && <RemediationPanel courseId={selected} />}
        </div>
      ) : (
        <p className="muted">No courses yet. Use <strong>+ New course</strong> to create one.</p>
      )}
    </div>
  );
}
