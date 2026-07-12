import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../api/client";
import type { Course, Mastery, RemediationModule, StudentDashboard as Dash } from "../types";

function pct(n: number) { return `${Math.round(n * 100)}%`; }
const RISK_ORDER: Record<string, number> = { at_risk: 0, developing: 1, mastered: 2 };

// Supportive, student-facing framing (never the instructor's "at risk" language).
const SUP: Record<Mastery["status"], { key: string; bg: string; fg: string; bar: string; dot: string }> = {
  at_risk: { key: "student.needsReview", bg: "#FBEDDC", fg: "#8A5312", bar: "#E0912F", dot: "#E0912F" },
  developing: { key: "student.improving", bg: "#E9F0FB", fg: "#2B4A8C", bar: "var(--developing)", dot: "#3E7BD6" },
  mastered: { key: "student.masteredLabel", bg: "#E5F5EC", fg: "#1E7A43", bar: "var(--mastered)", dot: "#2F9D5B" },
};

// Estimate effort from the number of short activities (no per-question tracking in the payload).
function topicSteps(mods: RemediationModule[]) {
  const s = mods.reduce((n, m) => n + (m.activities?.length || 0), 0);
  return s || mods.length * 3;
}
function estMinutes(steps: number) { return Math.max(3, Math.round(steps * 1.5)); }
function confidenceKey(score: number) {
  return score < 0.4 ? "student.confLow" : score < 0.75 ? "student.confMedium" : "student.confHigh";
}

interface Topic {
  conceptId: number;
  name: string;
  status: Mastery["status"];
  score: number;
  modules: RemediationModule[];
}

