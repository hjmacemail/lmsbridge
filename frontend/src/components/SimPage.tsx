import type { CSSProperties } from "react";
import { useTranslation } from "react-i18next";
import type { LmsId, LmsPage } from "./LmsFrame";
import { localizeName, localizeCourseLabel } from "../i18n/terms";

// Plausible, static "LMS content" pages for the demo, styled to closely resemble the real
// Canvas LMS UI. The only real, interactive page is the tool (rendered by DemoPage). All
// styling here is inline so it does not inherit the product's card/pill/btn look.
//
// The body content is fully localized (en/ar/es/fr) so the simulated pages read in the same
// language the demo is set to. Fixed data (emails, SIS IDs, section codes, scores) stays as-is;
// student/instructor names route through localizeName so Arabic shows transliterated names.

// ---- Canvas design tokens -------------------------------------------------
const BLUE = "#0374B5";
const TEXT = "#2D3B45";
const MUTED = "#6B7780";
const BORDER = "#C7CDD1";
const DIVIDER = "#E8EAEC";
const ROW_HOVER = "#F5F5F5";
const GREEN = "#0B874B";

const primaryBtn: CSSProperties = {
  background: BLUE, color: "#fff", border: "none", borderRadius: 4, padding: "8px 14px",
  fontSize: 14, fontWeight: 600, cursor: "pointer", display: "inline-flex", alignItems: "center", gap: 6,
};
const secondaryBtn: CSSProperties = {
  background: "#fff", color: TEXT, border: `1px solid ${BORDER}`, borderRadius: 4, padding: "8px 12px",
  fontSize: 14, cursor: "pointer", display: "inline-flex", alignItems: "center", gap: 6,
};
const inputStyle: CSSProperties = {
  border: `1px solid ${BORDER}`, borderRadius: 4, padding: "8px 12px", fontSize: 14, color: TEXT, background: "#fff",
};
const linkStyle: CSSProperties = { color: BLUE, textDecoration: "none" };
const pageWrap: CSSProperties = {
  background: "#fff", color: TEXT, fontSize: 14, lineHeight: 1.5, padding: "18px 22px 40px",
  maxWidth: 1180, margin: "0 auto",
};
const h1Style: CSSProperties = { fontSize: 24, fontWeight: 700, color: TEXT, margin: "0 0 16px" };

// ---- Localized strings ----------------------------------------------------
type Lang = "en" | "ar" | "es" | "fr";
function pickLang(l: string): Lang {
  const b = (l || "").slice(0, 2).toLowerCase();
  return b === "ar" || b === "es" || b === "fr" ? (b as Lang) : "en";
}

interface AnnItem { title: string; body: string; posted: string }
interface QuizItem { title: string; due: string; pts: number; qn: number }
interface ModItem { title: string; items: string[] }
interface SimStrings {
  noteA: string; noteB: string;
  // Home
  welcome: string; instructorAdded: string; instructorBody: string; openBridge: string;
  latest: string; midtermTitle: string; midtermBody: string;
  // People
  people: string; everyone: string; groups: string; groupSet: string; searchPeople: string;
  allRoles: string; teacher: string; student: string; peopleBtn: string;
  thName: string; thLogin: string; thSis: string; thSection: string; thRole: string;
  thLast: string; thTotal: string;
  // Announcements
  announcements: string; all: string; unread: string; searchDots: string; addAnnouncement: string;
  markAllRead: string; externalFeeds: string; allSections: string; reply: string; postedOn: string;
  annItems: AnnItem[];
  // Quizzes
  quizzes: string; searchQuiz: string; addQuiz: string; assignmentQuizzes: string;
  closed: string; ptsWord: string; questionsWord: string; quizItems: QuizItem[];
  // Gradebook
  gradebook: string; studentNames: string; searchStudents: string; assignmentNames: string;
  searchAssignments: string; applyFilters: string; importBtn: string; exportBtn: string;
  studentName: string; outOf: string; gradeCols: string[];
  // Discussions
  discussions: string; repliesWord: string; discTopics: string[];
  // Modules
  modules: string; modItems: ModItem[];
}

