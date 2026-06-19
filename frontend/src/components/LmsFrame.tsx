import type { ReactNode, CSSProperties } from "react";

export type LmsId = "canvas" | "blackboard" | "moodle" | "brightspace";
export type LmsPage =
  | "home" | "announcements" | "assignments" | "grades"
  | "people" | "modules" | "discussions" | "tool";

export const LMS_CONFIG: Record<LmsId, { label: string; font: string }> = {
  canvas: { label: "Canvas", font: "Lato" },
  blackboard: { label: "Blackboard", font: "Open Sans" },
  moodle: { label: "Moodle", font: "Open Sans" },
  brightspace: { label: "Brightspace", font: "Lato" },
};

const COURSE = "CS 101";
const COURSE_LONG = "CS 101 · Intro to Computer Science";
const CONTENT_BG = "#f4f5f7";
const VH = "calc(100vh - 46px)";

export function pageFor(label: string): LmsPage {
  const l = label.toLowerCase();
  if (l.includes("bridge")) return "tool";
  if (l.includes("announce")) return "announcements";
  if (l.includes("assignment") || l.includes("quiz") || l.includes("content")) return "assignments";
  if (l.includes("grade")) return "grades";
  if (l.includes("people") || l.includes("participant") || l.includes("classlist") || l.includes("roster")) return "people";
  if (l.includes("module")) return "modules";
  if (l.includes("discussion")) return "discussions";
  return "home";
}
export function pageLabel(p: LmsPage): string {
  return p === "tool" ? "LMS Bridge" : p.charAt(0).toUpperCase() + p.slice(1);
}

interface FrameProps {
  lms: LmsId;
  role: "student" | "instructor";
  activePage: LmsPage;
  linkFor: (p: LmsPage) => string;
  children: ReactNode;
}

const FONT = (name: string) =>
  `"${name}", -apple-system, "Helvetica Neue", Arial, sans-serif`;

// A simple rounded-square brand mark (a stand-in, NOT the vendor logo).
function Mark({ bg, fg, text, size = 30 }: { bg: string; fg: string; text: string; size?: number }) {
  return (
    <span aria-hidden style={{ width: size, height: size, borderRadius: 7, background: bg,
      color: fg, display: "inline-flex", alignItems: "center", justifyContent: "center",
      fontWeight: 800, fontSize: size * 0.46, flex: "0 0 auto" }}>{text}</span>
  );
}

function I({ d, s = 18 }: { d: string; s?: number }) {
  return (
    <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke="currentColor"
      strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
      <path d={d} />
    </svg>
  );
}
const IC = {
  home: "M3 11l9-8 9 8M5 10v10h14V10",
  grid: "M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h6v6h-6z",
  cal: "M3 5h18v16H3zM3 9h18M8 3v4M16 3v4",
  mail: "M3 6h18v12H3zM3 6l9 7 9-7",
  clock: "M12 3a9 9 0 100 18 9 9 0 000-18zM12 8v4l3 2",
  help: "M9 9a3 3 0 114 2.8c-1 .6-1 1.2-1 2.2M12 17h.01",
  bell: "M6 9a6 6 0 1112 0c0 5 2 6 2 6H4s2-1 2-6M10 21a2 2 0 004 0",
  tools: "M14 7l3 3-7 7-3 3-3-3 3-3 7-7zM14 7l3-3 3 3-3 3",
  chat: "M21 15a2 2 0 01-2 2H8l-4 4V6a2 2 0 012-2h13a2 2 0 012 2z",
  gear: "M12 15a3 3 0 100-6 3 3 0 000 6zM19.4 13a7.6 7.6 0 000-2l2-1.5-2-3.4-2.4 1a7.5 7.5 0 00-1.7-1L14.5 3h-5l-.8 2.6a7.5 7.5 0 00-1.7 1l-2.4-1-2 3.4 2 1.5a7.6 7.6 0 000 2l-2 1.5 2 3.4 2.4-1a7.5 7.5 0 001.7 1l.8 2.6h5l.8-2.6a7.5 7.5 0 001.7-1l2.4 1 2-3.4z",
};