export default function StudentDashboard(
  { moduleLink = (id: number) => `/modules/${id}` }: { moduleLink?: (id: number) => string },
) {
  const { t: tr } = useTranslation();
  const [courses, setCourses] = useState<Course[]>([]);
  const [courseId, setCourseId] = useState<number | null>(null);
  const [dash, setDash] = useState<Dash | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [openTopic, setOpenTopic] = useState<number | null>(null);
  const [showAll, setShowAll] = useState(false);
  const [openGroups, setOpenGroups] = useState<Set<string>>(new Set(["at_risk"]));
  const VISIBLE = 4;

  useEffect(() => {
    api.myCourses().then((cs) => {
      setCourses(cs);
      if (cs.length) setCourseId(cs[0].id);
      else api.myDashboard().then(setDash);
    }).catch((e) => setErr((e as Error).message));
  }, []);

  useEffect(() => {
    if (courseId == null) return;
    setDash(null);
    api.myDashboard(courseId).then(setDash).catch((e) => setErr((e as Error).message));
  }, [courseId]);

  const topics: Topic[] = useMemo(() => {
    if (!dash) return [];
    const masteryByConcept = new Map(dash.masteries.map((m) => [m.concept_id, m]));
    const byConcept = new Map<number, Topic>();
    for (const mod of dash.open_modules) {
      const m = masteryByConcept.get(mod.concept_id);
      if (!byConcept.has(mod.concept_id)) {
        byConcept.set(mod.concept_id, {
          conceptId: mod.concept_id,
          name: m?.concept_name || "This topic",
          status: m?.status || "developing",
          score: m?.mastery_score ?? 0.5,
          modules: [],
        });
      }
      byConcept.get(mod.concept_id)!.modules.push(mod);
    }
    return [...byConcept.values()].sort(
      (a, b) => (RISK_ORDER[a.status] - RISK_ORDER[b.status]) || (a.score - b.score),
    );
  }, [dash]);

  useEffect(() => {
    setOpenTopic(topics.length ? topics[0].conceptId : null);
    setShowAll(false);
  }, [topics]);

  const mastered = useMemo(
    () => (dash?.masteries || []).filter((m) => m.status === "mastered"), [dash]);

  if (err) return <div className="container"><div className="card error">{err}</div></div>;

  function Pill({ status }: { status: Mastery["status"] }) {
    const s = SUP[status];
    return (
      <span style={{
        background: s.bg, color: s.fg, fontSize: 12, fontWeight: 600,
        padding: "2px 10px", borderRadius: 999, whiteSpace: "nowrap",
      }}>{tr(s.key)}</span>
    );
  }

  function actionLabel(mod: RemediationModule, mins: number) {
    const started = mod.status !== "pending";
    return tr(started ? "student.continueWithTime" : "student.startWithTime", { min: mins });
  }

  return (
    <div className="container">
      <div className="row">
        <h1>{dash ? tr("student.greeting", { name: dash.full_name.split(" ")[0] }) : tr("student.loading")}</h1>
        {courses.length > 0 && (
          <select value={courseId ?? ""} onChange={(e) => setCourseId(Number(e.target.value))}
            style={{ width: 280 }}>
            {courses.map((c) => <option key={c.id} value={c.id}>{c.code} — {c.title}</option>)}
          </select>
        )}
      </div>

      {!dash ? <p className="muted">{tr("student.loading")}</p> : (
        <>
          <p className="muted">
            {tr("student.subtitle", { open: dash.open_modules.length, done: dash.completed_modules })}
          </p>

          {mastered.length > 0 && (
            <div className="card" style={{
              background: "#E5F5EC", border: "1px solid #BFE6CD", display: "flex",
              alignItems: "center", gap: 12, padding: "12px 16px",
            }}>
              <span style={{ fontSize: 22, lineHeight: 1 }}>🎉</span>
              <div>
                <div style={{ fontWeight: 700, color: "#1E7A43", fontSize: 14 }}>
                  {tr("student.celebrateTitle")}</div>
                <div style={{ fontSize: 13.5, color: "#22603C" }}>
                  {tr("student.celebrateBody", { names: mastered.map((m) => m.concept_name).join(", ") })}
                </div>
              </div>
            </div>
          )}

          <h2 style={{ marginTop: 28 }}>{tr("student.recommended")}</h2>
          <p className="muted" style={{ marginTop: -6, fontSize: 13 }}>{tr("student.recommendedHint")}</p>

          {topics.length === 0 ? (
            <div className="card muted">{tr("student.nothing")}</div>
          ) : (
            <>
              <div className="stack" style={{ gap: 10 }}>
                {(showAll ? topics : topics.slice(0, VISIBLE)).map((t) => {
                  const open = openTopic === t.conceptId;
                  const primary = t.modules[0];
                  const steps = topicSteps(t.modules);
                  const mins = estMinutes(steps);
                  return (
                    <div className="card" key={t.conceptId} style={{ padding: "12px 16px" }}>
                      <div className="row" style={{ alignItems: "center", cursor: "pointer", gap: 10 }}
                        onClick={() => setOpenTopic(open ? null : t.conceptId)}>
                        <div className="row" style={{ gap: 10, alignItems: "center", minWidth: 0 }}>
                          <span style={{ color: "var(--muted, #888)", fontSize: 12, width: 12 }}>
                            {open ? "▾" : "▸"}</span>
                          <h3 style={{ margin: 0, fontSize: 15 }}>{t.name}</h3>
                          <Pill status={t.status} />
                        </div>
                        {primary && (
                          <Link className="btn" to={moduleLink(primary.id)}
                            onClick={(e) => e.stopPropagation()} style={{ whiteSpace: "nowrap" }}>
                            {actionLabel(primary, mins)}
                          </Link>
                        )}
                      </div>
                      {open && (
                        <div style={{ marginTop: 10, paddingLeft: 22 }}>
                          <div style={{ fontWeight: 600, fontSize: 12.5, color: "#444",
                            textTransform: "uppercase", letterSpacing: ".4px", marginBottom: 4 }}>
                            {tr("student.whyTitle")}</div>
                          {t.modules.map((m) => (
                            <div key={m.id} style={{ marginBottom: t.modules.length > 1 ? 12 : 0 }}>
                              <p className="muted" style={{ fontSize: 13, margin: "0 0 6px" }}>
                                {m.rationale || tr("student.whyIntro")}</p>
                              <div className="row">
                                <span className="muted" style={{ fontSize: 12 }}>
                                  💬 {tr("student.interactiveTutor")} · {m.strategy.replace(/_/g, " ")} ·{" "}
                                  {tr("student.stepsMeta", { count: m.activities?.length || steps,
                                    min: estMinutes(m.activities?.length || steps) })}
                                </span>
                                {t.modules.length > 1 && (
                                  <Link className="btn secondary" to={moduleLink(m.id)}
                                    style={{ padding: "5px 12px", whiteSpace: "nowrap" }}>
                                    {actionLabel(m, estMinutes(m.activities?.length || 3))}
                                  </Link>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
              {topics.length > VISIBLE && !showAll && (
                <button className="btn secondary" style={{ marginTop: 12 }} onClick={() => setShowAll(true)}>
                  Show {topics.length - VISIBLE} more {topics.length - VISIBLE === 1 ? "topic" : "topics"}
                </button>
              )}
            </>
          )}

          <h2 style={{ marginTop: 32 }}>{tr("student.topicsOverview")}</h2>
          <div className="card" style={{ background: "var(--soft)", marginBottom: 12 }}>
            <p className="muted" style={{ margin: 0, fontSize: 13 }}>
              <strong>{tr("student.noteLabel")}</strong> {tr("student.masteryNote")}
            </p>
          </div>

          {dash.masteries.length === 0 ? (
            <div className="card muted">{tr("student.noData")}</div>
          ) : (
            <div className="card">
              <div className="stack" style={{ gap: 6 }}>
                {(["at_risk", "developing", "mastered"] as Mastery["status"][]).map((status) => {
                  const items = dash.masteries
                    .filter((m) => m.status === status)
                    .sort((a, b) => a.mastery_score - b.mastery_score);
                  if (items.length === 0) return null;
                  const g = SUP[status];
                  const groupLabel = status === "at_risk" ? "student.groupNeeds"
                    : status === "developing" ? "student.groupImproving" : "student.groupMastered";
                  const isOpen = openGroups.has(status);
                  return (
                    <div key={status}>
                      <div className="row" style={{ alignItems: "center", cursor: "pointer", padding: "8px 2px" }}
                        onClick={() => setOpenGroups((prev) => {
                          const next = new Set(prev);
                          next.has(status) ? next.delete(status) : next.add(status);
                          return next;
                        })}>
                        <div className="row" style={{ gap: 9, alignItems: "center" }}>
                          <span style={{ color: "var(--muted,#888)", fontSize: 12, width: 12 }}>
                            {isOpen ? "▾" : "▸"}</span>
                          <span style={{ width: 10, height: 10, borderRadius: "50%", background: g.dot }} />
                          <span style={{ fontWeight: 600, fontSize: 14 }}>{tr(groupLabel)}</span>
                        </div>
                        <span className="muted" style={{ fontSize: 13 }}>{items.length}</span>
                      </div>
                      {isOpen && (
                        <div style={{ paddingLeft: 31, paddingBottom: 6 }}>
                          {items.map((m) => (
                            <div key={m.concept_id} style={{ marginBottom: 12 }}>
                              <div className="row" style={{ marginBottom: 4 }}>
                                <span style={{ fontWeight: 600, fontSize: 14 }}>{m.concept_name}</span>
                                <span className="muted" style={{ fontSize: 12 }}>
                                  {tr("student.confidenceLabel")}: {tr(confidenceKey(m.mastery_score))}
                                  {" · "}{tr("student.estMastery", { pct: pct(m.mastery_score) })}
                                </span>
                              </div>
                              <div className="bar">
                                <span style={{ width: pct(m.mastery_score), background: g.bar }} />
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