const DICT: Record<Lang, SimStrings> = {
  en: {
    noteA: "Simulated Canvas page — example content. The real, interactive piece is ", noteB: ".",
    welcome: "Welcome to the course. Use the menu to reach assignments, grades, and your learning support.",
    instructorAdded: "Your instructor added LMS Bridge",
    instructorBody: "Personalized, just-in-time tutoring based on your assessment results. Open it to see your recommended practice.",
    openBridge: "Open LMS Bridge", latest: "Latest announcements",
    midtermTitle: "Midterm next week",
    midtermBody: "Covers number systems through Boolean logic. Review the practice set.",
    people: "People", everyone: "Everyone", groups: "Groups", groupSet: "+ Group Set",
    searchPeople: "Search people", allRoles: "All Roles", teacher: "Teacher", student: "Student", peopleBtn: "+ People",
    thName: "Name", thLogin: "Login ID", thSis: "SIS ID", thSection: "Section", thRole: "Role",
    thLast: "Last Activity", thTotal: "Total Activity",
    announcements: "Announcements", all: "All", unread: "Unread", searchDots: "Search…",
    addAnnouncement: "+ Add Announcement", markAllRead: "✉ Mark All as Read", externalFeeds: "External Feeds",
    allSections: "All Sections", reply: "↩ Reply", postedOn: "Posted on:",
    annItems: [
      { title: "Final Exam Grades", body: "Dear Class, Final Exam grades are now available through coursework (You should be able to see …", posted: "May 4, 2025, 9:21 PM" },
      { title: "Final Review Session", body: "Dear students, I have changed this week's OH to Wednesday 5:00 – 6:00 PM on Zoom, to help y…", posted: "Apr 28, 2025, 7:21 PM" },
      { title: "Assignment 5 posted", body: "The last homework is up; it covers hypothesis testing. Due next Friday, 11:59 PM.", posted: "Apr 20, 2025, 3:10 PM" },
    ],
    quizzes: "Quizzes", searchQuiz: "Search for Quiz", addQuiz: "+ Quiz", assignmentQuizzes: "▾ Assignment Quizzes",
    closed: "Closed", ptsWord: "pts", questionsWord: "Questions",
    quizItems: [
      { title: "Midterm Exam (Remotely Proctored)", due: "Due Mar 6 at 7:50pm", pts: 20, qn: 40 },
      { title: "Final Exam (Remotely Proctored)", due: "Due May 1 at 8:00pm", pts: 20, qn: 40 },
      { title: "Quiz 1 — Binary arithmetic", due: "Due Feb 12 at 11:59pm", pts: 10, qn: 8 },
    ],
    gradebook: "Gradebook", studentNames: "Student Names", searchStudents: "Search Students",
    assignmentNames: "Assignment Names", searchAssignments: "Search Assignments", applyFilters: "⏷ Apply Filters",
    importBtn: "⇥ Import", exportBtn: "Export ▾", studentName: "Student Name", outOf: "Out of {{n}}",
    gradeCols: ["Assignment-1", "Assignment-2", "Assignment-3", "Assignment-4", "Assignment-5", "Roll Call Attendance", "Midterm Exam"],
    discussions: "Discussions", repliesWord: "replies",
    discTopics: ["Two's complement intuition?", "Why does carry propagate left?", "Study group for the midterm"],
    modules: "Modules",
    modItems: [
      { title: "Week 1 · Number systems", items: ["Reading: binary & hex", "A01 — Number representation"] },
      { title: "Week 2 · Binary arithmetic", items: ["Reading: two's complement", "Quiz 1"] },
      { title: "Week 3 · Boolean logic", items: ["Reading: truth tables", "A02 — Boolean logic"] },
    ],
  },
  ar: {
    noteA: "صفحة Canvas محاكاة — محتوى توضيحي. الجزء الحقيقي التفاعلي هو ", noteB: ".",
    welcome: "مرحبًا بك في المقرر. استخدم القائمة للوصول إلى الواجبات والدرجات ودعم التعلّم الخاص بك.",
    instructorAdded: "أضاف مُدرّسك LMS Bridge",
    instructorBody: "دروس خصوصية مخصّصة وفورية بناءً على نتائج تقييماتك. افتحه لرؤية التدريبات الموصى بها لك.",
    openBridge: "افتح LMS Bridge", latest: "أحدث الإعلانات",
    midtermTitle: "الامتحان النصفي الأسبوع القادم",
    midtermBody: "يغطّي أنظمة الأعداد حتى جبر المنطق. راجِع مجموعة التدريبات.",
    people: "الأشخاص", everyone: "الجميع", groups: "المجموعات", groupSet: "+ مجموعة",
    searchPeople: "بحث عن أشخاص", allRoles: "كل الأدوار", teacher: "مدرّس", student: "طالب", peopleBtn: "+ أشخاص",
    thName: "الاسم", thLogin: "معرّف الدخول", thSis: "معرّف النظام", thSection: "الشعبة", thRole: "الدور",
    thLast: "آخر نشاط", thTotal: "إجمالي النشاط",
    announcements: "الإعلانات", all: "الكل", unread: "غير المقروءة", searchDots: "بحث…",
    addAnnouncement: "+ إضافة إعلان", markAllRead: "✉ تحديد الكل كمقروء", externalFeeds: "الخلاصات الخارجية",
    allSections: "كل الشُّعَب", reply: "↩ رد", postedOn: "نُشِر في:",
    annItems: [
      { title: "درجات الامتحان النهائي", body: "أعزائي الطلاب، أصبحت درجات الامتحان النهائي متاحة الآن عبر صفحة المقرر (ينبغي أن تتمكنوا من رؤية …", posted: "4 مايو 2025، 9:21 م" },
      { title: "جلسة المراجعة النهائية", body: "أعزائي الطلاب، لقد غيّرت الساعات المكتبية لهذا الأسبوع إلى الأربعاء 5:00 – 6:00 مساءً عبر Zoom، لمساعدتـ…", posted: "28 أبريل 2025، 7:21 م" },
      { title: "تم نشر الواجب 5", body: "الواجب الأخير متاح الآن؛ ويغطّي اختبار الفرضيات. موعد التسليم الجمعة القادمة، 11:59 مساءً.", posted: "20 أبريل 2025، 3:10 م" },
    ],
    quizzes: "الاختبارات", searchQuiz: "بحث عن اختبار", addQuiz: "+ اختبار", assignmentQuizzes: "▾ اختبارات الواجبات",
    closed: "مغلق", ptsWord: "نقطة", questionsWord: "سؤالاً",
    quizItems: [
      { title: "امتحان منتصف الفصل (مراقَب عن بُعد)", due: "التسليم 6 مارس، 7:50 م", pts: 20, qn: 40 },
      { title: "الامتحان النهائي (مراقَب عن بُعد)", due: "التسليم 1 مايو، 8:00 م", pts: 20, qn: 40 },
      { title: "الاختبار 1 — الحساب الثنائي", due: "التسليم 12 فبراير، 11:59 م", pts: 10, qn: 8 },
    ],
    gradebook: "سجل الدرجات", studentNames: "أسماء الطلاب", searchStudents: "بحث عن طلاب",
    assignmentNames: "أسماء الواجبات", searchAssignments: "بحث عن واجبات", applyFilters: "⏷ تطبيق عوامل التصفية",
    importBtn: "⇥ استيراد", exportBtn: "تصدير ▾", studentName: "اسم الطالب", outOf: "من {{n}}",
    gradeCols: ["الواجب-1", "الواجب-2", "الواجب-3", "الواجب-4", "الواجب-5", "تسجيل الحضور", "امتحان منتصف الفصل"],
    discussions: "النقاشات", repliesWord: "ردود",
    discTopics: ["حدس المتمم الثنائي؟", "لماذا ينتشر الحمل نحو اليسار؟", "مجموعة دراسة للامتحان النصفي"],
    modules: "الوحدات",
    modItems: [
      { title: "الأسبوع 1 · أنظمة الأعداد", items: ["قراءة: الثنائي والسداسي عشري", "A01 — تمثيل الأعداد"] },
      { title: "الأسبوع 2 · الحساب الثنائي", items: ["قراءة: المتمم الثنائي", "الاختبار 1"] },
      { title: "الأسبوع 3 · جبر المنطق", items: ["قراءة: جداول الصدق", "A02 — جبر المنطق"] },
    ],
  },
  es: {
    noteA: "Página simulada de Canvas — contenido de ejemplo. La pieza real e interactiva es ", noteB: ".",
    welcome: "Bienvenido al curso. Usa el menú para acceder a las tareas, las calificaciones y tu apoyo de aprendizaje.",
    instructorAdded: "Tu instructor añadió LMS Bridge",
    instructorBody: "Tutoría personalizada y justo a tiempo según los resultados de tus evaluaciones. Ábrelo para ver tu práctica recomendada.",
    openBridge: "Abrir LMS Bridge", latest: "Últimos anuncios",
    midtermTitle: "Parcial la próxima semana",
    midtermBody: "Cubre los sistemas numéricos hasta la lógica booleana. Repasa el conjunto de práctica.",
    people: "Personas", everyone: "Todos", groups: "Grupos", groupSet: "+ Conjunto de grupos",
    searchPeople: "Buscar personas", allRoles: "Todos los roles", teacher: "Profesor", student: "Estudiante", peopleBtn: "+ Personas",
    thName: "Nombre", thLogin: "ID de acceso", thSis: "ID SIS", thSection: "Sección", thRole: "Rol",
    thLast: "Última actividad", thTotal: "Actividad total",
    announcements: "Anuncios", all: "Todos", unread: "No leídos", searchDots: "Buscar…",
    addAnnouncement: "+ Añadir anuncio", markAllRead: "✉ Marcar todo como leído", externalFeeds: "Fuentes externas",
    allSections: "Todas las secciones", reply: "↩ Responder", postedOn: "Publicado el:",
    annItems: [
      { title: "Calificaciones del examen final", body: "Estimada clase, las calificaciones del examen final ya están disponibles a través del curso (deberían poder ver …", posted: "4 may 2025, 9:21 p. m." },
      { title: "Sesión de repaso final", body: "Estimados estudiantes, cambié la tutoría de esta semana al miércoles de 5:00 a 6:00 p. m. por Zoom, para ayudar…", posted: "28 abr 2025, 7:21 p. m." },
      { title: "Tarea 5 publicada", body: "La última tarea ya está disponible; cubre la prueba de hipótesis. Vence el próximo viernes, 11:59 p. m.", posted: "20 abr 2025, 3:10 p. m." },
    ],
    quizzes: "Cuestionarios", searchQuiz: "Buscar cuestionario", addQuiz: "+ Cuestionario", assignmentQuizzes: "▾ Cuestionarios de tarea",
    closed: "Cerrado", ptsWord: "pts", questionsWord: "Preguntas",
    quizItems: [
      { title: "Examen parcial (supervisado a distancia)", due: "Vence el 6 mar a las 7:50 p. m.", pts: 20, qn: 40 },
      { title: "Examen final (supervisado a distancia)", due: "Vence el 1 may a las 8:00 p. m.", pts: 20, qn: 40 },
      { title: "Cuestionario 1 — Aritmética binaria", due: "Vence el 12 feb a las 11:59 p. m.", pts: 10, qn: 8 },
    ],
    gradebook: "Libro de calificaciones", studentNames: "Nombres de estudiantes", searchStudents: "Buscar estudiantes",
    assignmentNames: "Nombres de tareas", searchAssignments: "Buscar tareas", applyFilters: "⏷ Aplicar filtros",
    importBtn: "⇥ Importar", exportBtn: "Exportar ▾", studentName: "Nombre del estudiante", outOf: "De {{n}}",
    gradeCols: ["Tarea-1", "Tarea-2", "Tarea-3", "Tarea-4", "Tarea-5", "Registro de asistencia", "Examen parcial"],
    discussions: "Debates", repliesWord: "respuestas",
    discTopics: ["¿Intuición del complemento a dos?", "¿Por qué el acarreo se propaga a la izquierda?", "Grupo de estudio para el parcial"],
    modules: "Módulos",
    modItems: [
      { title: "Semana 1 · Sistemas numéricos", items: ["Lectura: binario y hexadecimal", "A01 — Representación de números"] },
      { title: "Semana 2 · Aritmética binaria", items: ["Lectura: complemento a dos", "Cuestionario 1"] },
      { title: "Semana 3 · Lógica booleana", items: ["Lectura: tablas de verdad", "A02 — Lógica booleana"] },
    ],
  },
  fr: {
    noteA: "Page Canvas simulée — contenu d'exemple. La partie réelle et interactive est ", noteB: ".",
    welcome: "Bienvenue dans le cours. Utilisez le menu pour accéder aux devoirs, aux notes et à votre soutien d'apprentissage.",
    instructorAdded: "Votre enseignant a ajouté LMS Bridge",
    instructorBody: "Tutorat personnalisé et au bon moment selon vos résultats d'évaluation. Ouvrez-le pour voir vos exercices recommandés.",
    openBridge: "Ouvrir LMS Bridge", latest: "Dernières annonces",
    midtermTitle: "Partiel la semaine prochaine",
    midtermBody: "Couvre les systèmes de numération jusqu'à la logique booléenne. Révisez la série d'exercices.",
    people: "Personnes", everyone: "Tout le monde", groups: "Groupes", groupSet: "+ Ensemble de groupes",
    searchPeople: "Rechercher des personnes", allRoles: "Tous les rôles", teacher: "Enseignant", student: "Étudiant", peopleBtn: "+ Personnes",
    thName: "Nom", thLogin: "Identifiant", thSis: "ID SIS", thSection: "Section", thRole: "Rôle",
    thLast: "Dernière activité", thTotal: "Activité totale",
    announcements: "Annonces", all: "Toutes", unread: "Non lues", searchDots: "Rechercher…",
    addAnnouncement: "+ Ajouter une annonce", markAllRead: "✉ Tout marquer comme lu", externalFeeds: "Flux externes",
    allSections: "Toutes les sections", reply: "↩ Répondre", postedOn: "Publié le :",
    annItems: [
      { title: "Notes de l'examen final", body: "Chère classe, les notes de l'examen final sont désormais disponibles via le cours (vous devriez pouvoir voir …", posted: "4 mai 2025, 21:21" },
      { title: "Séance de révision finale", body: "Chers étudiants, j'ai déplacé la permanence de cette semaine au mercredi de 17h00 à 18h00 sur Zoom, pour aider…", posted: "28 avr. 2025, 19:21" },
      { title: "Devoir 5 publié", body: "Le dernier devoir est en ligne ; il porte sur les tests d'hypothèses. À rendre vendredi prochain, 23h59.", posted: "20 avr. 2025, 15:10" },
    ],
    quizzes: "Quiz", searchQuiz: "Rechercher un quiz", addQuiz: "+ Quiz", assignmentQuizzes: "▾ Quiz de devoir",
    closed: "Fermé", ptsWord: "pts", questionsWord: "Questions",
    quizItems: [
      { title: "Examen partiel (surveillé à distance)", due: "À rendre le 6 mars à 19h50", pts: 20, qn: 40 },
      { title: "Examen final (surveillé à distance)", due: "À rendre le 1 mai à 20h00", pts: 20, qn: 40 },
      { title: "Quiz 1 — Arithmétique binaire", due: "À rendre le 12 févr. à 23h59", pts: 10, qn: 8 },
    ],
    gradebook: "Carnet de notes", studentNames: "Noms des étudiants", searchStudents: "Rechercher des étudiants",
    assignmentNames: "Noms des devoirs", searchAssignments: "Rechercher des devoirs", applyFilters: "⏷ Appliquer les filtres",
    importBtn: "⇥ Importer", exportBtn: "Exporter ▾", studentName: "Nom de l'étudiant", outOf: "Sur {{n}}",
    gradeCols: ["Devoir-1", "Devoir-2", "Devoir-3", "Devoir-4", "Devoir-5", "Feuille de présence", "Examen partiel"],
    discussions: "Discussions", repliesWord: "réponses",
    discTopics: ["Intuition du complément à deux ?", "Pourquoi la retenue se propage-t-elle vers la gauche ?", "Groupe d'étude pour le partiel"],
    modules: "Modules",
    modItems: [
      { title: "Semaine 1 · Systèmes de numération", items: ["Lecture : binaire et hexadécimal", "A01 — Représentation des nombres"] },
      { title: "Semaine 2 · Arithmétique binaire", items: ["Lecture : complément à deux", "Quiz 1"] },
      { title: "Semaine 3 · Logique booléenne", items: ["Lecture : tables de vérité", "A02 — Logique booléenne"] },
    ],
  },
};

