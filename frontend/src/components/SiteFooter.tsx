declare global {
  interface Window {
    __LMSBRIDGE_SOURCE__?: string;
    __LMSBRIDGE_BRANDING__?: boolean;
  }
}

const SOURCE =
  (typeof window !== "undefined" && window.__LMSBRIDGE_SOURCE__) ||
  "https://github.com/hjmacemail/lmsbridge";
// Branding badge is opt-out (SHOW_BRANDING=false); the Source link always stays (AGPL §13).
const SHOW_BRANDING =
  typeof window === "undefined" || window.__LMSBRIDGE_BRANDING__ !== false;

export default function SiteFooter() {
  return (
    <footer style={{ textAlign: "center", padding: "14px 12px", fontSize: 12,
      color: "var(--muted, #8a929b)", borderTop: "1px solid var(--line, #eceef1)" }}>
      {SHOW_BRANDING && (
        <>
          Powered by <strong style={{ color: "var(--muted, #8a929b)" }}>LMS Bridge</strong>
          {" · "}
        </>
      )}
      <a href={SOURCE} target="_blank" rel="noreferrer"
        style={{ color: "var(--muted, #8a929b)", textDecoration: "underline" }}>Source</a>
      {" · free & open-source (AGPL-3.0)"}
    </footer>
  );
}
