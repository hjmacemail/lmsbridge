import type { CSSProperties } from "react";
import type { LmsId, LmsPage } from "./LmsFrame";

// Plausible, static "LMS content" pages for the demo, styled to closely resemble the real
// Canvas LMS UI. The only real, interactive page is the tool (rendered by DemoPage). All
// styling here is inline so it does not inherit the product's card/pill/btn look.

// ---- Canvas design tokens -------------------------------------------------
const BLUE = "#0374B5";
const TEXT = "#2D3B45";
const MUTED = "#6B7780";
const BORDER = "#C7CDD1";
const DIVIDER = "#E8EAEC";
const ROW_HOVER = "#F5F5F5";
const STRIPE = "#E9EEF2";
const GREEN = "#0B874B";

const primaryBtn: CSSProperties = {
  background: BLUE,
  color: "#fff",
  border: "none",
  borderRadius: 4,
  padding: "8px 14px",
  fontSize: 14,
  fontWeight: 600,
  cursor: "pointer",
  display: "inline-flex",
  alignItems: "center",
  gap: 6,
};

const secondaryBtn: CSSProperties = {
  background: "#fff",
  color: TEXT,
  border: `1px solid ${BORDER}`,
  borderRadius: 4,
  padding: "8px 12px",
  fontSize: 14,
  cursor: "pointer",
  display: "inline-flex",
  alignItems: "center",
  gap: 6,
};

const inputStyle: CSSProperties = {
  border: `1px solid ${BORDER}`,
  borderRadius: 4,
  padding: "8px 12px",
  fontSize: 14,
  color: TEXT,
  background: "#fff",
};

const linkStyle: CSSProperties = { color: BLUE, textDecoration: "none" };

const pageWrap: CSSProperties = {
  background: "#fff",
  color: TEXT,
  fontSize: 14,
  lineHeight: 1.5,
  padding: "18px 22px 40px",
  maxWidth: 1180,
  margin: "0 auto",
};

const h1Style: CSSProperties = {
  fontSize: 24,
  fontWeight: 700,
  color: TEXT,
  margin: "0 0 16px",
};

function Kebab() {
  return (
    <button
      type="button"
      aria-label="Options"
      style={{
        border: "none",
        background: "transparent",
        color: MUTED,
        fontSize: 18,
        lineHeight: 1,
        cursor: "pointer",
        padding: "2px 6px",
      }}
    >
      ⋮
    </button>
  );
}

function initials(name: string): string {
  const parts = name.replace(/^Dr\.\s*/i, "").trim().split(/\s+/);
  const first = parts[0]?.[0] ?? "";
  const last = parts.length > 1 ? parts[parts.length - 1][0] : "";
  return (first + last).toUpperCase();
}

function Avatar({ name, size = 32, bg = BORDER, color = "#fff" }: {
  name: string;
  size?: number;
  bg?: string;
  color?: string;
}) {
  return (
    <span
      aria-hidden
      style={{
        width: size,
        height: size,
        minWidth: size,
        borderRadius: "50%",
        background: bg,
        color,
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: Math.round(size * 0.38),
        fontWeight: 700,
      }}
    >
      {initials(name)}
    </span>
  );
}

export default function SimPage(
  { page, lms, toolHref }: { page: LmsPage; lms: LmsId; toolHref: string },
) {
  // Styled as Canvas regardless of `lms` (Canvas is the demo default).
  void lms;
  return (
    <div style={pageWrap}>
      <div style={{ fontSize: 12.5, color: MUTED, marginBottom: 14 }}>
        Simulated Canvas page — example content. The real, interactive piece is{" "}
        <a href={toolHref} style={{ color: BLUE }}>LMS Bridge</a>.
      </div>
      {render(page, toolHref)}
    </div>
  );
}

function render(page: LmsPage, toolHref: string) {
  switch (page) {
    case "assignments": return <Quizzes />;
    case "grades": return <Gradebook />;
    case "people": return <People />;
    case "announcements": return <Announcements />;
    case "discussions": return <Discussions />;
    case "modules": return <Modules />;
    default: return <Home toolHref={toolHref} />;
  }
}

