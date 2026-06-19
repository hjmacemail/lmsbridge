import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import LanguageDetector from "i18next-browser-languagedetector";
import en from "./locales/en.json";
import ar from "./locales/ar.json";
import fr from "./locales/fr.json";
import es from "./locales/es.json";

export const LANGUAGES = [
  { code: "en", label: "English" },
  { code: "es", label: "Español" },
  { code: "fr", label: "Français" },
  { code: "ar", label: "العربية" },
];
const RTL = new Set(["ar", "he", "fa", "ur"]);
export const isRtl = (lng?: string) => RTL.has((lng || i18n.language || "en").split("-")[0]);

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      ar: { translation: ar },
      fr: { translation: fr },
      es: { translation: es },
    },
    fallbackLng: "en",
    supportedLngs: ["en", "es", "fr", "ar"],
    interpolation: { escapeValue: false },
    react: { useSuspense: false },
    detection: {
      order: ["querystring", "localStorage", "navigator"],
      lookupQuerystring: "lang",
      caches: ["localStorage"],
    },
  });

// Keep document direction + lang in sync (right-to-left for Arabic, etc.).
function applyDir(lng: string) {
  if (typeof document === "undefined") return;
  document.documentElement.dir = isRtl(lng) ? "rtl" : "ltr";
  document.documentElement.lang = (lng || "en").split("-")[0];
}
applyDir(i18n.language);
i18n.on("languageChanged", applyDir);

export default i18n;
