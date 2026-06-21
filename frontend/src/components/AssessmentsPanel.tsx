import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import type { AssessmentBreakdown } from "../types";

function pct(n: number) { return `${Math.round(n * 100)}%`; }

export default function AssessmentsPanel({ courseId }: { courseId: number }) {
  const [data, setData] = useState<AssessmentBreakdown[]>([]);
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState<string | null>(null);

  const load = useCallback(() => {
    api.assessmentBreakdown(courseId).then(setData).catch(() => setData([]));
  }, [courseId]);
  useEffect(() => { load(); setNote(null); }, [load]);

  async function toggle(assessmentId: number, enabled: boolean) {
    setData((d) => d.map((a) =>
      a.assessment_id === assessmentId ? { ...a, adaptive_enabled: enabled } : a));
    try {
      await api.setAdaptive(assessmentId, enabled);
      setNote("Saved. Click “Recompute” to apply the change to mastery & remediation.");
    } catch {
      load(); // revert on failure
    }
  }

  async function recompute() {
    setBusy(true); setNote(null);
    try {
      const r = await api.recompute(courseId);
      setNote(`Recomputed from enabled assessments — replayed ${r.results_replayed} results, `
        + `triggered ${r.modules_triggered} new module(s).`);
      load();
    } finally {
      setBusy(false);
    }
  }

  if (data.length === 0)
    return (
      <div className="card muted">
        No assessments yet. They import automatically from your LMS gradebook the next time an
        instructor launches LMS Bridge from the course — or add one manually under Course Setup.
      </div>
    );

  const disabledCount = data.filter((a) => !a.adaptive_enabled).length;

  return (
    <div className="grid" style={{ gap: 16 }}>
      <div className="card" style={{ background: "var(--soft)" }}>
        <div className="row">
          <div>
            <h3 style={{ marginBottom: 2 }}>Adaptive learning sources</h3>
            <p className="muted" style={{ margin: 0, fontSize: 13 }}>
              Toggle which assessments feed the adaptive engine. Disabled assessments are still
              recorded and shown here, but their feedback won't affect mastery or trigger
              remediation. {disabledCount > 0 && <strong>{disabledCount} disabled.</strong>}
            </p>
          </div>
          <button className="btn" onClick={recompute} disabled={busy}>
            {busy ? "Recomputing…" : "Recompute adaptive model"}
          </button>
        </div>
        {note && <div className="feedback" style={{ marginTop: 10, fontSize: 13 }}>{note}</div>}
      </div>

      {data.map((a) => (
        <div key={a.assessment_id} className="card"
          style={{ opacity: a.adaptive_enabled ? 1 : 0.7 }}>
          <div className="row">
            <div>
              <h3 style={{ marginBottom: 2 }}>
                {a.title}{" "}
                {!a.adaptive_enabled &&
                  <span className="pill at_risk" style={{ marginLeft: 4 }}>excluded</span>}
              </h3>
              <span className="muted" style={{ fontSize: 13 }}>
                {a.type} · {a.submissions} submissions
              </span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
              <label className="switch" title="Use this assessment for adaptive learning">
                <input type="checkbox" checked={a.adaptive_enabled}
                  onChange={(e) => toggle(a.assessment_id, e.target.checked)} />
                <span className="slider" />
                <span className="switch-label">{a.adaptive_enabled ? "Adaptive" : "Excluded"}</span>
              </label>
              <div style={{ textAlign: "right" }}>
                <div className="muted" style={{ fontSize: 12 }}>class average</div>
                <div className="kpi" style={{ fontSize: 22 }}>{pct(a.avg_score)}</div>
              </div>
            </div>
          </div>

          <table style={{ marginTop: 10 }}>
            <thead><tr><th>Concept</th><th>Class average</th><th>Data points</th></tr></thead>
            <tbody>
              {a.concept_stats.map((c) => (
                <tr key={c.concept_key}>
                  <td style={{ fontWeight: 600 }}>{c.concept_name}</td>
                  <td>
                    <div className="row" style={{ gap: 8 }}>
                      <div className="bar" style={{ width: 140 }}>
                        <span style={{ width: pct(c.avg),
                          background: c.avg <= 0.7 ? "var(--at-risk)"
                            : c.avg < 0.85 ? "var(--developing)" : "var(--mastered)" }} />
                      </div>
                      {pct(c.avg)}
                    </div>
                  </td>
                  <td className="muted">{c.n}</td>
                </tr>
              ))}
            </tbody>
          </table>

          {a.sample_rubric_feedback.length > 0 && (
            <div style={{ marginTop: 10 }}>
              <div className="muted" style={{ fontSize: 12, marginBottom: 4 }}>
                Sample rubric-level feedback
              </div>
              {a.sample_rubric_feedback.map((f, i) => (
                <div key={i} className="feedback" style={{ marginTop: 6, fontSize: 13 }}>{f}</div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