// ---- Fixed (non-translated) data ------------------------------------------
const REPLY_COUNTS = [8, 5, 12];
const GRADE_OUT = [10, 10, 10, 10, 10, 100, 20];
const GRADE_ROWS: { student: string; scores: string[] }[] = [
  { student: "Sam Lee", scores: ["9", "8", "10", "7", "—", "96", "17"] },
  { student: "Ava Chen", scores: ["10", "9", "9", "10", "8", "100", "19"] },
  { student: "Jordan Diaz", scores: ["6", "—", "7", "5", "—", "72", "11"] },
  { student: "Priya Patel", scores: ["10", "10", "9", "9", "10", "98", "20"] },
];
const ROSTER: { name: string; login: string; sis: string; section: string; role: "teacher" | "student"; last: string; total: string }[] = [
  { name: "Dr. Alex Rivera", login: "a.rivera@uni.edu", sis: "1001", section: "CS 101", role: "teacher", last: "Apr 30, 2025", total: "58:12" },
  { name: "Sam Lee", login: "s.lee@uni.edu", sis: "2043", section: "CS 101", role: "student", last: "May 2, 2025", total: "24:07" },
  { name: "Ava Chen", login: "a.chen@uni.edu", sis: "2044", section: "CS 101", role: "student", last: "May 1, 2025", total: "31:44" },
  { name: "Jordan Diaz", login: "j.diaz@uni.edu", sis: "2045", section: "CS 101", role: "student", last: "Apr 27, 2025", total: "12:03" },
  { name: "Priya Patel", login: "p.patel@uni.edu", sis: "2046", section: "CS 101", role: "student", last: "May 3, 2025", total: "40:19" },
];