function Waffle({ color = "#3a4654" }: { color?: string }) {
  return (
    <span aria-hidden style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 2.5 }}>
      {Array.from({ length: 9 }).map((_, i) =>
        <span key={i} style={{ width: 4, height: 4, background: color, borderRadius: 1 }} />)}
    </span>
  );
}
function Dots() {
  return <span aria-hidden style={{ color: "#c9ced3", fontSize: 16, lineHeight: 1 }}>⋮</span>;
}

function sideStyle(active: boolean, accent: string): CSSProperties {
  return {
    padding: active ? "9px 16px 9px 13px" : "9px 16px",
    borderLeft: active ? `3px solid ${accent}` : "3px solid transparent",
    background: active ? "#f3f6fa" : "transparent",
    fontWeight: active ? 700 : 400,
    color: active ? "#0a1a2b" : "#3a4654",
    fontSize: 13.5, textDecoration: "none", display: "block",
  };
}
function SideNav({ labels, accent, activePage, linkFor }: {
  labels: string[]; accent: string; activePage: LmsPage; linkFor: (p: LmsPage) => string;
}) {
  return (
    <>
      {labels.map((label) => {
        const page = pageFor(label);
        return (
          <a key={label} href={linkFor(page)} style={sideStyle(page === activePage, accent)}>{label}</a>
        );
      })}
    </>
  );
}

// ============================ Canvas ============================
function Canvas({ activePage, linkFor, children }: Omit<FrameProps, "lms">) {
  const glob: [keyof typeof IC, string][] = [
    ["grid", "Dashboard"], ["home", "Courses"], ["cal", "Calendar"],
    ["mail", "Inbox"], ["clock", "History"], ["help", "Help"],
  ];
  const nav = ["Home", "Announcements", "Assignments", "Discussions", "Grades",
    "People", "Pages", "Files", "Modules", "LMS Bridge"];
  return (
    <div style={{ display: "flex", minHeight: VH, background: CONTENT_BG, fontFamily: FONT("Lato") }}>
      <div style={{ width: 84, background: "#394B58", color: "#fff", display: "flex",
        flexDirection: "column", alignItems: "center", padding: "12px 0", gap: 2 }}>
        <div style={{ width: 42, height: 42, borderRadius: "50%", background: "#0a1a2b",
          color: "#fff", display: "flex", alignItems: "center", justifyContent: "center",
          fontWeight: 700, marginBottom: 10 }}>SL</div>
        {glob.map(([ic, l]) => (
          <a key={l} href={linkFor("home")} style={{ textAlign: "center", padding: "8px 0",
            width: "100%", color: "#fff", textDecoration: "none", opacity: .95 }}>
            <I d={IC[ic]} s={22} />
            <div style={{ fontSize: 10, marginTop: 2 }}>{l}</div>
          </a>
        ))}
      </div>
      <div style={{ width: 184, background: "#fff", borderRight: "1px solid #d9dde1", padding: "14px 0" }}>
        <div style={{ padding: "0 16px 10px", fontWeight: 700, color: "#E0061F", fontSize: 14 }}>{COURSE}</div>
        <SideNav labels={nav} accent="#0374B5" activePage={activePage} linkFor={linkFor} />
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ padding: "10px 22px", fontSize: 12.5, color: "#6b7780", background: "#fff",
          borderBottom: "1px solid #ebedf0" }}>
          {COURSE} <span style={{ margin: "0 6px" }}>›</span>
          <b style={{ color: "#2d3b45" }}>{pageLabel(activePage)}</b>
        </div>
        {children}
      </div>
    </div>
  );
}

