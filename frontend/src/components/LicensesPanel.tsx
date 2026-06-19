import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { LicenseStatus, TenantLicenseRow } from "../types";

const STATUSES = ["active", "trial", "expired", "suspended", "canceled"];
const PLANS = ["free", "pilot", "standard", "enterprise"];

function statusPill(s: string) {
  const cls = s === "active" ? "mastered"
    : s === "trial" ? "developing" : "at_risk";
  return <span className={`pill ${cls}`}>{s}</span>;
}

export default function LicensesPanel() {
  const [rows, setRows] = useState<TenantLicenseRow[]>([]);
  const [status, setStatus] = useState<LicenseStatus | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [note, setNote] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);

  function load() {
    api.licenses().then(setRows).catch((e) => setErr((e as Error).message));
    api.licenseStatus().then(setStatus).catch(() => undefined);
  }
  useEffect(load, []);

  async function save(r: TenantLicenseRow) {
    setBusyId(r.id); setErr(null); setNote(null);
    try {
      await api.updateTenantLicense(r.id, {
        subscription_status: r.subscription_status,
        plan: r.plan,
        seat_limit: r.seat_limit ?? null,
        license_expires_at: r.license_expires_at || null,
      });
      setNote(`Saved ${r.name}.`);
      load();
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setBusyId(null);
    }
  }

  function patch(id: number, k: keyof TenantLicenseRow, v: unknown) {
    setRows((cur) => cur.map((r) => (r.id === id ? { ...r, [k]: v } : r)));
  }

  return (
    <>
      <h2 style={{ margin: 0 }}>Licenses</h2>
      <p className="muted" style={{ marginTop: 6, fontSize: 13, maxWidth: 760 }}>
        Each institution is one tenant. Set its subscription, plan, seat cap, and expiry —
        these are enforced at every LTI launch. Suspended/expired institutions see a
        “tool unavailable” screen instead of signing in.
      </p>

      {status && (
        <div className="card" style={{ marginBottom: 16, background: "var(--soft)" }}>
          <strong>Licensing mode:</strong>{" "}
          {status.mode === "self_hosted" ? "Self-hosted (signed license file)" : "SaaS (per-tenant)"}
          {status.enforcement_disabled &&
            <span className="pill at_risk" style={{ marginLeft: 8 }}>enforcement disabled</span>}
          {status.mode === "self_hosted" && status.self_hosted && (
            <div className="muted" style={{ marginTop: 6, fontSize: 13 }}>
              {status.self_hosted.ok
                ? `Licensed to ${status.self_hosted.customer ?? "—"} · plan ${status.self_hosted.plan ?? "—"} · `
                  + `${status.self_hosted.seats ?? "∞"} seats · expires `
                  + `${status.self_hosted.expires_at?.slice(0, 10) ?? "—"}`
                : `⚠ ${status.self_hosted.detail}`}
            </div>
          )}
        </div>
      )}

      {err && <div className="error">{err}</div>}
      {note && <div style={{ color: "var(--mastered)", fontSize: 14, marginBottom: 8 }}>{note}</div>}

      <div className="card">
        <table>
          <thead><tr>
            <th>Institution</th><th>Status</th><th>Plan</th>
            <th>Seats (used / cap)</th><th>Expires</th><th></th>
          </tr></thead>
          <tbody>
            {rows.length === 0 &&
              <tr><td colSpan={6} className="muted">No institutions yet.</td></tr>}
            {rows.map((r) => (
              <tr key={r.id}>
                <td><strong>{r.name}</strong><div className="muted" style={{ fontSize: 12 }}>{r.slug}</div></td>
                <td>
                  <select value={r.subscription_status}
                    onChange={(e) => patch(r.id, "subscription_status", e.target.value)}>
                    {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
                  </select>
                  <div style={{ marginTop: 4 }}>{statusPill(r.subscription_status)}</div>
                </td>
                <td>
                  <select value={r.plan} onChange={(e) => patch(r.id, "plan", e.target.value)}>
                    {PLANS.map((p) => <option key={p} value={p}>{p}</option>)}
                  </select>
                </td>
                <td>
                  <span style={{ marginRight: 6 }}>{r.seats_used} /</span>
                  <input type="number" min={0} style={{ width: 80 }}
                    value={r.seat_limit ?? ""}
                    placeholder="∞"
                    onChange={(e) => patch(r.id, "seat_limit",
                      e.target.value === "" ? null : Number(e.target.value))} />
                </td>
                <td>
                  <input type="date"
                    value={r.license_expires_at ? r.license_expires_at.slice(0, 10) : ""}
                    onChange={(e) => patch(r.id, "license_expires_at",
                      e.target.value ? `${e.target.value}T23:59:59Z` : null)} />
                </td>
                <td>
                  <button className="btn secondary" disabled={busyId === r.id}
                    onClick={() => save(r)}>
                    {busyId === r.id ? "Saving…" : "Save"}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
