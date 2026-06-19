import { useTranslation } from "react-i18next";
import { LANGUAGES } from "../i18n";

export default function LanguageSwitcher({ dark = false }: { dark?: boolean }) {
  const { i18n, t } = useTranslation();
  const cur = (i18n.language || "en").split("-")[0];
  return (
    <select
      aria-label={t("common.language")}
      value={LANGUAGES.some((l) => l.code === cur) ? cur : "en"}
      onChange={(e) => i18n.changeLanguage(e.target.value)}
      style={{
        fontSize: 13, padding: "4px 8px", borderRadius: 7, cursor: "pointer",
        border: dark ? "1px solid rgba(255,255,255,.4)" : "1px solid var(--line, #d9dde1)",
        background: dark ? "transparent" : "#fff",
        color: dark ? "#fff" : "inherit",
      }}
    >
      {LANGUAGES.map((l) => (
        <option key={l.code} value={l.code} style={{ color: "#11161b" }}>{l.label}</option>
      ))}
    </select>
  );
}