// ---- Home ------------------------------------------------------------------
function Home({ toolHref }: { toolHref: string }) {
  return (
    <>
      <h1 style={h1Style}>CS 101 — Intro to Computer Science</h1>
      <p style={{ color: MUTED, margin: "0 0 18px" }}>
        Welcome to the course. Use the menu to reach assignments, grades, and your learning
        support.
      </p>
      <div
        style={{
          borderLeft: `4px solid ${BLUE}`,
          background: "#fff",
          border: `1px solid ${DIVIDER}`,
          borderLeftWidth: 4,
          borderLeftColor: BLUE,
          borderRadius: 4,
          padding: 18,
          marginBottom: 26,
        }}
      >
        <h3 style={{ margin: "0 0 6px", fontSize: 18, fontWeight: 700, color: TEXT }}>
          Your instructor added LMS Bridge
        </h3>
        <p style={{ color: MUTED, margin: "0 0 14px" }}>
          Personalized, just-in-time tutoring based on your assessment results. Open it to see
          your recommended practice.
        </p>
        <a href={toolHref} style={{ ...primaryBtn, textDecoration: "none" }}>Open LMS Bridge</a>
      </div>
      <h2 style={{ fontSize: 20, fontWeight: 700, color: TEXT, margin: "0 0 12px" }}>
        Latest announcements
      </h2>
      <div style={{ borderTop: `1px solid ${DIVIDER}`, paddingTop: 12 }}>
        <a href="#" style={{ ...linkStyle, fontWeight: 700, fontSize: 15 }}>Midterm next week</a>
        <p style={{ color: MUTED, margin: "6px 0 0" }}>
          Covers number systems through Boolean logic. Review the practice set.
        </p>
      </div>
    </>
  );
}

// ---- People ----------------------------------------------------------------
type Person = {
  name: string;
  login: string;
  sis: string;
  section: string;
  role: string;
  last: string;
  total: string;
};

const roster: Person[] = [
  { name: "Dr. Alex Rivera", login: "a.rivera@uni.edu", sis: "1001", section: "CS 101", role: "Teacher", last: "Apr 30, 2025", total: "58:12" },
  { name: "Sam Lee", login: "s.lee@uni.edu", sis: "2043", section: "CS 101", role: "Student", last: "May 2, 2025", total: "24:07" },
  { name: "Ava Chen", login: "a.chen@uni.edu", sis: "2044", section: "CS 101", role: "Student", last: "May 1, 2025", total: "31:44" },
  { name: "Jordan Diaz", login: "j.diaz@uni.edu", sis: "2045", section: "CS 101", role: "Student", last: "Apr 27, 2025", total: "12:03" },
  { name: "Priya Patel", login: "p.patel@uni.edu", sis: "2046", section: "CS 101", role: "Student", last: "May 3, 2025", total: "40:19" },
];

