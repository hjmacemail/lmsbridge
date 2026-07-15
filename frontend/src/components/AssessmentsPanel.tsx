import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../api/client";
import type { AssessmentBreakdown } from "../types";

function pct(n: number) { return `${Math.round(n * 100)}%`; }

export default function AssessmentsPanel({ courseId }: { courseId: number }) {
  const { t } = useTranslation();
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
      setNote(t("instructor.assessments.savedRecompute"));
    } catch {
      load(); // revert on failure
    }
  }

  async function recompute() {
    setBusy(true); setNote(null);
    try {
      const r = await api.recompute(courseId);
      setNote(t("instructor.assessments.recomputed", { results: r.results_replayed, modules: r.modules_triggered }));
      load();
    } finally {
      setBusy(false);
    }
  }

  async function syncLms() {
    setBusy(true); setNote(null);
    try {
      const r = await api.syncAssessments(courseId);
      setNote(t("instructor.assessments.importedFromLms", { n: r.assessments }));
      load();
    } catch (e) {
      setNote((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  if (data.length === 0)
    return (
      <div className="card">
        <p className="muted" style={{ marginTop: 0 }}>
          {t("instructor.assessments.emptyIntro")}
        </p>
        <button className="btn" onClick={syncLms} disabled={busy}>
          {busy ? t("instructor.assessments.syncing") : t("instructor.assessments.syncFromLms")}
        </button>
        {note && <p className="muted" style={{ fontSize: 13 }}>{note}</p>}
      </div>
    );

  const disabledCount = data.filter((a) => !a.adaptive_enabled).length;

  return (
    <div className="grid" style={{ gap: 16 }}>
      <div className="card" style={{ background: "var(--soft)" }}>
        <div className="row">
          <div>
            <h3 style={{ marginBottom: 2 }}>{t("instructor.assessments.sourcesTitle")}</h3>
            <p className="muted" style={{ margin: 0, fontSize: 13 }}>
              {t("instructor.assessments.sourcesHelp")}{" "}
              {disabledCount > 0 && <strong>{t("instructor.assessments.disabledCount", { count: disabledCount })}</strong>}
            </p>
          </div>
          <div className="row" style={{ gap: 8 }}>
            <button className="btn" onClick={syncLms} disabled={busy}>
              {busy ? t("instructor.assessments.syncing") : t("instructor.assessments.syncFromLms")}
            </button>
            <button className="btn" onClick={recompute} disabled={busy}>
              {busy ? t("instructor.assessments.recomputing") : t("instructor.assessments.recompute")}
            </button>
          </div>
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
                  <span className="pill at_risk" style={{ marginLeft: 4 }}>{t("instructor.assessments.excluded")}</span>}
              </h3>
              <span className="muted" style={{ fontSize: 13 }}>
                {a.type} · {t("instructor.assessments.submissions", { count: a.submissions })}
              </span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
              <label className="switch" title="Use this assessment for adaptive learning">
                <input type="checkbox" checked={a.adaptive_enabled}
                  onChange={(e) => toggle(a.assessment_id, e.target.checked)} />
                <span className="slider" />
                <span className="switch-label">{a.adaptive_enabled ? t("instructor.assessments.adaptive") : t("instructor.assessments.excludedLabel")}</span>
              </label>
              <div style={{ textAlign: "right" }}>
                <div className="muted" style={{ fontSize: 12 }}>{t("instructor.assessments.classAverage")}</div>
                <div className="kpi" style={{ fontSize: 22 }}>{pct(a.avg_score)}</div>
              </div>
            </div>
          </div>

          <table style={{ marginTop: 10 }}>
            <thead><tr><th>{t("instructor.assessments.thConcept")}</th><th>{t("instructor.assessments.thClassAverage")}</th><th>{t("instructor.assessments.thDataPoints")}</th></tr></thead>
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
                {t("instructor.assessments.sampleRubric")}
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
