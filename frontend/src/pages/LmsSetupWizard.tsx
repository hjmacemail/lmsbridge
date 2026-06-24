import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { LtiToolConfig } from "../types";

const ink = "#0b1020";
const accent = "#4f46e5";

function CopyRow({ label, value }: { label: string; value: string }) {
  const [done, setDone] = useState(false);
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 0",
      borderTop: "1px solid #eceef1", flexWrap: "wrap" }}>
      <div style={{ minWidth: 180, fontSize: 13, color: "#5f6470", fontWeight: 600 }}>{label}</div>
      <code style={{ flex: 1, minWidth: 200, fontSize: 13, background: "#f6f7f9", padding: "6px 10px",
        borderRadius: 8, overflowX: "auto", whiteSpace: "nowrap" }}>{value}</code>
      <button onClick={() => { navigator.clipboard?.writeText(value); setDone(true); setTimeout(() => setDone(false), 1400); }}
        style={{ border: "1px solid #d7dae0", background: "#fff", borderRadius: 8, padding: "6px 12px",
          cursor: "pointer", fontSize: 13 }}>{done ? "Copied ✓" : "Copy"}</button>
    </div>
  );
}

const STEPS: Record<string, { name: string; oneClick: boolean; steps: string[] }> = {
  canvas: { name: "Canvas", oneClick: true, steps: [
    "Admin → Developer Keys → + Developer Key → + LTI Registration.",
    "Paste the Dynamic Registration URL → Continue → confirm → Enable & Close.",
    "Set the key's State to ON and copy the Client ID.",
    "Install it: Admin → Settings → Apps → +App → By Client ID (account-wide), or hand the Client ID to instructors to add per course.",
  ] },
  moodle: { name: "Moodle", oneClick: true, steps: [
    "Site administration → Plugins → Activity modules → External tool → Manage tools.",
    "Paste the Dynamic Registration URL in Tool URL → Add LTI Advantage.",
    "Review the pending tool, then Activate it and set 'Show in activity chooser'.",
    "Instructors add it per course as an activity.",
  ] },
  brightspace: { name: "Brightspace (D2L)", oneClick: false, steps: [
    "Admin → Manage Extensibility → LTI Advantage → Register Tool → Dynamic → paste the Dynamic Registration URL → Register, then enable it.",
    "Admin → External Learning Tools → New Deployment → select your org units → Create Deployment.",
    "On the deployment → View Links → New Link → Target Link / Launch URL → Save.",
    "Instructors add the link via Content → Add Existing → External Learning Tools.",
  ] },
  blackboard: { name: "Blackboard (Anthology)", oneClick: false, steps: [
    "Register once in the Anthology Developer Portal using the Login, Redirect, and JWKS URLs below → get a Client ID.",
    "Each institution's Blackboard admin: Admin → Integrations → LTI Tool Providers → Register LTI 1.3/Advantage Tool → paste the Client ID.",
    "Set Tool Status = Approved; enable grade (AGS) and membership (NRPS) services.",
    "Instructors add it via the Content Market (Ultra) or Build Content (Original).",
  ] },
};

export default function LmsSetupWizard() {
  const [cfg, setCfg] = useState<LtiToolConfig | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [lms, setLms] = useState<keyof typeof STEPS>("canvas");
  useEffect(() => { api.ltiConfig().then(setCfg).catch((e) => setErr((e as Error).message)); }, []);

  return (
    <div style={{ minHeight: "100vh", background: "#f6f7f9" }}>
      <header style={{ background: ink, color: "#fff", padding: "16px 0" }}>
        <div style={{ maxWidth: 820, margin: "0 auto", padding: "0 16px" }}>
          <div style={{ fontWeight: 800, fontSize: 19 }}>LMS Bridge · Connect your LMS</div>
          <div style={{ opacity: 0.7, fontSize: 13, marginTop: 2 }}>
            Everything an admin needs to register the tool — copy a URL, follow the steps. No docs required.
          </div>
        </div>
      </header>
      <div style={{ maxWidth: 820, margin: "0 auto", padding: "24px 16px 56px" }}>
        {err && <div style={{ background: "#fdecea", color: "#b91c1c", padding: 14, borderRadius: 10 }}>
          Could not load the tool's URLs ({err}). Make sure the backend is reachable.</div>}
        {!cfg ? <p style={{ color: "#5f6470" }}>Loading the tool's URLs…</p> : (
          <>
            <div style={{ background: "#eef2ff", border: "1px solid #c7d0fb", borderRadius: 12,
              padding: "14px 16px", marginBottom: 18 }}>
              <div style={{ fontWeight: 600, color: accent, marginBottom: 4 }}>
                One-click for Canvas &amp; Moodle</div>
              <div style={{ fontSize: 14, color: "#33373f" }}>Paste this single Dynamic Registration URL and
                the LMS configures everything automatically:</div>
              <CopyRow label="Dynamic Registration URL" value={cfg.dynamic_registration_url} />
            </div>

            <div style={{ background: "#fff", border: "1px solid #e7e9ee", borderRadius: 12, padding: "16px 18px", marginBottom: 18 }}>
              <h3 style={{ marginTop: 0, fontSize: 16 }}>All the URLs your LMS may ask for</h3>
              <CopyRow label="OIDC login / initiation" value={cfg.oidc_initiation_url} />
              <CopyRow label="Target Link / Launch URI" value={cfg.target_link_uri} />
              <CopyRow label="Redirect URI" value={cfg.redirect_uris[0] || cfg.target_link_uri} />
              <CopyRow label="Public keyset (JWKS)" value={cfg.public_jwks_url} />
              <CopyRow label="Deep Linking URL" value={cfg.deep_linking_url} />
              <div style={{ fontSize: 12.5, color: "#5f6470", marginTop: 10 }}>
                {cfg.lms_connected ? "✓ At least one LMS is already connected." : "No LMS connected yet."}
                {" "}Scopes requested: AGS (grades), NRPS (roster).
              </div>
            </div>

            <div style={{ background: "#fff", border: "1px solid #e7e9ee", borderRadius: 12, padding: "16px 18px" }}>
              <h3 style={{ marginTop: 0, fontSize: 16 }}>Step-by-step for your LMS</h3>
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 12 }}>
                {Object.keys(STEPS).map((k) => (
                  <button key={k} onClick={() => setLms(k as keyof typeof STEPS)}
                    style={{ border: "1px solid #d7dae0", borderRadius: 999, padding: "6px 14px", cursor: "pointer",
                      fontSize: 13.5, background: lms === k ? ink : "#fff", color: lms === k ? "#fff" : ink }}>
                    {STEPS[k].name}</button>
                ))}
              </div>
              <div style={{ fontSize: 13, color: STEPS[lms].oneClick ? "#15803d" : "#854f0b", marginBottom: 8 }}>
                {STEPS[lms].oneClick ? "✓ Supports one-click Dynamic Registration." : "Manual registration (no one-click for this LMS)."}
              </div>
              <ol style={{ margin: 0, paddingLeft: 20, fontSize: 14, lineHeight: 1.7 }}>
                {STEPS[lms].steps.map((s, i) => <li key={i}>{s}</li>)}
              </ol>
              <p style={{ fontSize: 13, color: "#5f6470", marginTop: 12 }}>
                Need the full detail? See the complete per-LMS runbook in
                {" "}<a href="https://github.com/hjmacemail/lmsbridge/blob/main/docs/INSTALL_LTI.md"
                  target="_blank" rel="noreferrer" style={{ color: accent }}>docs/INSTALL_LTI.md</a>.
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