// ---- Small UI helpers ------------------------------------------------------
function Kebab() {
  return (
    <button type="button" aria-label="Options" style={{ border: "none", background: "transparent",
      color: MUTED, fontSize: 18, lineHeight: 1, cursor: "pointer", padding: "2px 6px" }}>⋮</button>
  );
}
function initials(name: string): string {
  const parts = name.replace(/^Dr\.\s*/i, "").replace(/^د\.\s*/, "").trim().split(/\s+/);
  const first = parts[0]?.[0] ?? "";
  const last = parts.length > 1 ? parts[parts.length - 1][0] : "";
  return (first + last).toUpperCase();
}
function Avatar({ name, size = 32, bg = BORDER, color = "#fff" }: {
  name: string; size?: number; bg?: string; color?: string;
}) {
  return (
    <span aria-hidden style={{ width: size, height: size, minWidth: size, borderRadius: "50%",
      background: bg, color, display: "inline-flex", alignItems: "center", justifyContent: "center",
      fontSize: Math.round(size * 0.38), fontWeight: 700 }}>{initials(name)}</span>
  );
}
function GreenCheck() {
  return (
    <span aria-hidden style={{ width: 20, height: 20, borderRadius: "50%", background: GREEN, color: "#fff",
      display: "inline-flex", alignItems: "center", justifyContent: "center", fontSize: 12, fontWeight: 700 }}>✓</span>
  );
}

