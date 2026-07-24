# LMS Bridge — demo reel script &amp; shot list

A ~2-minute, auto-playing walkthrough. The player is `index.html`; it plays 14 scenes
(11 of them are your real screenshots, 3 are branded title/closing/privacy cards).

## How to use it

1. **Add your screenshots.** Capture the 11 screens listed below and drop them into the
   `shots/` folder using the exact filenames. Any slot without an image shows a labeled
   placeholder, so you can preview the flow before you have every shot.
2. **Open `index.html`** in a browser (double-click it).
3. Press **F** for fullscreen, then **P** for present mode (hides the controls).
4. **Screen-record** it to get an MP4 — QuickTime (⌘⇧5 on Mac) or OBS. It auto-plays and
   loops; record one clean pass (~2 min). Add the voiceover below live or in post.
   - Controls while previewing: **Space** play/pause · **← →** navigate · click the dots to jump.

**Tip for crisp screenshots:** capture at 1600×900 (16:9) or a maximized browser window so
they fill the 16:9 frame without letterboxing.

---

## Shot list &amp; narration

Total runtime ≈ 2:06. Each screenshot appears inside a subtle browser frame with a caption.

| # | Screenshot file | What to capture | On-screen caption | Voiceover |
|---|----------------|-----------------|-------------------|-----------|
| 1 | *(title card)* | — | LMS Bridge — AI tutoring built into your LMS | "Every LMS can tell you who's failing. LMS Bridge tells you *why* — and does something about it." |
| 2 | `01-problem.png` | The landing‑page hero ("Your LMS tells you who failed…") **or** a Canvas gradebook with a low score | Your LMS tells you **who** failed | "In cumulative subjects, one early gap quietly compounds into later failure. By the time it shows up in grades, it's too late." |
| 3 | `02-launch-in-lms.png` | The demo's simulated **Canvas** course with **LMS Bridge** in the left nav (Insights & remediation) | Launches right inside the course | "LMS Bridge lives *inside* your LMS. Students open it from Canvas, Moodle, Blackboard, or Brightspace — single sign-on, no new account." |
| 4 | `03-quiz-result.png` | A **quiz result** screen (e.g. the student "Quiz results — 58%" view) | A quiz comes back low | "The moment a quiz is submitted, LMS Bridge reads the results — question by question." |
| 5 | `04-needs-review.png` | The student **"Needs review" / "Why you're seeing this"** card | LMS Bridge finds the **root cause** | "It maps the wrong answers to concepts, pinpoints the misconception, and builds a short, targeted practice session — automatically." |
| 6 | `05-tutor-session.png` | The **AI tutor chat** session (goal banner + conversation) | A patient, one-on-one AI tutor | "Then it tutors. Grounded in the course, using retrieval practice and Socratic questioning — it guides the student to the answer instead of handing it over." |
| 7 | `06-tutor-check.png` | The tutor showing a **multiple-choice checkpoint** | Checks understanding as it goes | "Quick checks confirm the concept actually landed before the session wraps up." |
| 8 | `07-instructor-copilot.png` | The **instructor Overview** with the AI Copilot brief ("what to do before your next class") | An AI copilot, not just a dashboard | "For instructors, it's a copilot: the single highest-impact thing to review before the next class — grounded in real class data." |
| 9 | `08-analytics.png` | The **Analytics** screen (concept-mastery bars + practice-impact donut) | See exactly where the class is stuck | "Concept-level mastery, at-risk students, and practice impact — real numbers from real submissions." |
| 10 | `09-install-lti.png` | The landing‑page **Install** section (LTI URLs + steps) **or** the in‑app setup helper | A standard **LTI 1.3** tool | "Installing it is a one-time job: four copy-ready URLs, or one-click registration. Roster and grades sync on their own." |
| 11 | `10-sage.png` | The **Sage** overview/dashboard (standalone mini-LMS) | Sage — a standalone mini-LMS | "No LMS? Sage is a standalone mini-LMS with the same tutor built in. Make a course, share a code, and adaptive remediation just works." |
| 12 | `11-multilanguage.png` | Any screen in **Arabic (right-to-left)** — e.g. the tutor or student dashboard | Speaks your students' language | "It speaks English, Spanish, French, and Arabic — right-to-left included — across the whole platform and the tutor." |
| 13 | *(privacy card)* | — | Private by design, open by default | "It's FERPA-aware, runs on your own AI key, and it's open source — self-host the whole thing if you want." |
| 14 | *(closing card)* | — | Bridge early gaps before they widen — www.lmsbridge.app | "LMS Bridge. Bridge early gaps before they widen." |

---

## Where to grab each screenshot in your deployment

- **Canvas launch (02):** open the live demo (`/demo`), Student role — the simulated Canvas frame with LMS Bridge in the nav.
- **Quiz result (03), Needs review (04), Tutor (05, 06), Multi-language (12):** the demo Student view, or a Sage student account.
- **Copilot (07), Analytics (08):** the demo Instructor view, or a Sage instructor course → Overview / Analytics.
- **Install (09):** `www.lmsbridge.app/#install`.
- **Sage (11):** `app.lmsbridge.app/sage` (or your Sage URL), instructor overview.

Timings, captions, and order can all be tweaked in `index.html` (the `S = [...]` array near the
top of the script) — each scene has a `t` (seconds), `title`, `sub`, and `img`.
