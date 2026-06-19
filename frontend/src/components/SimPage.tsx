import type { LmsId, LmsPage } from "./LmsFrame";

// Plausible, static "LMS content" pages for the demo, so a visitor can click around the
// simulated LMS. The only real, interactive page is the tool (rendered by DemoPage).
export default function SimPage(
  { page, lms, toolHref }: { page: LmsPage; lms: LmsId; toolHref: string },
) {
  const vendor = lms.charAt(0).toUpperCase() + lms.slice(1);
  return (
    <div className="container" style={{ paddingTop: 18 }}>
      <div className="card" style={{ background: "var(--soft)", marginBottom: 16, fontSize: 13 }}>
        <span className="muted">
          Simulated {vendor} page — example content, part of the demo. The real, interactive
          piece is <a href={toolHref}>LMS Bridge</a>.
        </span>
      </div>
      {render(page, toolHref)}
    </div>
  );
}

function render(page: LmsPage, toolHref: string) {
  switch (page) {
    case "assignments": return <Assignments />;
    case "grades": return <Grades />;
    case "people": return <People />;
    case "announcements": return <Announcements />;
    case "discussions": return <Discussions />;
    case "modules": return <Modules />;
    default: return <Home toolHref={toolHref} />;
  }
}

function Home({ toolHref }: { toolHref: string }) {
  return (
    <>
      <h1>CS 101 — Intro to Computer Science</h1>
      <p className="muted">Welcome to the course. Use the menu to reach assignments, grades, and
      your learning support.</p>
      <div className="card" style={{ borderLeft: "4px solid var(--primary)", marginTop: 14 }}>
        <h3 style={{ marginTop: 0 }}>Your instructor added LMS Bridge</h3>
        <p className="muted" style={{ fontSize: 14 }}>
          Personalized, just-in-time tutoring based on your assessment results. Open it to see your
          recommended practice.
        </p>
        <a className="btn" href={toolHref}>Open LMS Bridge</a>
      </div>
      <h2 style={{ marginTop: 26 }}>Latest announcements</h2>
      <div className="card"><strong>Midterm next week</strong>
        <p className="muted" style={{ fontSize: 14, margin: "6px 0 0" }}>
          Covers number systems through Boolean logic. Review the practice set.</p></div>
    </>
  );
}

function Assignments() {
  const rows = [
    ["A01 — Number representation", "Sep 12", "100", "Graded"],
    ["Quiz 1 — Binary arithmetic", "Sep 19", "20", "Graded"],
    ["A02 — Boolean logic", "Sep 26", "100", "Submitted"],
    ["A03 — Logic gates", "Oct 3", "100", "Upcoming"],
    ["Midterm exam", "Oct 10", "100", "Upcoming"],
  ];
  return (
    <>
      <h1>Assignments</h1>
      <div className="card" style={{ padding: 0 }}>
        <table>
          <thead><tr><th>Name</th><th>Due</th><th>Points</th><th>Status</th></tr></thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r[0]}><td>{r[0]}</td><td>{r[1]}</td><td>{r[2]}</td>
                <td><span className={`pill ${r[3] === "Graded" ? "mastered"
                  : r[3] === "Submitted" ? "developing" : "at_risk"}`}>{r[3]}</span></td></tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

function Grades() {
  const rows = [
    ["A01 — Number representation", "92 / 100"],
    ["Quiz 1 — Binary arithmetic", "13 / 20"],
    ["A02 — Boolean logic", "—"],
  ];
  return (
    <>
      <h1>Grades</h1>
      <p className="muted" style={{ fontSize: 13 }}>Official grades are set by your instructor.
      (LMS Bridge mastery indicators are a separate, private learning aid — not a grade.)</p>
      <div className="card" style={{ padding: 0 }}>
        <table>
          <thead><tr><th>Item</th><th>Score</th></tr></thead>
          <tbody>{rows.map((r) => <tr key={r[0]}><td>{r[0]}</td><td>{r[1]}</td></tr>)}</tbody>
        </table>
      </div>
    </>
  );
}

function People() {
  const people = [
    ["Dr. Alex Rivera", "Teacher"], ["Sam Lee", "Student"], ["Ava Chen", "Student"],
    ["Jordan Diaz", "Student"], ["Priya Patel", "Student"],
  ];
  return (
    <>
      <h1>People</h1>
      <div className="card" style={{ padding: 0 }}>
        <table>
          <thead><tr><th>Name</th><th>Role</th></tr></thead>
          <tbody>{people.map((p) => <tr key={p[0]}><td>{p[0]}</td><td>{p[1]}</td></tr>)}</tbody>
        </table>
      </div>
    </>
  );
}

function Announcements() {
  const items = [
    ["Midterm next week", "Covers number systems through Boolean logic. Review the practice set."],
    ["Office hours moved", "This week only: Thursday 2–4pm in Room 214."],
    ["Welcome to CS 101", "Read the syllabus and complete the intro survey by Friday."],
  ];
  return (
    <>
      <h1>Announcements</h1>
      <div className="stack" style={{ gap: 12 }}>
        {items.map((a) => (
          <div className="card" key={a[0]}><strong>{a[0]}</strong>
            <p className="muted" style={{ fontSize: 14, margin: "6px 0 0" }}>{a[1]}</p></div>
        ))}
      </div>
    </>
  );
}

function Discussions() {
  const threads = [
    ["Two's complement intuition?", "8 replies"],
    ["Why does carry propagate left?", "5 replies"],
    ["Study group for the midterm", "12 replies"],
  ];
  return (
    <>
      <h1>Discussions</h1>
      <div className="card" style={{ padding: 0 }}>
        <table>
          <thead><tr><th>Topic</th><th>Activity</th></tr></thead>
          <tbody>{threads.map((t) => <tr key={t[0]}><td>{t[0]}</td><td className="muted">{t[1]}</td></tr>)}</tbody>
        </table>
      </div>
    </>
  );
}

function Modules() {
  const mods = [
    ["Week 1 · Number systems", ["Reading: binary & hex", "A01 — Number representation"]],
    ["Week 2 · Binary arithmetic", ["Reading: two's complement", "Quiz 1"]],
    ["Week 3 · Boolean logic", ["Reading: truth tables", "A02 — Boolean logic"]],
  ];
  return (
    <>
      <h1>Modules</h1>
      <div className="stack" style={{ gap: 14 }}>
        {mods.map((m) => (
          <div className="card" key={m[0] as string}>
            <h3 style={{ marginTop: 0 }}>{m[0]}</h3>
            <ul style={{ margin: 0, color: "var(--muted)", fontSize: 14 }}>
              {(m[1] as string[]).map((i) => <li key={i}>{i}</li>)}
            </ul>
          </div>
        ))}
      </div>
    </>
  );
}
