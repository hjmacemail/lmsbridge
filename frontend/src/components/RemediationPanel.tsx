import { Fragment, useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../api/client";
import type { ModuleWithStudent } from "../types";

type GroupBy = "student" | "concept";

function ModuleDetail({ m }: { m: ModuleWithStudent }) {
  const { t } = useTranslation();
  return (
    <div style={{ padding: "8px 4px" }}>
      {m.rationale && <p className="muted" style={{ marginTop: 0 }}>{m.rationale}</p>}
      {m.grounded_on?.length ? (
        <p style={{ fontSize: 12 }} className="muted">{t("instructor.remediation.groundedIn", { list: m.grounded_on.join(", ") })}</p>
      ) : null}
      {m.transcript && m.transcript.length > 0 ? (
        <div>
          <div className="muted" style={{ fontSize: 12, marginBottom: 6 }}>{t("instructor.remediation.transcript")}</div>
          <div className="chat-log" style={{ borderRadius: 10, maxHeight: 360 }}>
            {m.transcript.map((msg, i) => (
              <div key={i} className={`bubble ${msg.role}`}>
                {msg.role === "tutor" && <div className="bubble-who">{t("tutor.aiTutor")}</div>}
                <div className="bubble-text">{msg.content}</div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <p className="muted" style={{ fontSize: 13 }}>{t("instructor.remediation.notStarted")}</p>
      )}
      {m.activities.length > 0 && (
        <details style={{ marginTop: 10 }}>
          <summary className="muted" style={{ fontSize: 12, cursor: "pointer" }}>
            {t("instructor.remediation.sessionPlan", { count: m.activities.length })}
          </summary>
          {m.activities.map((a) => (
            <div key={a.id} style={{ fontSize: 13, padding: "4px 0" }}>
              <span className="type">{a.activity_type}</span> {a.prompt}
            </div>
          ))}
        </details>
      )}
    </div>
  );
}

export default function RemediationPanel({ courseId }: { courseId: number }) {
  const { t } = useTranslation();
  const [modules, setModules] = useState<ModuleWithStudent[]>([]);
  const [groupBy, setGroupBy] = useState<GroupBy>("student");
  const [openGroups, setOpenGroups] = useState<Set<string>>(new Set());
  const [openModule, setOpenModule] = useState<number | null>(null);

  useEffect(() => {
    api.courseRemediation(courseId).then(setModules).catch(() => setModules([]));
    setOpenGroups(new Set());
    setOpenModule(null);
  }, [courseId]);

  const groups = useMemo(() => {
    const map = new Map<string, ModuleWithStudent[]>();
    for (const m of modules) {
      const key = (groupBy === "student" ? m.student_name : m.concept_name) || "—";
      if (!map.has(key)) map.set(key, []);
      map.get(key)!.push(m);
    }
    return [...map.entries()].sort((a, b) => a[0].localeCompare(b[0]));
  }, [modules, groupBy]);

  const toggleGroup = (k: string) => setOpenGroups((prev) => {
    const next = new Set(prev);
    next.has(k) ? next.delete(k) : next.add(k);
    return next;
  });

  const summary = (mods: ModuleWithStudent[]) => {
    const done = mods.filter((m) => m.status === "completed").length;
    const active = mods.filter((m) => m.status === "in_progress").length;
    const parts = [t("instructor.remediation.summaryModules", { count: mods.length })];
    if (done) parts.push(t("instructor.remediation.summaryCompleted", { count: done }));
    if (active) parts.push(t("instructor.remediation.summaryInProgress", { count: active }));
    return parts.join(" · ");
  };

  const groupWord = (g: GroupBy) =>
    g === "student" ? t("instructor.remediation.groupStudent") : t("instructor.remediation.groupConcept");
  const secondCol = groupBy === "student" ? t("instructor.remediation.thConcept") : t("instructor.remediation.thStudent");

  return (
    <div className="card">
      <div className="row" style={{ alignItems: "center", marginBottom: 6 }}>
        <h3 style={{ margin: 0 }}>{t("instructor.remediation.title", { count: modules.length, group: groupWord(groupBy) })}</h3>
        <div style={{ display: "inline-flex", border: "1px solid var(--border,#e2e2ea)",
          borderRadius: 8, overflow: "hidden" }}>
          {(["student", "concept"] as GroupBy[]).map((g) => (
            <button key={g} onClick={() => { setGroupBy(g); setOpenGroups(new Set()); }}
              style={{ border: "none", padding: "5px 13px", fontSize: 13, cursor: "pointer",
                background: groupBy === g ? "var(--primary,#4f46e5)" : "#fff",
                color: groupBy === g ? "#fff" : "var(--ink,#333)",
                textTransform: "capitalize" }}>{groupWord(g)}</button>
          ))}
        </div>
      </div>
      <p className="muted" style={{ fontSize: 12.5, marginTop: 0 }}>
        {t("instructor.remediation.clickToExpand", { group: groupWord(groupBy) })}
      </p>
      <table>
        <thead>
          <tr><th>{groupBy === "student" ? t("instructor.remediation.thStudent") : t("instructor.remediation.thConcept")}</th><th>{secondCol}</th>
            <th>{t("instructor.remediation.thStrategy")}</th><th>{t("instructor.remediation.thStatus")}</th></tr>
        </thead>
        <tbody>
          {groups.length === 0 &&
            <tr><td colSpan={4} className="muted">{t("instructor.remediation.noModules")}</td></tr>}
          {groups.map(([key, mods]) => {
            const gOpen = openGroups.has(key);
            return (
              <Fragment key={key}>
                <tr style={{ cursor: "pointer", background: "var(--soft)" }} onClick={() => toggleGroup(key)}>
                  <td style={{ fontWeight: 700 }}>{gOpen ? "▾ " : "▸ "}{key}</td>
                  <td colSpan={3} className="muted" style={{ fontSize: 13 }}>{summary(mods)}</td>
                </tr>
                {gOpen && mods.map((m) => (
                  <Fragment key={m.id}>
                    <tr style={{ cursor: "pointer" }}
                      onClick={() => setOpenModule(openModule === m.id ? null : m.id)}>
                      <td style={{ paddingLeft: 26 }} className="muted">
                        {openModule === m.id ? "▾ " : "▸ "}
                        {groupBy === "student" ? m.concept_name : m.student_name}</td>
                      <td className="muted">{groupBy === "student" ? m.student_name : m.concept_name}</td>
                      <td className="muted">{t(`tutor.strategy.${m.strategy}`, { defaultValue: m.strategy.replace(/_/g, " ") })}</td>
                      <td><span className={`pill ${m.status}`}>{t(`status.${m.status}`, { defaultValue: m.status.replace("_", " ") })}</span></td>
                    </tr>
                    {openModule === m.id && (
                      <tr><td colSpan={4} style={{ background: "var(--soft)" }}><ModuleDetail m={m} /></td></tr>
                    )}
                  </Fragment>
                ))}
              </Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