function People() {
  const th: CSSProperties = {
    textAlign: "left",
    fontSize: 13,
    fontWeight: 700,
    color: TEXT,
    padding: "10px 12px",
    borderBottom: `2px solid ${DIVIDER}`,
    whiteSpace: "nowrap",
  };
  const td: CSSProperties = { padding: "10px 12px", color: TEXT, verticalAlign: "middle" };

  return (
    <>
      <h1 style={h1Style}>People</h1>

      {/* Tabs + Group Set */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
          <span
            style={{
              background: "#fff",
              border: `1px solid ${BORDER}`,
              borderRadius: 4,
              color: TEXT,
              padding: "8px 16px",
              fontWeight: 600,
            }}
          >
            Everyone
          </span>
          <a href="#" style={linkStyle}>Groups</a>
        </div>
        <button type="button" style={primaryBtn}>+ Group Set</button>
      </div>

      {/* Search + roles + People button */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, marginBottom: 16 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ position: "relative", display: "inline-flex", alignItems: "center" }}>
            <span style={{ position: "absolute", left: 10, color: MUTED, fontSize: 15 }}>⌕</span>
            <input style={{ ...inputStyle, width: 300, paddingLeft: 30 }} placeholder="Search people" />
          </span>
          <select style={{ ...inputStyle, minWidth: 130 }} defaultValue="all">
            <option value="all">All Roles</option>
            <option value="teacher">Teacher</option>
            <option value="student">Student</option>
          </select>
        </div>
        <button type="button" style={primaryBtn}>+ People</button>
      </div>

      {/* Table */}
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th style={th}>Name</th>
            <th style={th}>Login ID</th>
            <th style={th}>SIS ID</th>
            <th style={th}>Section</th>
            <th style={th}>Role</th>
            <th style={th}>Last Activity</th>
            <th style={th}>Total Activity</th>
            <th style={{ ...th, width: 32 }} aria-label="Options" />
          </tr>
        </thead>
        <tbody>
          {roster.map((p, i) => (
            <tr
              key={p.sis}
              style={{
                borderBottom: `1px solid ${DIVIDER}`,
                background: i % 2 === 1 ? "#F8F9FA" : "#fff",
              }}
            >
              <td style={td}>
                <span style={{ display: "inline-flex", alignItems: "center", gap: 10 }}>
                  <Avatar name={p.name} />
                  <a href="#" style={{ ...linkStyle, fontWeight: 600 }}>{p.name}</a>
                </span>
              </td>
              <td style={{ ...td, color: MUTED }}>{p.login}</td>
              <td style={{ ...td, color: MUTED }}>{p.sis}</td>
              <td style={td}>{p.section}</td>
              <td style={td}>{p.role}</td>
              <td style={{ ...td, color: MUTED }}>{p.last}</td>
              <td style={{ ...td, color: MUTED }}>{p.total}</td>
              <td style={{ ...td, textAlign: "right" }}><Kebab /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}

// ---- Announcements ---------------------------------------------------------
type Ann = { title: string; body: string; posted: string };

const announcements: Ann[] = [
  {
    title: "Final Exam Grades",
    body: "Dear Class, Final Exam grades are now available through coursework (You should be able to see …",
    posted: "May 4, 2025, 9:21 PM",
  },
  {
    title: "Final Review Session",
    body: "Dear students, I have changed this week's OH to Wednesday 5:00 – 6:00 PM on Zoom, to help y…",
    posted: "Apr 28, 2025, 7:21 PM",
  },
  {
    title: "Assignment 5 posted",
    body: "The last homework is up; it covers hypothesis testing. Due next Friday, 11:59 PM.",
    posted: "Apr 20, 2025, 3:10 PM",
  },
];

function Announcements() {
  const disabledIconBtn: CSSProperties = {
    ...secondaryBtn,
    color: MUTED,
    cursor: "default",
    opacity: 0.6,
    padding: "8px 10px",
  };
  return (
    <>
      <h1 style={h1Style}>Announcements</h1>

      <div style={{ marginBottom: 14 }}>
        <select style={{ ...inputStyle, width: "100%" }} defaultValue="all">
          <option value="all">All</option>
          <option value="unread">Unread</option>
        </select>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
        <input style={{ ...inputStyle, flex: 1 }} placeholder="Search…" />
        <button type="button" style={primaryBtn}>+ Add Announcement</button>
        <button type="button" style={secondaryBtn}>✉ Mark All as Read</button>
        <button type="button" style={disabledIconBtn} disabled aria-label="Delete">🗑</button>
        <button type="button" style={disabledIconBtn} disabled aria-label="Lock">🔒</button>
      </div>

      <div style={{ textAlign: "right", marginBottom: 6 }}>
        <a href="#" style={linkStyle}>External Feeds</a>
      </div>

      <div style={{ borderTop: `1px solid ${DIVIDER}` }}>
        {announcements.map((a) => (
          <div
            key={a.title}
            style={{
              display: "flex",
              alignItems: "flex-start",
              gap: 14,
              padding: "16px 0",
              borderBottom: `1px solid ${DIVIDER}`,
            }}
          >
            <input type="checkbox" style={{ marginTop: 6 }} aria-label={`Select ${a.title}`} />
            <Avatar name="Hasan A" size={40} bg={STRIPE} color={BLUE} />
            <div style={{ flex: 1, minWidth: 0 }}>
              <a href="#" style={{ ...linkStyle, fontWeight: 700, fontSize: 15 }}>{a.title}</a>
              <div style={{ color: MUTED, fontSize: 13, margin: "2px 0 6px" }}>All Sections</div>
              <div
                style={{
                  color: MUTED,
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                }}
              >
                {a.body}
              </div>
              <a href="#" style={{ ...linkStyle, display: "inline-block", marginTop: 8 }}>↩ Reply</a>
            </div>
            <div style={{ textAlign: "right", minWidth: 160, whiteSpace: "nowrap" }}>
              <div style={{ fontWeight: 700, color: TEXT }}>Posted on:</div>
              <div style={{ color: MUTED, fontSize: 13 }}>{a.posted}</div>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}

// ---- Quizzes (rendered for the "assignments" route) ------------------------
type Quiz = { title: string; meta: string };

const quizzes: Quiz[] = [
  { title: "Midterm Exam (Remotely Proctored)", meta: "Closed   Due Mar 6 at 7:50pm   20 pts   40 Questions" },
  { title: "Final Exam (Remotely Proctored)", meta: "Closed   Due May 1 at 8:00pm   20 pts   40 Questions" },
  { title: "Quiz 1 — Binary arithmetic", meta: "Closed   Due Feb 12 at 11:59pm   10 pts   8 Questions" },
];

function GreenCheck() {
  return (
    <span
      aria-hidden
      style={{
        width: 20,
        height: 20,
        borderRadius: "50%",
        background: GREEN,
        color: "#fff",
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: 12,
        fontWeight: 700,
      }}
    >
      ✓
    </span>
  );
}

function Quizzes() {
  return (
    <>
      <h1 style={h1Style}>Quizzes</h1>

      {/* Toolbar */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "flex-end", gap: 10, marginBottom: 16 }}>
        <input style={{ ...inputStyle, width: 220 }} placeholder="Search for Quiz" />
        <button type="button" style={primaryBtn}>+ Quiz</button>
        <Kebab />
      </div>

      {/* Group header */}
      <div
        style={{
          background: ROW_HOVER,
          border: `1px solid ${DIVIDER}`,
          padding: "10px 14px",
          fontWeight: 700,
          color: TEXT,
        }}
      >
        ▾ Assignment Quizzes
      </div>

      {/* Rows */}
      <div style={{ border: `1px solid ${DIVIDER}`, borderTop: "none" }}>
        {quizzes.map((q) => (
          <div
            key={q.title}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 12,
              padding: "14px 14px 14px 12px",
              borderLeft: `4px solid ${GREEN}`,
              borderBottom: `1px solid ${DIVIDER}`,
            }}
          >
            <span aria-hidden style={{ fontSize: 16 }}>🚀</span>
            <div style={{ flex: 1, minWidth: 0 }}>
              <a href="#" style={{ color: TEXT, fontWeight: 700, textDecoration: "none" }}>{q.title}</a>
              <div style={{ color: MUTED, fontSize: 13, marginTop: 3 }}>{q.meta}</div>
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
type GradeCol = { name: string; out: string };
const gradeCols: GradeCol[] = [
  { name: "Assignment-1", out: "Out of 10" },
  { name: "Assignment-2", out: "Out of 10" },
  { name: "Assignment-3", out: "Out of 10" },
  { name: "Assignment-4", out: "Out of 10" },
  { name: "Assignment-5", out: "Out of 10" },
  { name: "Roll Call Attendance", out: "Out of 100" },
  { name: "Midterm Exam", out: "Out of 20" },
];

type GradeRow = { student: string; scores: string[] };
const gradeRows: GradeRow[] = [
  { student: "Sam Lee", scores: ["9", "8", "10", "7", "—", "96", "17"] },
  { student: "Ava Chen", scores: ["10", "9", "9", "10", "8", "100", "19"] },
  { student: "Jordan Diaz", scores: ["6", "—", "7", "5", "—", "72", "11"] },
  { student: "Priya Patel", scores: ["10", "10", "9", "9", "10", "98", "20"] },
];

function Gradebook() {
  const cellBorder = `1px solid ${DIVIDER}`;
  const firstColStyle: CSSProperties = {
    padding: "10px 12px",
    border: cellBorder,
    background: "#fff",
    fontWeight: 700,
    textAlign: "left",
    position: "sticky",
    left: 0,
    minWidth: 180,
    color: TEXT,
  };

  return (
    <>
      {/* Header row */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
        <span style={{ fontSize: 24, fontWeight: 700, color: TEXT }}>
          Gradebook <span style={{ color: MUTED, fontSize: 16 }}>▾</span>
        </span>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <button type="button" style={{ ...secondaryBtn, padding: "8px 10px" }} aria-label="Keyboard shortcuts">⌨</button>
          <button type="button" style={secondaryBtn}>⇥ Import</button>
          <button type="button" style={secondaryBtn}>Export ▾</button>
          <button type="button" style={{ ...secondaryBtn, padding: "8px 10px" }} aria-label="Settings">⚙</button>
        </div>
      </div>

      {/* Filters */}
      <div style={{ display: "flex", gap: 24, marginBottom: 12, flexWrap: "wrap" }}>
        <div>
          <div style={{ fontSize: 13, fontWeight: 700, color: TEXT, marginBottom: 6 }}>Student Names</div>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <input style={{ ...inputStyle, width: 220 }} placeholder="Search Students" />
            <span style={{ color: MUTED }}>▾</span>
          </div>
        </div>
        <div>
          <div style={{ fontSize: 13, fontWeight: 700, color: TEXT, marginBottom: 6 }}>Assignment Names</div>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <input style={{ ...inputStyle, width: 220 }} placeholder="Search Assignments" />
            <span style={{ color: MUTED }}>▾</span>
          </div>
        </div>
      </div>
      <div style={{ marginBottom: 16 }}>
        <button type="button" style={secondaryBtn}>⏷ Apply Filters</button>
      </div>

      {/* Table */}
      <div style={{ overflowX: "auto", border: `1px solid ${DIVIDER}` }}>
        <table style={{ borderCollapse: "collapse", width: "100%", minWidth: 900 }}>
          <thead>
            <tr>
              <th style={{ ...firstColStyle, background: ROW_HOVER, zIndex: 1 }}>Student Name</th>
              {gradeCols.map((c) => (
                <th
                  key={c.name}
                  style={{
                    padding: "8px 12px",
                    border: cellBorder,
                    background: ROW_HOVER,
                    minWidth: 120,
                    textAlign: "left",
                    verticalAlign: "top",
                  }}
                >
                  <div style={{ fontWeight: 700, color: TEXT }}>{c.name}</div>
                  <div style={{ color: MUTED, fontWeight: 400, fontSize: 12 }}>{c.out}</div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {gradeRows.map((r) => (
              <tr key={r.student}>
                <td style={firstColStyle}>
                  <a href="#" style={{ ...linkStyle, fontWeight: 600 }}>{r.student}</a>
                </td>
                {r.scores.map((s, i) => (
                  <td
                    key={gradeCols[i].name}
                    style={{
                      padding: "10px 12px",
                      border: cellBorder,
                      color: s === "—" ? MUTED : TEXT,
                      textAlign: "right",
                    }}
                  >
                    {s}
                  </td>
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
function Discussions() {
  const threads: Array<[string, string]> = [
    ["Two's complement intuition?", "8 replies"],
    ["Why does carry propagate left?", "5 replies"],
    ["Study group for the midterm", "12 replies"],
  ];
  return (
    <>
      <h1 style={h1Style}>Discussions</h1>
      <div style={{ borderTop: `1px solid ${DIVIDER}` }}>
        {threads.map(([topic, activity]) => (
          <div
            key={topic}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "14px 0",
              borderBottom: `1px solid ${DIVIDER}`,
            }}
          >
            <a href="#" style={{ ...linkStyle, fontWeight: 600 }}>{topic}</a>
            <span style={{ color: MUTED, fontSize: 13 }}>{activity}</span>
          </div>
        ))}
      </div>
    </>
  );
}

// ---- Modules ---------------------------------------------------------------
function Modules() {
  const mods: Array<[string, string[]]> = [
    ["Week 1 · Number systems", ["Reading: binary & hex", "A01 — Number representation"]],
    ["Week 2 · Binary arithmetic", ["Reading: two's complement", "Quiz 1"]],
    ["Week 3 · Boolean logic", ["Reading: truth tables", "A02 — Boolean logic"]],
  ];
  return (
    <>
      <h1 style={h1Style}>Modules</h1>
      <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        {mods.map(([title, items]) => (
          <div key={title} style={{ border: `1px solid ${DIVIDER}`, borderRadius: 4 }}>
            <div
              style={{
                background: ROW_HOVER,
                padding: "10px 14px",
                fontWeight: 700,
                color: TEXT,
                borderBottom: `1px solid ${DIVIDER}`,
              }}
            >
              {title}
            </div>
            <ul style={{ margin: 0, padding: "10px 14px 10px 30px", color: TEXT }}>
              {items.map((i) => (
                <li key={i} style={{ padding: "4px 0" }}>
                  <a href="#" style={linkStyle}>{i}</a>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </>
  );
}