// ============================ Blackboard (Ultra) ============================
function Blackboard({ activePage, linkFor, children }: Omit<FrameProps, "lms">) {
  const base: [keyof typeof IC, string][] = [
    ["home", "Institution Page"], ["grid", "Courses"], ["cal", "Calendar"],
    ["mail", "Messages"], ["clock", "Grades"], ["tools", "Tools"],
  ];
  const nav = ["Content", "Calendar", "Announcements", "Discussions", "Gradebook",
    "Messages", "People", "Modules", "LMS Bridge"];
  return (
    <div style={{ display: "flex", minHeight: VH, background: CONTENT_BG, fontFamily: FONT("Open Sans") }}>
      <div style={{ width: 150, background: "#262626", color: "#d6d6d6", padding: "14px 0" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 9, padding: "0 14px 14px" }}>
          <Mark bg="#fff" fg="#262626" text="Bb" size={26} />
          <span style={{ color: "#fff", fontWeight: 700, fontSize: 13 }}>Blackboard</span>
        </div>
        {base.map(([ic, l]) => (
          <a key={l} href={linkFor(pageFor(l))} style={{ display: "flex", alignItems: "center",
            gap: 10, padding: "10px 14px", color: "#d6d6d6", textDecoration: "none", fontSize: 12.5 }}>
            <I d={IC[ic]} s={17} /> {l}
          </a>
        ))}
      </div>
      <div style={{ width: 196, background: "#fff", borderRight: "1px solid #d9dde1", padding: "16px 0" }}>
        <div style={{ padding: "0 18px 12px" }}>
          <div style={{ fontSize: 11, color: "#6b7780", textTransform: "uppercase", letterSpacing: .4 }}>Course</div>
          <div style={{ fontWeight: 700, color: "#11161b", fontSize: 15 }}>{COURSE}</div>
        </div>
        <SideNav labels={nav} accent="#c2113a" activePage={activePage} linkFor={linkFor} />
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ padding: "12px 24px", fontSize: 13, color: "#6b7780", background: "#fff",
          borderBottom: "1px solid #ebedf0" }}>
          {COURSE_LONG} <span style={{ margin: "0 6px" }}>›</span>
          <b style={{ color: "#262626" }}>{pageLabel(activePage)}</b>
        </div>
        {children}
      </div>
    </div>
  );
}

// ============================ Moodle (Boost) ============================
function Moodle({ activePage, linkFor, children }: Omit<FrameProps, "lms">) {
  const tabs = ["Course", "Participants", "Grades", "Announcements", "More"];
  return (
    <div style={{ minHeight: VH, background: CONTENT_BG, fontFamily: FONT("Open Sans") }}>
      <div style={{ background: "#0f6cbf", color: "#fff", height: 52, display: "flex",
        alignItems: "center", gap: 14, padding: "0 18px" }}>
        <span aria-hidden style={{ fontSize: 20, opacity: .95 }}>≡</span>
        <span style={{ fontWeight: 700, fontSize: 19, letterSpacing: -.3 }}>moodle</span>
        <span style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 14, color: "#fff" }}>
          <I d={IC.mail} s={18} /><I d={IC.bell} s={18} />
          <span style={{ display: "flex", alignItems: "center", gap: 7, fontSize: 13 }}>
            <span style={{ width: 28, height: 28, borderRadius: "50%", background: "#fff",
              color: "#0f6cbf", display: "flex", alignItems: "center", justifyContent: "center",
              fontWeight: 700 }}>SL</span>Sam Lee ▾</span>
        </span>
      </div>
      <div style={{ background: "#fff", borderBottom: "1px solid #dee2e6", padding: "14px 22px 0" }}>
        <div style={{ fontSize: 19, fontWeight: 700, color: "#1d2125", marginBottom: 8 }}>{COURSE_LONG}</div>
        <div style={{ display: "flex", gap: 22, fontSize: 14 }}>
          {tabs.map((t) => {
            const on = pageFor(t) === activePage;
            return (
              <a key={t} href={linkFor(pageFor(t))} style={{ color: on ? "#0f6cbf" : "#5d6772",
                borderBottom: on ? "3px solid #0f6cbf" : "3px solid transparent", paddingBottom: 10,
                textDecoration: "none", fontWeight: on ? 700 : 400 }}>{t}</a>
            );
          })}
        </div>
      </div>
      <div style={{ display: "flex", minHeight: "calc(100vh - 46px - 52px - 86px)" }}>
        <div style={{ width: 220, background: "#fff", borderRight: "1px solid #dee2e6", padding: "16px 0" }}>
          <div style={{ padding: "0 16px 10px", fontWeight: 700, fontSize: 13, color: "#1d2125" }}>Course index</div>
          {["General", "Number systems", "Logic", "Machine code"].map((n) => (
            <a key={n} href={linkFor("modules")} style={{ padding: "7px 16px", display: "block",
              fontSize: 13, color: "#3a4654", textDecoration: "none" }}>{n}</a>
          ))}
          <a href={linkFor("tool")} style={{ padding: "7px 16px 7px 13px", display: "block",
            borderLeft: "3px solid #f98012", fontWeight: 700, fontSize: 13, color: "#1d2125",
            textDecoration: "none", background: activePage === "tool" ? "#fff5ec" : "transparent" }}>
            LMS Bridge</a>
        </div>
        <div style={{ flex: 1, minWidth: 0, background: CONTENT_BG }}>{children}</div>
      </div>
    </div>
  );
}