// ---- Entry point -----------------------------------------------------------
export default function SimPage(
  { page, lms, toolHref }: { page: LmsPage; lms: LmsId; toolHref: string },
) {
  void lms; // Styled as Canvas regardless of `lms` (Canvas is the demo default).
  const { i18n } = useTranslation();
  const lang = pickLang(i18n.language);
  const s = DICT[lang];
  return (
    <div style={pageWrap}>
      <div style={{ fontSize: 12.5, color: MUTED, marginBottom: 14 }}>
        {s.noteA}<a href={toolHref} style={{ color: BLUE }}>LMS Bridge</a>{s.noteB}
      </div>
      {render(page, toolHref, s, lang)}
    </div>
  );
}

function render(page: LmsPage, toolHref: string, s: SimStrings, lang: Lang) {
  switch (page) {
    case "assignments": return <Quizzes s={s} />;
    case "grades": return <Gradebook s={s} lang={lang} />;
    case "people": return <People s={s} lang={lang} />;
    case "announcements": return <Announcements s={s} />;
    case "discussions": return <Discussions s={s} />;
    case "modules": return <Modules s={s} />;
    default: return <Home s={s} lang={lang} toolHref={toolHref} />;
  }
}

// ---- Home ------------------------------------------------------------------
function Home({ s, lang, toolHref }: { s: SimStrings; lang: Lang; toolHref: string }) {
  return (
    <>
      <h1 style={h1Style}>{localizeCourseLabel("CS 101 — Intro to Computer Science", lang)}</h1>
      <p style={{ color: MUTED, margin: "0 0 18px" }}>{s.welcome}</p>
      <div style={{ background: "#fff", border: `1px solid ${DIVIDER}`, borderInlineStartWidth: 4,
        borderInlineStartColor: BLUE, borderInlineStartStyle: "solid", borderRadius: 4, padding: 18, marginBottom: 26 }}>
        <h3 style={{ margin: "0 0 6px", fontSize: 18, fontWeight: 700, color: TEXT }}>{s.instructorAdded}</h3>
        <p style={{ color: MUTED, margin: "0 0 14px" }}>{s.instructorBody}</p>
        <a href={toolHref} style={{ ...primaryBtn, textDecoration: "none" }}>{s.openBridge}</a>
      </div>
      <h2 style={{ fontSize: 20, fontWeight: 700, color: TEXT, margin: "0 0 12px" }}>{s.latest}</h2>
      <div style={{ borderTop: `1px solid ${DIVIDER}`, paddingTop: 12 }}>
        <a href="#" style={{ ...linkStyle, fontWeight: 700, fontSize: 15 }}>{s.midtermTitle}</a>
        <p style={{ color: MUTED, margin: "6px 0 0" }}>{s.midtermBody}</p>
      </div>
    </>
  );
}

