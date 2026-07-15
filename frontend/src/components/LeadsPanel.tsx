import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { Lead } from "../types";

export default function LeadsPanel() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api.leads().then(setLeads).catch((e) => setErr((e as Error).message));
  }, []);

  if (err) return <div className="card error">{err}</div>;

  return (
    <div className="card">
      <div className="row">
        <h3>Messages ({leads.length})</h3>
        <span className="muted" style={{ fontSize: 13 }}>
          Contact, demo &amp; purchase requests submitted from the marketing site.
        </span>
      </div>
      <table>
        <thead>
          <tr><th>When</th><th>Name</th><th>Email</th><th>Organization</th>
            <th>Role</th><th>Interest</th><th>Message</th></tr>
        </thead>
        <tbody>
          {leads.length === 0 &&
            <tr><td colSpan={7} className="muted">No leads yet.</td></tr>}
          {leads.map((l) => (
            <tr key={l.id}>
              <td className="muted" style={{ fontSize: 12, whiteSpace: "nowrap" }}>
                {new Date(l.created_at).toLocaleDateString()}</td>
              <td style={{ fontWeight: 600 }}>{l.name}</td>
              <td><a href={`mailto:${l.email}`}>{l.email}</a></td>
              <td>{l.organization || "—"}</td>
              <td className="muted" style={{ fontSize: 13 }}>{l.role || "—"}</td>
              <td>
                <span className="pill pending">{l.kind}</span>
                {l.plan ? <span className="muted" style={{ fontSize: 12 }}> · {l.plan}</span> : null}
              </td>
              <td className="muted" style={{ fontSize: 13, maxWidth: 280 }}>{l.message || "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
