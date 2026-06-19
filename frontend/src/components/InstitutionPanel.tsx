import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { InstitutionUsage, LicenseStatus } from "../types";

export default function InstitutionPanel() {
  const [u, setU] = useState<InstitutionUsage | null>(null);
  const [lic, setLic] = useState<LicenseStatus | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api.institutionUsage().then(setU).catch((e) => setErr((e as Error).message));
    api.licenseStatus().then(setLic).catch(() => undefined);
  }, []);

  if (err) return <div className="card error">{err}</div>;
  if (!u) return <p className="muted">Loading…</p>;

  const pct = (n: number) => `${Math.round(n * 100)}%`;
  // Billing/subscription only applies to a hosted (multi-tenant SaaS) deployment. In the
  // free, self-hosted community mode there is no subscription to show.
  const t = lic?.deployment_mode === "hosted" ? lic?.tenant : undefined;
  const statusCls = t?.subscription_status === "active" ? "mastered"
    : t?.subscription_status === "trial" ? "developing" : "at_risk";

  return (
    <>
      <div className="row" style={{ alignItems: "baseline" }}>
        <h2 style={{ margin: 0 }}>{u.tenant_name} — usage</h2>
        <span className={`pill ${u.lms_connected ? "mastered" : "developing"}`}>
          {u.lms_connected ? "LMS connected" : "No LMS connected"}
        </span>
      </div>

      {t && (
        <div className="card" style={{ marginTop: 12, background: "var(--soft)" }}>
          <div className="row" style={{ alignItems: "baseline", gap: 10 }}>
            <strong>Subscription</strong>
            <span className={`pill ${statusCls}`}>{t.subscription_status}</span>
            <span className="muted" style={{ fontSize: 13 }}>
              plan {t.plan} · {t.seats_used}{t.seat_limit != null ? ` / ${t.seat_limit}` : ""} seats
              {t.license_expires_at ? ` · renews ${t.license_expires_at.slice(0, 10)}` : ""}
            </span>
          </div>
          <p className="muted" style={{ margin: "6px 0 0", fontSize: 12 }}>
            Billing and seats are managed by LMS Bridge. Contact your account rep to change your plan.
          </p>
        </div>
      )}
      <p className="muted" style={{ marginTop: 6, fontSize: 13, maxWidth: 720 }}>
        Institution-wide adoption metrics. This view is aggregate by design — individual student
        names, scores, and answers stay with course instructors, not the institution admin.
      </p>

      <div className="grid cols-4" style={{ marginTop: 18 }}>
        <div className="card"><div className="muted">Active courses</div>
          <div className="kpi">{u.courses}</div></div>
        <div className="card"><div className="muted">Students reached</div>
          <div className="kpi">{u.students}</div></div>
        <div className="card"><div className="muted">Instructors</div>
          <div className="kpi">{u.instructors}</div></div>
        <div className="card"><div className="muted">Tutor sessions started</div>
          <div className="kpi">{u.sessions_started}</div></div>
      </div>

      <div className="grid cols-3" style={{ marginTop: 14 }}>
        <div className="card"><div className="muted">Remediation generated</div>
          <div className="kpi">{u.modules_generated}</div></div>
        <div className="card"><div className="muted">Remediation completed</div>
          <div className="kpi">{u.modules_completed}</div></div>
        <div className="card"><div className="muted">Completion rate</div>
          <div className="kpi">{pct(u.completion_rate)}</div></div>
      </div>

      <h3 style={{ marginTop: 26 }}>By course</h3>
      <div className="card">
        <table>
          <thead><tr>
            <th>Course</th><th>Students</th><th>Sessions completed</th><th>Avg mastery</th>
          </tr></thead>
          <tbody>
            {u.course_rows.length === 0 &&
              <tr><td colSpan={4} className="muted">No course activity yet.</td></tr>}
            {u.course_rows.map((c) => (
              <tr key={c.course_id}>
                <td><strong>{c.code}</strong> — {c.title}</td>
                <td>{c.students}</td>
                <td>{c.modules_completed}</td>
                <td>{c.students > 0 ? pct(c.avg_mastery) : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