// ---- People ----------------------------------------------------------------
function People({ s, lang }: { s: SimStrings; lang: Lang }) {
  const th: CSSProperties = { textAlign: "start", fontSize: 13, fontWeight: 700, color: TEXT,
    padding: "10px 12px", borderBottom: `2px solid ${DIVIDER}`, whiteSpace: "nowrap" };
  const td: CSSProperties = { padding: "10px 12px", color: TEXT, verticalAlign: "middle" };
  return (
    <>
      <h1 style={h1Style}>{s.people}</h1>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
          <span style={{ background: "#fff", border: `1px solid ${BORDER}`, borderRadius: 4, color: TEXT,
            padding: "8px 16px", fontWeight: 600 }}>{s.everyone}</span>
          <a href="#" style={linkStyle}>{s.groups}</a>
        </div>
        <button type="button" style={primaryBtn}>{s.groupSet}</button>
      </div>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, marginBottom: 16 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ position: "relative", display: "inline-flex", alignItems: "center" }}>
            <span style={{ position: "absolute", insetInlineStart: 10, color: MUTED, fontSize: 15 }}>⌕</span>
            <input style={{ ...inputStyle, width: 300, paddingInlineStart: 30 }} placeholder={s.searchPeople} />
          </span>
          <select style={{ ...inputStyle, minWidth: 130 }} defaultValue="all">
            <option value="all">{s.allRoles}</option>
            <option value="teacher">{s.teacher}</option>
            <option value="student">{s.student}</option>
          </select>
        </div>
        <button type="button" style={primaryBtn}>{s.peopleBtn}</button>
      </div>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th style={th}>{s.thName}</th>
            <th style={th}>{s.thLogin}</th>
            <th style={th}>{s.thSis}</th>
            <th style={th}>{s.thSection}</th>
            <th style={th}>{s.thRole}</th>
            <th style={th}>{s.thLast}</th>
            <th style={th}>{s.thTotal}</th>
            <th style={{ ...th, width: 32 }} aria-label="Options" />
          </tr>
        </thead>
        <tbody>
          {ROSTER.map((p, i) => (
            <tr key={p.sis} style={{ borderBottom: `1px solid ${DIVIDER}`, background: i % 2 === 1 ? "#F8F9FA" : "#fff" }}>
              <td style={td}>
                <span style={{ display: "inline-flex", alignItems: "center", gap: 10 }}>
                  <Avatar name={localizeName(p.name, lang)} />
                  <a href="#" style={{ ...linkStyle, fontWeight: 600 }}>{localizeName(p.name, lang)}</a>
                </span>
              </td>
              <td style={{ ...td, color: MUTED }}>{p.login}</td>
              <td style={{ ...td, color: MUTED }}>{p.sis}</td>
              <td style={td}>{p.section}</td>
              <td style={td}>{p.role === "teacher" ? s.teacher : s.student}</td>
              <td style={{ ...td, color: MUTED }}>{p.last}</td>
              <td style={{ ...td, color: MUTED }}>{p.total}</td>
              <td style={{ ...td, textAlign: "end" }}><Kebab /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}

// ---- Announcements ---------------------------------------------------------
function Announcements({ s }: { s: SimStrings }) {
  const disabledIconBtn: CSSProperties = { ...secondaryBtn, color: MUTED, cursor: "default", opacity: 0.6, padding: "8px 10px" };
  return (
    <>
      <h1 style={h1Style}>{s.announcements}</h1>
      <div style={{ marginBottom: 14 }}>
        <select style={{ ...inputStyle, width: "100%" }} defaultValue="all">
          <option value="all">{s.all}</option>
          <option value="unread">{s.unread}</option>
        </select>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6, flexWrap: "wrap" }}>
        <input style={{ ...inputStyle, flex: 1 }} placeholder={s.searchDots} />
        <button type="button" style={primaryBtn}>{s.addAnnouncement}</button>
        <button type="button" style={secondaryBtn}>{s.markAllRead}</button>
        <button type="button" style={disabledIconBtn} disabled aria-label="Delete">🗑</button>
        <button type="button" style={disabledIconBtn} disabled aria-label="Lock">🔒</button>
      </div>
      <div style={{ textAlign: "end", marginBottom: 6 }}>
        <a href="#" style={linkStyle}>{s.externalFeeds}</a>
      </div>
      <div style={{ borderTop: `1px solid ${DIVIDER}` }}>
        {s.annItems.map((a) => (
          <div key={a.title} style={{ display: "flex", alignItems: "flex-start", gap: 14, padding: "16px 0",
            borderBottom: `1px solid ${DIVIDER}` }}>
            <input type="checkbox" style={{ marginTop: 6 }} aria-label={a.title} />
            <Avatar name="HA" size={40} bg="#E9EEF2" color={BLUE} />
            <div style={{ flex: 1, minWidth: 0 }}>
              <a href="#" style={{ ...linkStyle, fontWeight: 700, fontSize: 15 }}>{a.title}</a>
              <div style={{ color: MUTED, fontSize: 13, margin: "2px 0 6px" }}>{s.allSections}</div>
              <div style={{ color: MUTED, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{a.body}</div>
              <a href="#" style={{ ...linkStyle, display: "inline-block", marginTop: 8 }}>{s.reply}</a>
            </div>
            <div style={{ textAlign: "end", minWidth: 160, whiteSpace: "nowrap" }}>
              <div style={{ fontWeight: 700, color: TEXT }}>{s.postedOn}</div>
              <div style={{ color: MUTED, fontSize: 13 }}>{a.posted}</div>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}

// ---- Quizzes (rendered for the "assignments" route) ------------------------
function Quizzes({ s }: { s: SimStrings }) {
  return (
    <>
      <h1 style={h1Style}>{s.quizzes}</h1>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "flex-end", gap: 10, marginBottom: 16 }}>
        <input style={{ ...inputStyle, width: 220 }} placeholder={s.searchQuiz} />
        <button type="button" style={primaryBtn}>{s.addQuiz}</button>
        <Kebab />
      </div>
      <div style={{ background: ROW_HOVER, border: `1px solid ${DIVIDER}`, padding: "10px 14px", fontWeight: 700, color: TEXT }}>
        {s.assignmentQuizzes}
      </div>
      <div style={{ border: `1px solid ${DIVIDER}`, borderTop: "none" }}>
        {s.quizItems.map((q) => (
          <div key={q.title} style={{ display: "flex", alignItems: "center", gap: 12, padding: "14px 14px",
            borderInlineStart: `4px solid ${GREEN}`, borderBottom: `1px solid ${DIVIDER}` }}>
            <span aria-hidden style={{ fontSize: 16 }}>🚀</span>
            <div style={{ flex: 1, minWidth: 0 }}>
              <a href="#" style={{ color: TEXT, fontWeight: 700, textDecoration: "none" }}>{q.title}</a>
              <div style={{ color: MUTED, fontSize: 13, marginTop: 3 }}>
                {s.closed}   ·   {q.due}   ·   {q.pts} {s.ptsWord}   ·   {q.qn} {s.questionsWord}
              </div>
            </div>
            <GreenCheck />
            <Kebab />
          </div>
        ))}
      </div>
    </>
  );
}

// ---- Gradebook (rendered for the "grades" route) ---------------------------
function Gradebook({ s, lang }: { s: SimStrings; lang: Lang }) {
  const cellBorder = `1px solid ${DIVIDER}`;
  const firstColStyle: CSSProperties = { padding: "10px 12px", border: cellBorder, background: "#fff",
    fontWeight: 700, textAlign: "start", position: "sticky", insetInlineStart: 0, minWidth: 180, color: TEXT };
  return (
    <>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
        <span style={{ fontSize: 24, fontWeight: 700, color: TEXT }}>
          {s.gradebook} <span style={{ color: MUTED, fontSize: 16 }}>▾</span>
        </span>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <button type="button" style={{ ...secondaryBtn, padding: "8px 10px" }} aria-label="Keyboard shortcuts">⌨</button>
          <button type="button" style={secondaryBtn}>{s.importBtn}</button>
          <button type="button" style={secondaryBtn}>{s.exportBtn}</button>
          <button type="button" style={{ ...secondaryBtn, padding: "8px 10px" }} aria-label="Settings">⚙</button>
        </div>
      </div>
      <div style={{ display: "flex", gap: 24, marginBottom: 12, flexWrap: "wrap" }}>
        <div>
          <div style={{ fontSize: 13, fontWeight: 700, color: TEXT, marginBottom: 6 }}>{s.studentNames}</div>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <input style={{ ...inputStyle, width: 220 }} placeholder={s.searchStudents} />
            <span style={{ color: MUTED }}>▾</span>
          </div>
        </div>
        <div>
          <div style={{ fontSize: 13, fontWeight: 700, color: TEXT, marginBottom: 6 }}>{s.assignmentNames}</div>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <input style={{ ...inputStyle, width: 220 }} placeholder={s.searchAssignments} />
            <span style={{ color: MUTED }}>▾</span>
          </div>
        </div>
      </div>
      <div style={{ marginBottom: 16 }}>
        <button type="button" style={secondaryBtn}>{s.applyFilters}</button>
      </div>
      <div style={{ overflowX: "auto", border: `1px solid ${DIVIDER}` }}>
        <table style={{ borderCollapse: "collapse", width: "100%", minWidth: 900 }}>
          <thead>
            <tr>
              <th style={{ ...firstColStyle, background: ROW_HOVER, zIndex: 1 }}>{s.studentName}</th>
              {s.gradeCols.map((c, i) => (
                <th key={i} style={{ padding: "8px 12px", border: cellBorder, background: ROW_HOVER,
                  minWidth: 120, textAlign: "start", verticalAlign: "top" }}>
                  <div style={{ fontWeight: 700, color: TEXT }}>{c}</div>
                  <div style={{ color: MUTED, fontWeight: 400, fontSize: 12 }}>{s.outOf.replace("{{n}}", String(GRADE_OUT[i]))}</div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {GRADE_ROWS.map((r) => (
              <tr key={r.student}>
                <td style={firstColStyle}>
                  <a href="#" style={{ ...linkStyle, fontWeight: 600 }}>{localizeName(r.student, lang)}</a>
                </td>
                {r.scores.map((sc, i) => (
                  <td key={i} style={{ padding: "10px 12px", border: cellBorder,
                    color: sc === "—" ? MUTED : TEXT, textAlign: "end" }}>{sc}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

// ---- Discussions -----------------------------------------------------------
function Discussions({ s }: { s: SimStrings }) {
  return (
    <>
      <h1 style={h1Style}>{s.discussions}</h1>
      <div style={{ borderTop: `1px solid ${DIVIDER}` }}>
        {s.discTopics.map((topic, i) => (
          <div key={topic} style={{ display: "flex", alignItems: "center", justifyContent: "space-between",
            padding: "14px 0", borderBottom: `1px solid ${DIVIDER}` }}>
            <a href="#" style={{ ...linkStyle, fontWeight: 600 }}>{topic}</a>
            <span style={{ color: MUTED, fontSize: 13 }}>{REPLY_COUNTS[i]} {s.repliesWord}</span>
          </div>
        ))}
      </div>
    </>
  );
}

// ---- Modules ---------------------------------------------------------------
function Modules({ s }: { s: SimStrings }) {
  return (
    <>
      <h1 style={h1Style}>{s.modules}</h1>
      <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        {s.modItems.map((m) => (
          <div key={m.title} style={{ border: `1px solid ${DIVIDER}`, borderRadius: 4 }}>
            <div style={{ background: ROW_HOVER, padding: "10px 14px", fontWeight: 700, color: TEXT,
              borderBottom: `1px solid ${DIVIDER}` }}>{m.title}</div>
            <ul style={{ margin: 0, padding: "10px 30px", color: TEXT }}>
              {m.items.map((it) => (
                <li key={it} style={{ padding: "4px 0" }}><a href="#" style={linkStyle}>{it}</a></li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </>
  );
}
