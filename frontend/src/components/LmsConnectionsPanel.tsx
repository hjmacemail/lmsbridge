import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import type { LtiRegistrationView, LtiToolConfig } from "../types";

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="row" style={{ alignItems: "center", gap: 10, padding: "3px 0" }}>
      <span className="muted" style={{ minWidth: 180, fontSize: 12 }}>{label}</span>
      <code style={{ flex: 1, fontSize: 12, wordBreak: "break-all" }}>{value}</code>
      <button className="btn secondary" style={{ padding: "4px 8px", fontSize: 12 }}
        onClick={() => navigator.clipboard?.writeText(value)}>Copy</button>
    </div>
  );
}

const EMPTY = {
  name: "", issuer: "", client_id: "", auth_login_url: "",
  auth_token_url: "", key_set_url: "", audience: "", deployment_id: "",
};

export default function LmsConnectionsPanel() {
  const [cfg, setCfg] = useState<LtiToolConfig | null>(null);
  const [regs, setRegs] = useState<LtiRegistrationView[]>([]);
  const [form, setForm] = useState({ ...EMPTY });
  const [showForm, setShowForm] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [note, setNote] = useState<string | null>(null);

  const load = useCallback(() => {
    api.ltiConfig().then(setCfg).catch(() => {});
    api.ltiRegistrations().then(setRegs).catch((e) => setErr((e as Error).message));
  }, []);
  useEffect(load, [load]);

  async function create(e: React.FormEvent) {
    e.preventDefault();
    setErr(null); setNote(null);
    try {
      await api.createLtiRegistration({
        ...form, audience: form.audience || undefined,
        deployment_id: form.deployment_id || undefined,
      });
      setForm({ ...EMPTY }); setShowForm(false); setNote("LMS connected.");
      load();
    } catch (e) {
      setErr((e as Error).message);
    }
  }

  async function remove(id: number) {
    await api.deleteLtiRegistration(id);
    load();
  }

  const F = (k: keyof typeof EMPTY, label: string, ph = "") => (
    <div className="field" style={{ marginBottom: 10 }}>
      <label>{label}</label>
      <input value={form[k]} onChange={(e) => setForm({ ...form, [k]: e.target.value })}
        placeholder={ph} />
    </div>
  );

  return (
    <div className="grid" style={{ gap: 16, maxWidth: 860 }}>
      <div className="card">
        <h3>Tool details (give these to your LMS admin)</h3>
        <p className="muted" style={{ marginTop: 0, fontSize: 13 }}>
          Register LMS Bridge as an LTI 1.3 / Advantage tool in your LMS using these URLs. Canvas and
          Moodle can auto-configure via the Dynamic Registration URL; Blackboard and Brightspace use
          the individual URLs, then you add the LMS's issuer/client id below.
        </p>
        {cfg && (
          <div>
            <Row label="OIDC login URL" value={cfg.oidc_initiation_url} />
            <Row label="Launch / target URL" value={cfg.target_link_uri} />
            <Row label="Redirect URL" value={cfg.redirect_uris[0]} />
            <Row label="Public JWKS URL" value={cfg.public_jwks_url} />
            <Row label="Dynamic Registration URL" value={cfg.dynamic_registration_url} />
          </div>
        )}
      </div>

      <div className="card">
        <div className="row">
          <h3>Connected LMS platforms ({regs.length})</h3>
          <button className="btn" onClick={() => setShowForm((s) => !s)}>
            {showForm ? "Cancel" : "+ Add LMS manually"}
          </button>
        </div>
        {note && <div className="ok" style={{ marginTop: 8 }}>{note}</div>}
        {err && <div className="error">{err}</div>}

        {showForm && (
          <form onSubmit={create} style={{ marginTop: 12, borderTop: "1px solid var(--border)",
            paddingTop: 12 }}>
            <p className="muted" style={{ fontSize: 13, marginTop: 0 }}>
              Enter the values your LMS gives you after you register the tool there.
            </p>
            <div className="grid cols-2">
              {F("name", "Name", "e.g. State U Canvas")}
              {F("issuer", "Issuer / Platform ID", "https://canvas.instructure.com")}
              {F("client_id", "Client ID")}
              {F("deployment_id", "Deployment ID")}
              {F("auth_login_url", "OIDC auth endpoint")}
              {F("auth_token_url", "Access-token endpoint")}
              {F("key_set_url", "Platform JWKS endpoint")}
              {F("audience", "Token audience (optional)")}
            </div>
            <button className="btn" style={{ marginTop: 8 }}>Connect LMS</button>
          </form>
        )}

        <table style={{ marginTop: 12 }}>
          <thead><tr><th>Name</th><th>Issuer</th><th>Client ID</th><th>Deployments</th><th></th></tr></thead>
          <tbody>
            {regs.length === 0 &&
              <tr><td colSpan={5} className="muted">No LMS connected yet.</td></tr>}
            {regs.map((r) => (
              <tr key={r.id}>
                <td style={{ fontWeight: 600 }}>{r.name}
                  {r.auto_register_deployments &&
                    <span className="pill mastered" style={{ marginLeft: 6 }}>dynamic</span>}</td>
                <td className="muted" style={{ fontSize: 12, wordBreak: "break-all" }}>{r.issuer}</td>
                <td className="muted" style={{ fontSize: 12 }}>{r.client_id}</td>
                <td className="muted" style={{ fontSize: 12 }}>
                  {r.deployments.map((d) => d.deployment_id).join(", ") || "—"}</td>
                <td style={{ textAlign: "right" }}>
                  <button className="btn secondary" style={{ padding: "6px 10px", color: "var(--at-risk)" }}
                    onClick={() => remove(r.id)}>Remove</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
