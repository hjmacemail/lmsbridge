import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../api/client";
import type { Course, Mastery, RemediationModule, StudentDashboard as Dash } from "../types";

function pct(n: number) { return `${Math.round(n * 100)}%`; }
function masteryColor(status: Mastery["status"]) {
  return status === "mastered" ? "var(--mastered)"
    : status === "at_risk" ? "var(--at-risk)" : "var(--developing)";
}
const RISK_ORDER: Record<string, number> = { at_risk: 0, developing: 1, mastered: 2 };

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

  useEffect(() => {
    api.myCourses().then((cs) => {
      setCourses(cs);
      if (cs.length) setCourseId(cs[0].id);
      else api.myDashboard().then(setDash); // not enrolled in any course
    }).catch((e) => setErr((e as Error).message));
  }, []);

  useEffect(() => {
    if (courseId == null) return;
    setDash(null);
    api.myDashboard(courseId).then(setDash).catch((e) => setErr((e as Error).message));
  }, [courseId]);

  // Group open modules by concept (topic), enrich with mastery risk, sort by risk.
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

  if (err) return <div className="container"><div className="card error">{err}</div></div>;

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

          <h2 style={{ marginTop: 28 }}>{tr("student.recommended")}</h2>
          <p className="muted" style={{ marginTop: -6, fontSize: 13 }}>
            {tr("student.recommendedHint")}
          </p>
          {topics.length === 0 ? (
            <div className="card muted">{tr("student.nothing")}</div>
          ) : (
            <div className="stack" style={{ gap: 18 }}>
              {topics.map((t) => (
                <div key={t.conceptId}>
                  <div className="row" style={{ marginBottom: 8 }}>
                    <div className="row" style={{ gap: 10 }}>
                      <h3 style={{ margin: 0 }}>{t.name}</h3>
                      <span className={`pill ${t.status}`}>{tr("status." + t.status)}</span>
                    </div>
                    <div className="row" style={{ gap: 8, minWidth: 200 }}>
                      <div className="bar" style={{ width: 120 }}>
                        <span style={{ width: pct(t.score), background: masteryColor(t.status) }} />
                      </div>
                      <span className="muted" style={{ fontSize: 12 }}>{tr("student.mastery", { pct: pct(t.score) })}</span>
                    </div>
                  </div>
                  <div className="grid cols-2">
                    {t.modules.map((m) => (
                      <div className="card" key={m.id}>
                        <div className="row">
                          <h3 style={{ fontSize: 14 }}>{m.title}</h3>
                          <span className={`pill ${m.status}`}>{tr("status." + m.status)}</span>
                        </div>
                        <p className="muted" style={{ fontSize: 13 }}>{m.rationale}</p>
                        <div className="row">
                          <span className="muted" style={{ fontSize: 12 }}>
                            💬 {tr("student.interactiveTutor")} · {m.strategy.replace(/_/g, " ")}
                          </span>
                          <Link className="btn" to={moduleLink(m.id)}>
                            {m.status === "pending" ? tr("student.startSession") : tr("student.continue")}
                          </Link>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          <h2 style={{ marginTop: 32 }}>{tr("student.masteryTitle")}</h2>
          <div className="card" style={{ background: "var(--soft)", marginBottom: 12 }}>
            <p className="muted" style={{ margin: 0, fontSize: 13 }}>
              <strong>{tr("student.noteLabel")}</strong> {tr("student.masteryNote")}
            </p>
          </div>
          <div className="card">
            <div className="stack">
              {dash.masteries.length === 0 && <span className="muted">{tr("student.noData")}</span>}
              {dash.masteries
                .slice()
                .sort((a, b) =>
                  (RISK_ORDER[a.status] - RISK_ORDER[b.status])
                  || (a.mastery_score - b.mastery_score))
                .map((m) => (
                  <div key={m.concept_id} style={{ marginBottom: 10 }}>
                    <div className="row" style={{ marginBottom: 4 }}>
                      <span style={{ fontWeight: 600, fontSize: 14 }}>{m.concept_name}</span>
                      <span className={`pill ${m.status}`}>{tr("status." + m.status)}</span>
                    </div>
                    <div className="bar">
                      <span style={{
                        width: pct(m.mastery_score),
                        background: masteryColor(m.status),
                      }} />
                    </div>
                  </div>
                ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
