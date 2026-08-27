import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { api } from "../api/client";
import type { LtiToolConfig } from "../types";
import LanguageSwitcher from "../components/LanguageSwitcher";

const ink = "#0b1020";
const accent = "#4f46e5";

// Which LMSes support one-click Dynamic Registration (the rest need manual setup).
const LMS_KEYS = ["canvas", "moodle", "brightspace", "blackboard"] as const;
type LmsKey = (typeof LMS_KEYS)[number];
const ONE_CLICK: Record<LmsKey, boolean> = {
  canvas: true, moodle: true, brightspace: false, blackboard: false,
};

function CopyRow({ label, value }: { label: string; value: string }) {
  const { t } = useTranslation();
  const [done, setDone] = useState(false);
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 0",
      borderTop: "1px solid #eceef1", flexWrap: "wrap" }}>
      <div style={{ minWidth: 180, fontSize: 13, color: "#5f6470", fontWeight: 600 }}>{label}</div>
      <code style={{ flex: 1, minWidth: 200, fontSize: 13, background: "#f6f7f9", padding: "6px 10px",
        borderRadius: 8, overflowX: "auto", whiteSpace: "nowrap", direction: "ltr" }}>{value}</code>
      <button onClick={() => { navigator.clipboard?.writeText(value); setDone(true); setTimeout(() => setDone(false), 1400); }}
        style={{ border: "1px solid #d7dae0", background: "#fff", borderRadius: 8, padding: "6px 12px",
          cursor: "pointer", fontSize: 13 }}>
        {done ? t("connect.copied", { defaultValue: "Copied ✓" }) : t("connect.copy", { defaultValue: "Copy" })}</button>
    </div>
  );
}

export default function LmsSetupWizard() {
  const { t } = useTranslation();
  const [cfg, setCfg] = useState<LtiToolConfig | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [lms, setLms] = useState<LmsKey>("canvas");
  useEffect(() => { api.ltiConfig().then(setCfg).catch((e) => setErr((e as Error).message)); }, []);

  const steps = t(`connect.lms.${lms}.steps`, { returnObjects: true }) as unknown;
  const stepList = Array.isArray(steps) ? (steps as string[]) : [];

  return (
    <div style={{ minHeight: "100vh", background: "#f6f7f9" }}>
      <header style={{ background: ink, color: "#fff", padding: "16px 0" }}>
        <div style={{ maxWidth: 820, margin: "0 auto", padding: "0 16px", display: "flex",
          alignItems: "center", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
          <div>
            <div style={{ fontWeight: 800, fontSize: 19 }}>
              {t("connect.headerTitle", { defaultValue: "LMS Bridge · Connect your LMS" })}</div>
            <div style={{ opacity: 0.7, fontSize: 13, marginTop: 2 }}>
              {t("connect.headerSubtitle", { defaultValue: "Everything an admin needs to register the tool — copy a URL, follow the steps. No docs required." })}
            </div>
          </div>
          <LanguageSwitcher dark />
        </div>
      </header>
      <div style={{ maxWidth: 820, margin: "0 auto", padding: "24px 16px 56px" }}>
        {err && <div style={{ background: "#fdecea", color: "#b91c1c", padding: 14, borderRadius: 10 }}>
          {t("connect.loadError", { defaultValue: "Could not load the tool's URLs ({{err}}). Make sure the backend is reachable.", err })}</div>}
        {!cfg ? <p style={{ color: "#5f6470" }}>{t("connect.loading", { defaultValue: "Loading the tool's URLs…" })}</p> : (
          <>
            <div style={{ background: "#eef2ff", border: "1px solid #c7d0fb", borderRadius: 12,
              padding: "14px 16px", marginBottom: 18 }}>
              <div style={{ fontWeight: 600, color: accent, marginBottom: 4 }}>
                {t("connect.oneClickTitle", { defaultValue: "One-click for Canvas & Moodle" })}</div>
              <div style={{ fontSize: 14, color: "#33373f" }}>
                {t("connect.oneClickDesc", { defaultValue: "Paste this single Dynamic Registration URL and the LMS configures everything automatically:" })}</div>
              <CopyRow label={t("connect.dynRegLabel", { defaultValue: "Dynamic Registration URL" })} value={cfg.dynamic_registration_url} />
            </div>

            <div style={{ background: "#fff", border: "1px solid #e7e9ee", borderRadius: 12, padding: "16px 18px", marginBottom: 18 }}>
              <h3 style={{ marginTop: 0, fontSize: 16 }}>{t("connect.urlsTitle", { defaultValue: "All the URLs your LMS may ask for" })}</h3>
              <CopyRow label={t("connect.oidcLabel", { defaultValue: "OIDC login / initiation" })} value={cfg.oidc_initiation_url} />
              <CopyRow label={t("connect.targetLabel", { defaultValue: "Target Link / Launch URI" })} value={cfg.target_link_uri} />
              <CopyRow label={t("connect.redirectLabel", { defaultValue: "Redirect URI" })} value={cfg.redirect_uris[0] || cfg.target_link_uri} />
              <CopyRow label={t("connect.jwksLabel", { defaultValue: "Public keyset (JWKS)" })} value={cfg.public_jwks_url} />
              <CopyRow label={t("connect.deepLinkLabel", { defaultValue: "Deep Linking URL" })} value={cfg.deep_linking_url} />
              <div style={{ fontSize: 12.5, color: "#5f6470", marginTop: 10 }}>
                {cfg.lms_connected
                  ? t("connect.connectedYes", { defaultValue: "✓ At least one LMS is already connected." })
                  : t("connect.connectedNo", { defaultValue: "No LMS connected yet." })}
                {" "}{t("connect.scopes", { defaultValue: "Scopes requested: AGS (grades), NRPS (roster)." })}
              </div>
            </div>

            <div style={{ background: "#fff", border: "1px solid #e7e9ee", borderRadius: 12, padding: "16px 18px" }}>
              <h3 style={{ marginTop: 0, fontSize: 16 }}>{t("connect.stepsTitle", { defaultValue: "Step-by-step for your LMS" })}</h3>
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 12 }}>
                {LMS_KEYS.map((k) => (
                  <button key={k} onClick={() => setLms(k)}
                    style={{ border: "1px solid #d7dae0", borderRadius: 999, padding: "6px 14px", cursor: "pointer",
                      fontSize: 13.5, background: lms === k ? ink : "#fff", color: lms === k ? "#fff" : ink }}>
                    {t(`connect.lms.${k}.name`)}</button>
                ))}
              </div>
              <div style={{ fontSize: 13, color: ONE_CLICK[lms] ? "#15803d" : "#854f0b", marginBottom: 8 }}>
                {ONE_CLICK[lms]
                  ? t("connect.oneClickYes", { defaultValue: "✓ Supports one-click Dynamic Registration." })
                  : t("connect.oneClickNo", { defaultValue: "Manual registration (no one-click for this LMS)." })}
              </div>
              <ol style={{ margin: 0, paddingInlineStart: 20, fontSize: 14, lineHeight: 1.7 }}>
                {stepList.map((s, i) => <li key={i}>{s}</li>)}
              </ol>
              <p style={{ fontSize: 13, color: "#5f6470", marginTop: 12 }}>
                {t("connect.runbookPre", { defaultValue: "Need the full detail? See the complete per-LMS runbook in " })}
                <a href="https://github.com/hjmacemail/lmsbridge/blob/main/docs/INSTALL_LTI.md"
                  target="_blank" rel="noreferrer" style={{ color: accent }}>docs/INSTALL_LTI.md</a>
                {t("connect.runbookPost", { defaultValue: "." })}
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