// ============================ Brightspace (D2L "Daylight") ============================
function Brightspace({ role, activePage, linkFor, children }: Omit<FrameProps, "lms">) {
  // White header + white navbar with bold black links and a blue active accent (D2L Daylight).
  // Classlist/People is an instructor-only tool in Brightspace — hide it for students.
  const nav = ["Content", "Announcements", "Assignments", "Discussions", "Quizzes", "Grades",
    ...(role === "instructor" ? ["Classlist"] : []), "LMS Bridge"];
  const drop = ["More Tools", "Course Reports", "Help"];
  const BLUE = "#006fbf";
  const icon = { color: "#3a4654", display: "flex", alignItems: "center" } as CSSProperties;
  return (
    <div style={{ minHeight: VH, background: "#fafbfc", fontFamily: FONT("Lato") }}>
      {/* Header: logo · course title …… waffle | mail chat bell | avatar name gear */}
      <div style={{ background: "#fff", height: 64, display: "flex", alignItems: "center",
        gap: 16, padding: "0 22px", borderBottom: "1px solid #e6e9ed" }}>
        <Mark bg="#5a2a4d" fg="#fff" text="N" size={28} />
        <Dots />
        <span style={{ fontWeight: 700, fontSize: 18, color: "#202122" }}>{COURSE_LONG}</span>
        <span style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 16 }}>
          <span style={icon}><Waffle /></span>
          <Dots />
          <span style={icon}><I d={IC.mail} s={20} /></span>
          <span style={icon}><I d={IC.chat} s={20} /></span>
          <span style={icon}><I d={IC.bell} s={20} /></span>
          <Dots />
          <span style={{ width: 32, height: 32, borderRadius: 6, background: "#8a1f4c",
            color: "#fff", display: "flex", alignItems: "center", justifyContent: "center",
            fontWeight: 700, fontSize: 13 }}>SL</span>
          <span style={{ fontWeight: 700, fontSize: 14, color: "#202122" }}>Sam Lee</span>
          <span style={icon}><I d={IC.gear} s={20} /></span>
        </span>
      </div>
      {/* Navbar: bold black links, blue underline on the active one */}
      <div style={{ background: "#fff", borderBottom: "1px solid #e6e9ed", display: "flex",
        alignItems: "stretch", gap: 4, padding: "0 22px", flexWrap: "wrap", minHeight: 50 }}>
        {nav.map((n) => {
          const on = pageFor(n) === activePage;
          return (
            <a key={n} href={linkFor(pageFor(n))} style={{ display: "flex", alignItems: "center",
              padding: "0 14px", fontSize: 15, fontWeight: 700, textDecoration: "none",
              color: on ? BLUE : "#2d3338",
              borderBottom: on ? `3px solid ${BLUE}` : "3px solid transparent" }}>{n}</a>
          );
        })}
        {drop.map((n) => (
          <span key={n} style={{ display: "flex", alignItems: "center", padding: "0 14px",
            fontSize: 15, fontWeight: 700, color: "#2d3338" }}>{n} <span aria-hidden
              style={{ marginLeft: 5, color: "#6b7780" }}>▾</span></span>
        ))}
      </div>
      {children}
    </div>
  );
}

export default function LmsFrame(props: FrameProps) {
  const { lms, ...rest } = props;
  if (lms === "blackboard") return <Blackboard {...rest} />;
  if (lms === "moodle") return <Moodle {...rest} />;
  if (lms === "brightspace") return <Brightspace {...rest} />;
  return <Canvas {...rest} />;
}
