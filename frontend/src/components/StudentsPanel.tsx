import { Fragment, useEffect, useState } from "react";
import { api } from "../api/client";
import type { ResultDetail, RosterEntry, StudentDetailData } from "../types";

function pct(n: number) { return `${Math.round(n * 100)}%`; }
function masteryClass(s: string) {
  return s === "mastered" ? "mastered" : s === "at_risk" ? "at_risk" : "developing";
}

function McqDetail({ result }: { result: ResultDetail }) {
  const mcq = result.item_scores.filter((i) => i.choices && i.choices.length);
  if (mcq.length === 0)
    return <div className="muted" style={{ fontSize: 13, padding: "4px 0" }}>
      Rubric-graded — no multiple-choice answers.</div>;
  return (
    <div style={{ padding: "4px 0 8px" }}>
      {mcq.map((q, i) => (
        <div key={i} className="activity" style={{ background: "#fff", padding: 12 }}>
          <p style={{ margin: "0 0 8px", fontWeight: 600, fontSize: 14 }}>
            {q.is_correct
              ? <span style={{ color: "var(--mastered)" }}>✓ </span>
              : <span style={{ color: "var(--at-risk)" }}>✗ </span>}
            {q.question}
          </p>
          <div className="stack" style={{ gap: 4 }}>
            {(q.choices || []).map((c) => {
              const chosen = c === q.selected;
              const right = c === q.correct;
              const bg = right ? "#f0fdf4" : chosen ? "#fef2f2" : "transparent";
              const color = right ? "var(--mastered)" : chosen ? "var(--at-risk)" : "inherit";
              return (
                <div key={c} style={{
                  fontSize: 13, padding: "4px 8px", borderRadius: 6, background: bg, color,
                }}>
                  {right ? "● " : chosen ? "✗ " : "○ "}{c}
                  {chosen && !right && <em> — student's answer</em>}
                  {right && <em> — correct</em>}
                </div>
              );
            })}
          </div>
          {!q.is_correct && q.misconception && (
            <div className="feedback" style={{ marginTop: 8, fontSize: 13 }}>
              <strong>Reveals misconception:</strong> {q.misconception}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function StudentDrill({ courseId, studentId }: { courseId: number; studentId: number }) {
  const [data, setData] = useState<StudentDetailData | null>(null);
  const [openResult, setOpenResult] = useState<number | null>(null);
  useEffect(() => {
    api.studentDetail(courseId, studentId).then(setData).catch(() => setData(null));
  }, [courseId, studentId]);
  if (!data) return <tr><td colSpan={5} className="muted">Loading…</td></tr>;

  return (
    <tr>
      <td colSpan={5} style={{ background: "var(--soft)" }}>
        <div style={{ padding: "6px 4px" }}>
          <h3 style={{ marginBottom: 8 }}>Concept mastery</h3>
          <div className="grid cols-2">
            {data.masteries.map((m) => (
              <div key={m.concept_id} className="row" style={{ gap: 8 }}>
                <span style={{ fontSize: 13, minWidth: 150 }}>{m.concept_name}</span>
                <div className="bar" style={{ flex: 1 }}>
                  <span style={{ width: pct(m.mastery_score),
                    background: `var(--${masteryClass(m.status)})` }} />
                </div>
                <span style={{ fontSize: 12, minWidth: 38 }}>{pct(m.mastery_score)}</span>
              </div>
            ))}
          </div>

          <h3 style={{ margin: "16px 0 8px" }}>
            Assessment results <span className="muted" style={{ fontSize: 12, fontWeight: 400 }}>
              — click a quiz/exam to see the student's answers</span>
          </h3>
          <table>
            <thead><tr><th>Assessment</th><th>Type</th><th>Score</th>
              <th>Attempts</th><th>Time</th><th>Feedback</th></tr></thead>
            <tbody>
              {data.results.map((r) => {
                const hasMcq = r.item_scores.some((i) => i.choices && i.choices.length);
                return (
                  <Fragment key={r.id}>
                    <tr style={{ cursor: hasMcq ? "pointer" : "default" }}
                      onClick={() => hasMcq && setOpenResult(openResult === r.id ? null : r.id)}>
                      <td>{hasMcq && (openResult === r.id ? "▾ " : "▸ ")}{r.assessment_title}
                        {r.submitted_late &&
                          <span className="pill at_risk" style={{ marginLeft: 6 }}>late</span>}</td>
                      <td className="muted">{r.assessment_type}</td>
                      <td style={{ fontWeight: 600 }}>{pct(r.score)}</td>
                      <td>{r.attempts ?? "—"}</td>
                      <td className="muted">
                        {r.time_on_task_minutes ? `${r.time_on_task_minutes}m` : "—"}</td>
                      <td className="muted" style={{ fontSize: 12 }}>{r.rubric_feedback || "—"}</td>
                    </tr>
                    {openResult === r.id && (
                      <tr><td colSpan={6} style={{ background: "#fff" }}>
                        <McqDetail result={r} /></td></tr>
                    )}
                  </Fragment>
                );
              })}
            </tbody>
          </table>

          <h3 style={{ margin: "16px 0 8px" }}>Remediation modules ({data.modules.length})</h3>
          <div className="stack">
            {data.modules.length === 0 && <span className="muted">None generated.</span>}
            {data.modules.map((m) => (
              <div key={m.id} className="row card" style={{ padding: 12 }}>
                <div>
                  <strong>{m.title}</strong>
                  <div className="muted" style={{ fontSize: 12 }}>
                    {m.concept_name} · {m.activity_count} activities · {m.response_count} responses
                    {m.grounded_on?.length ? ` · grounded in ${m.grounded_on.join(", ")}` : ""}
                  </div>
                </div>
                <span className={`pill ${m.status}`}>{m.status.replace("_", " ")}</span>
              </div>
            ))}
          </div>
        </div>
      </td>
    </tr>
  );
}

export default function StudentsPanel({ courseId }: { courseId: number }) {
  const [roster, setRoster] = useState<RosterEntry[]>([]);
  const [open, setOpen] = useState<number | null>(null);

  useEffect(() => {
    api.roster(courseId).then(setRoster).catch(() => setRoster([]));
    setOpen(null);
  }, [courseId]);

  return (
    <div className="card">
      <h3>Roster ({roster.length}) — click a student to drill down</h3>
      <table>
        <thead>
          <tr><th>Student</th><th>Avg mastery</th><th>At-risk concepts</th>
            <th>Open</th><th>Completed</th></tr>
        </thead>
        <tbody>
          {roster.map((s) => (
            <Fragment key={s.student_id}>
              <tr style={{ cursor: "pointer" }}
                onClick={() => setOpen(open === s.student_id ? null : s.student_id)}>
                <td style={{ fontWeight: 600 }}>
                  {open === s.student_id ? "▾ " : "▸ "}{s.full_name}
                  <div className="muted" style={{ fontSize: 12 }}>{s.email}</div>
                </td>
                <td>
                  <div className="row" style={{ gap: 8 }}>
                    <div className="bar" style={{ width: 100 }}>
                      <span style={{ width: pct(s.avg_mastery),
                        background: s.avg_mastery <= 0.7 ? "var(--at-risk)"
                          : s.avg_mastery < 0.85 ? "var(--developing)" : "var(--mastered)" }} />
                    </div>
                    {pct(s.avg_mastery)}
                  </div>
                </td>
                <td>{s.at_risk_concepts > 0
                  ? <span className="pill at_risk">{s.at_risk_concepts}</span> : "0"}</td>
                <td>{s.open_modules}</td>
                <td>{s.completed_modules}</td>
              </tr>
              {open === s.student_id &&
                <StudentDrill courseId={courseId} studentId={s.student_id} />}
            </Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
}
