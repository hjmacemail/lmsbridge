import { Fragment, useEffect, useState } from "react";
import { api } from "../api/client";
import type { ModuleWithStudent } from "../types";

export default function RemediationPanel({ courseId }: { courseId: number }) {
  const [modules, setModules] = useState<ModuleWithStudent[]>([]);
  const [open, setOpen] = useState<number | null>(null);
  useEffect(() => {
    api.courseRemediation(courseId).then(setModules).catch(() => setModules([]));
    setOpen(null);
  }, [courseId]);

  return (
    <div className="card">
      <h3>Remediation modules ({modules.length}) — click to inspect activities & responses</h3>
      <table>
        <thead>
          <tr><th>Student</th><th>Concept</th><th>Module</th><th>Strategy</th><th>Status</th></tr>
        </thead>
        <tbody>
          {modules.length === 0 &&
            <tr><td colSpan={5} className="muted">No modules generated yet.</td></tr>}
          {modules.map((m) => (
            <Fragment key={m.id}>
              <tr style={{ cursor: "pointer" }}
                onClick={() => setOpen(open === m.id ? null : m.id)}>
                <td style={{ fontWeight: 600 }}>{open === m.id ? "▾ " : "▸ "}{m.student_name}</td>
                <td>{m.concept_name}</td>
                <td className="muted">{m.title}</td>
                <td className="muted">{m.strategy.replace(/_/g, " ")}</td>
                <td><span className={`pill ${m.status}`}>{m.status.replace("_", " ")}</span></td>
              </tr>
              {open === m.id && (
                <tr>
                  <td colSpan={5} style={{ background: "var(--soft)" }}>
                    <div style={{ padding: "8px 4px" }}>
                      {m.rationale && <p className="muted" style={{ marginTop: 0 }}>{m.rationale}</p>}
                      {m.grounded_on?.length ? (
                        <p style={{ fontSize: 12 }} className="muted">
                          Grounded in: {m.grounded_on.join(", ")}
                        </p>
                      ) : null}

                      {/* Live tutoring-session transcript */}
                      {m.transcript && m.transcript.length > 0 ? (
                        <div>
                          <div className="muted" style={{ fontSize: 12, marginBottom: 6 }}>
                            Tutoring session transcript
                          </div>
                          <div className="chat-log" style={{ borderRadius: 10, maxHeight: 360 }}>
                            {m.transcript.map((t, i) => (
                              <div key={i} className={`bubble ${t.role}`}>
                                {t.role === "tutor" && <div className="bubble-who">AI Tutor</div>}
                                <div className="bubble-text">{t.content}</div>
                              </div>
                            ))}
                          </div>
                        </div>
                      ) : (
                        <p className="muted" style={{ fontSize: 13 }}>
                          Session not started yet.
                        </p>
                      )}

                      {/* Session plan (the tutor's internal checkpoints) */}
                      {m.activities.length > 0 && (
                        <details style={{ marginTop: 10 }}>
                          <summary className="muted" style={{ fontSize: 12, cursor: "pointer" }}>
                            Session plan ({m.activities.length} checkpoints)
                          </summary>
                          {m.activities.map((a) => (
                            <div key={a.id} style={{ fontSize: 13, padding: "4px 0" }}>
                              <span className="type">{a.activity_type}</span> {a.prompt}
                            </div>
                          ))}
                        </details>
                      )}
                    </div>
                  </td>
                </tr>
              )}
            </Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
}
