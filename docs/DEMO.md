# Live demo — how it works, and a real-LMS demo later

## What's live now: the simulated-LMS demo (`/demo`)

The marketing site's **Try the live demo** button (and the per-LMS chooser next to it) opens
`https://<app-host>/demo`, where a visitor picks **Canvas, Blackboard, Moodle, or Brightspace** and
a role (**student** or **instructor**). The page renders the **real, interactive LMS Bridge tool**
inside a faithful frame of the chosen LMS — exactly what an LTI launch shows, since the LMS only
provides the surrounding chrome and the tool runs in its content area.

- No login: `POST /api/v1/auth/demo-login` signs the visitor in as the seeded demo student or
  instructor (password-less). It only ever returns those demo accounts and can be turned off with
  `DEMO_LOGIN_ENABLED=false` on a real institutional deployment.
- The tutoring, dashboards, mastery, and analytics are genuinely live. With `LLM_PROVIDER=mock`
  (the free default) it costs nothing and is deterministic; point it at a real key for live AI.
- Honest framing: the page label says *"Simulated <LMS> frame — the tool inside is the real LMS
  Bridge."* It is **not** a real Canvas/Blackboard instance (Blackboard and Brightspace cannot be
  self-hosted at all).

This covers all four LMSs and needs zero extra infrastructure.

## Later: a real end-to-end LTI demo (Canvas or Moodle only)

For a true "launch from inside a real LMS" demo, only the **open-source** LMSs are possible
(Blackboard and Brightspace are closed — no public demo instance exists). Steps:

1. **Stand up a test LMS instance.**
   - **Canvas:** a free **Canvas trial** (admin access — needed for LTI 1.3 Developer Keys), or the
     open-source `instructure/canvas-lms` via Docker on a host that has Docker. *(Canvas
     Free-for-Teacher does not give the admin Developer-Key access LTI 1.3 needs.)*
   - **Moodle:** a **MoodleCloud** trial, or `bitnami/moodle` via Docker — both give you admin.
2. **Register LMS Bridge** in that LMS using [`INSTALL_LTI.md`](INSTALL_LTI.md) (dynamic registration
   is one click in both Canvas and Moodle: paste `https://<app-host>/api/v1/lti/register`).
3. **Create a demo course** and a demo student + instructor enrollment; run a sync (or upload a
   couple of assessments) so there's mastery + remediation to show.
4. **Link it from marketing:** add a "Try it in real Canvas" button pointing at the course/tool
   launch URL of that instance.

Keep this instance behind a known demo login and reset its data periodically. It's real
infrastructure to maintain, which is why the simulated demo above is the default for everyone.
