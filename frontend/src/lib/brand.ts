// Configurable Sage branding. A deployment, subdomain, or even a single shareable link can show a
// partner's product name / logo / tagline without forking the product. AGPL attribution (the
// "by LMS Bridge" source link) always stays.
//
// Resolution order (later wins):
//   1. built-in defaults
//   2. per-instance env config: window.__LMSBRIDGE_BRAND__ (set from BRAND_* env vars at deploy)
//   3. a ?brand=<preset> query param (a "special link"), remembered for the session
export interface Brand {
  name: string;
  attribution: string;   // shown after the name, links to the LMS Bridge home (AGPL attribution)
  accent?: string;       // optional header colour override
  logoUrl?: string;      // optional logo image (replaces the default mark)
  tagline?: string;      // welcome-screen subtitle
}

const DEFAULT: Brand = {
  name: "Sage",
  attribution: "by LMS Bridge",
  tagline: "Your own mini class platform — create a course, add quizzes, and let LMS Bridge guide "
    + "students through what they miss. No LMS needed.",
};

// Demo presets you can activate with a link, e.g. .../sage?brand=twas
const PRESETS: Record<string, Partial<Brand>> = {
  twas: {
    name: "TWAS Learning",
    tagline: "Free, AI-guided STEM learning for the TWAS community — create a course, add quizzes, "
      + "and guide students through exactly what they miss. No LMS, no IT setup.",
  },
};

const KEY = "sage_brand";

export function resolveBrand(): Brand {
  let preset: string | null = null;
  try {
    const q = new URLSearchParams(window.location.search).get("brand");
    if (q) { sessionStorage.setItem(KEY, q); preset = q; }
    else preset = sessionStorage.getItem(KEY);
  } catch { /* no window/search */ }
  const env = (typeof window !== "undefined"
    ? (window as unknown as { __LMSBRIDGE_BRAND__?: Partial<Brand> }).__LMSBRIDGE_BRAND__
    : undefined) || {};
  const fromPreset = (preset && PRESETS[preset]) || {};
  return { ...DEFAULT, ...env, ...fromPreset };
}
