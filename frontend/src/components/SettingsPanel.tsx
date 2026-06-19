import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { TenantSettings } from "../types";

const PROVIDERS = [
  { v: "", label: "Server default (set by LLM_PROVIDER)" },
  { v: "azure_openai", label: "Azure OpenAI (your tenant — recommended)" },
  { v: "openai", label: "OpenAI" },
  { v: "anthropic", label: "Anthropic" },
  { v: "mock", label: "Local mock (no external calls)" },
];

export default function SettingsPanel() {
  const [t, setT] = useState<TenantSettings | null>(null);
  const [key, setKey] = useState("");
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api.getTenant().then(setT).catch((e) => setErr((e as Error).message));
  }, []);

  function set<K extends keyof TenantSettings>(k: K, v: TenantSettings[K]) {
    setT((cur) => (cur ? { ...cur, [k]: v } : cur));
  }

  async function save() {
    if (!t) return;
    setBusy(true); setNote(null); setErr(null);
    try {
      const payload: Record<string, unknown> = {
        ai_provider: t.ai_provider ?? "",
        ai_model: t.ai_model ?? "",
        ai_endpoint: t.ai_endpoint ?? "",
        ai_deployment: t.ai_deployment ?? "",
        external_ai_allowed: t.external_ai_allowed,
        pii_minimization: t.pii_minimization,
      };
      if (key) payload.ai_api_key = key;
      const updated = await api.updateTenantAi(payload);
      setT(updated); setKey("");
      setNote("Saved. New remediation and tutor sessions will use these settings.");
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  if (err && !t) return <div className="card error">{err}</div>;
  if (!t) return <p className="muted">Loading…</p>;
  const external = t.ai_provider === "anthropic" || t.ai_provider === "openai";

  return (
    <div className="grid" style={{ gap: 16, maxWidth: 720 }}>
      <div className="card">
        <h3>AI model — {t.name}</h3>
        <p className="muted" style={{ marginTop: 0, fontSize: 13 }}>
          Run AI through your own provider and key. Inference then happens entirely under your
          institution's own contract — student content stays within your boundary. Leave as
          “Server default” to use whatever the server is configured with (`LLM_PROVIDER`; the safe
          local mock if unset).
        </p>
        <div className="field">
          <label>Provider</label>
          <select value={t.ai_provider ?? ""} onChange={(e) => set("ai_provider", e.target.value)}>
            {PROVIDERS.map((p) => <option key={p.v} value={p.v}>{p.label}</option>)}
          </select>
        </div>
        {t.ai_provider && t.ai_provider !== "mock" && (
          <>
            <div className="field">
              <label>Model {t.ai_provider === "azure_openai" ? "/ deployment name" : ""}</label>
              <input value={t.ai_model ?? ""} onChange={(e) => set("ai_model", e.target.value)}
                placeholder="e.g. gpt-4o or claude-3-5-sonnet-latest" />
            </div>
            {t.ai_provider === "azure_openai" && (
              <>
                <div className="field"><label>Azure endpoint</label>
                  <input value={t.ai_endpoint ?? ""} onChange={(e) => set("ai_endpoint", e.target.value)}
                    placeholder="https://your-resource.openai.azure.com" /></div>
                <div className="field"><label>Deployment</label>
                  <input value={t.ai_deployment ?? ""} onChange={(e) => set("ai_deployment", e.target.value)} /></div>
              </>
            )}
            <div className="field">
              <label>API key {t.ai_key_set && <span className="pill mastered">set</span>}</label>
              <input value={key} onChange={(e) => setKey(e.target.value)} type="password"
                placeholder={t.ai_key_set ? "•••••••• (leave blank to keep)" : "Paste your API key"} />
              <p className="mini muted" style={{ marginTop: 6, fontSize: 12 }}>
                Stored encrypted at rest. We never display it back.
              </p>
            </div>
          </>
        )}
      </div>

      <div className="card">
        <h3>Privacy controls</h3>
        <label className="switch" style={{ marginBottom: 12 }}>
          <input type="checkbox" checked={t.pii_minimization}
            onChange={(e) => set("pii_minimization", e.target.checked)} />
          <span className="slider" /><span className="switch-label">
            {t.pii_minimization ? "PII minimized" : "PII minimization off"}</span>
        </label>
        <p className="muted" style={{ marginTop: 0, fontSize: 13 }}>
          Redact identifiers (emails, IDs, names) from anything sent to the model. Recommended on.
        </p>
        <label className="switch" style={{ margin: "8px 0 12px" }}>
          <input type="checkbox" checked={t.external_ai_allowed}
            onChange={(e) => set("external_ai_allowed", e.target.checked)} />
          <span className="slider" /><span className="switch-label">
            {t.external_ai_allowed ? "External AI allowed" : "External AI blocked"}</span>
        </label>
        <p className="muted" style={{ marginTop: 0, fontSize: 13 }}>
          When blocked, live student content is never sent to an external commercial API — the
          engine uses your self-hosted model or a safe local fallback instead.
          {external && !t.external_ai_allowed &&
            <strong style={{ color: "var(--at-risk)" }}> Your selected provider is external and is
            currently blocked; requests will fall back locally until you allow it.</strong>}
        </p>
      </div>

      <div className="row">
        <button className="btn" onClick={save} disabled={busy}>
          {busy ? "Saving…" : "Save settings"}
        </button>
        {note && <span style={{ color: "var(--mastered)", fontSize: 14 }}>{note}</span>}
        {err && <span className="error">{err}</span>}
      </div>
    </div>
  );
}
