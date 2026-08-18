// Localized display names for the fixed demo vocabulary (course titles + concept/topic names).
// These are seeded data, not UI labels, so they live here rather than in the locale files.
// localizeTerm() returns the original text for English / unknown terms, so it's always safe.

type Lang = "es" | "fr" | "ar";
const TERMS: Record<string, Record<Lang, string>> = {
  // ---- Concept / topic names ----
  "Binary Representation": { es: "Representación binaria", fr: "Représentation binaire", ar: "التمثيل الثنائي" },
  "Binary Arithmetic": { es: "Aritmética binaria", fr: "Arithmétique binaire", ar: "الحساب الثنائي" },
  "Boolean Logic": { es: "Lógica booleana", fr: "Logique booléenne", ar: "جبر المنطق" },
  "Machine-Level Computation": { es: "Cómputo a nivel de máquina", fr: "Calcul au niveau machine", ar: "الحوسبة على مستوى الآلة" },
  "Encapsulation": { es: "Encapsulamiento", fr: "Encapsulation", ar: "التغليف" },
  "Inheritance": { es: "Herencia", fr: "Héritage", ar: "الوراثة" },
  "Polymorphism": { es: "Polimorfismo", fr: "Polymorphisme", ar: "تعدّد الأشكال" },
  "Data Structures": { es: "Estructuras de datos", fr: "Structures de données", ar: "هياكل البيانات" },
  "Probability Basics": { es: "Fundamentos de probabilidad", fr: "Bases des probabilités", ar: "أساسيات الاحتمالات" },
  "Conditional Probability": { es: "Probabilidad condicional", fr: "Probabilité conditionnelle", ar: "الاحتمال الشرطي" },
  "Distributions": { es: "Distribuciones", fr: "Distributions", ar: "التوزيعات" },
  "Hypothesis Testing": { es: "Prueba de hipótesis", fr: "Test d'hypothèse", ar: "اختبار الفرضيات" },
  // ---- Course titles ----
  "Computer Architecture & Digital Logic": { es: "Arquitectura de computadoras y lógica digital", fr: "Architecture des ordinateurs et logique numérique", ar: "معمارية الحاسوب والمنطق الرقمي" },
  "Object-Oriented Programming": { es: "Programación orientada a objetos", fr: "Programmation orientée objet", ar: "البرمجة الكائنية التوجّه" },
  "Statistical Reasoning for Data Science": { es: "Razonamiento estadístico para ciencia de datos", fr: "Raisonnement statistique pour la science des données", ar: "الاستدلال الإحصائي لعلوم البيانات" },
  "Intro to Computer Science": { es: "Introducción a la informática", fr: "Introduction à l'informatique", ar: "مقدمة في علوم الحاسوب" },
};

// Seeded demo student names, transliterated into Arabic (Latin scripts keep the original,
// so we only map for Arabic). Keyed by full English name.
const NAMES_AR: Record<string, string> = {
  "Ava Chen": "آفا تشين",
  "Marcus Lopez": "ماركوس لوبيز",
  "Priya Patel": "بريا باتيل",
  "Sam Lee": "سام لي",
  "Jordan Diaz": "جوردن دياز",
  "Diego Santos": "دييغو سانتوس",
  "Lena Müller": "لينا مولر",
  "Omar Haddad": "عمر حدّاد",
  "Grace Kim": "غريس كيم",
  "Noah Williams": "نواه ويليامز",
  // Demo instructor
  "Dr. Alex Rivera": "د. أليكس ريفيرا",
  "Alex Rivera": "أليكس ريفيرا",
};

function base(lang: string): Lang | null {
  const l = (lang || "").slice(0, 2).toLowerCase();
  return l === "es" || l === "fr" || l === "ar" ? l : null;
}

/** Localize a demo person's name. Only Arabic is transliterated; other locales keep the
 *  original spelling. Unknown names pass through unchanged. */
export function localizeName(name: string | null | undefined, lang: string): string {
  if (!name) return name || "";
  if ((lang || "").slice(0, 2).toLowerCase() !== "ar") return name;
  return NAMES_AR[name.trim()] || name;
}

/** Localize a single seeded term (course title or concept name). Safe pass-through otherwise. */
export function localizeTerm(text: string | null | undefined, lang: string): string {
  if (!text) return text || "";
  const l = base(lang);
  if (!l) return text;
  return TERMS[text.trim()]?.[l] || text;
}

/** Localize a "CODE — Title" course label by translating only the Title part (code stays). */
export function localizeCourseLabel(label: string | null | undefined, lang: string): string {
  if (!label) return label || "";
  const parts = label.split(" — ");
  if (parts.length === 2) return `${parts[0]} — ${localizeTerm(parts[1], lang)}`;
  return localizeTerm(label, lang);
}
