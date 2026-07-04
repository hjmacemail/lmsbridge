# LMS Bridge — NYU Entrepreneurs Challenge pitch kit

**Track:** Technology Venture
**Founder:** Hasan Aljabbouli (NYU)
**One-liner:** LMS Bridge turns the assessment data universities already collect into just-in-time,
AI-guided tutoring that catches struggling STEM students *before* they fail — open-source, works
inside any LMS, and privacy-first.

---

## 0. The venture-model decision (why open-core + hosted)

You asked me to pick the model. **Lead with open-core + managed hosting.** Here's the reasoning,
briefly, so you can defend it on stage:

- **Social enterprise / nonprofit** tells a beautiful impact story but reads as a *grant project*,
  not a venture — judges in a startup competition discount it on "is this fundable / scalable?"
- **Services & support** is real revenue but caps low and doesn't scale (it sells your time).
- **Open-core + hosted** is the proven path for open-source companies (GitLab, Sentry, Discourse,
  Moodle): the software stays free and open — which *is* your trust, adoption, and mission engine —
  while revenue comes from an optional **managed, hosted version** institutions pay for so they
  don't have to run or secure it themselves, plus institution-grade add-ons (SSO, admin analytics,
  SLAs, priority support). It scales, it's defensible, and it doesn't betray the open ethos.

So the pitch is: **free and open for anyone who self-hosts; paid when an institution wants it run
for them.** The mission (equity, access, the Global South) becomes your "why," not your business
model. That's the framing that scores in *both* the venture and the impact dimensions.

---

## 1. Problem

In cumulative STEM subjects, a small misunderstanding in week 3 (binary representation, inheritance,
probability) quietly compounds and sinks the student in week 9. Large gateway courses make
individual, concept-level feedback impossible to deliver in time, so students who slip early rarely
recover.

The damage is concrete and well documented:

- Gateway STEM courses are notorious for high **DFW rates** (drop/fail/withdraw) — over **a quarter**
  of students DFW introductory chemistry, and just **1% of courses generate roughly a third** of all
  unproductive credits.
- Much of STEM degree attrition happens *inside* these intro courses, and it falls hardest on
  underrepresented students — these courses literally "push out" URM students.
- Every DFW is lost tuition, hurt retention metrics, jeopardized financial aid, and a widened equity
  gap — a problem universities spend real money trying to fix (learning assistants, tutoring,
  supplemental instruction), with proven but **labor-intensive, unscalable** solutions.

Meanwhile the LMS (Canvas, Moodle, Brightspace, Blackboard) already captures every quiz and
assignment result — but that data sits retrospective and unused. **The intervention never happens at
the moment it would matter.**

## 2. Solution

**LMS Bridge** is an AI-guided adaptive-remediation layer that converts assessment data into
immediate, personalized tutoring. When a student misses a concept, LMS Bridge detects the likely
misconception and delivers a short, **pedagogically constrained** tutoring session — retrieval
practice, Socratic questioning, mastery progression. It *diagnoses and guides; it never hands over
the answer.*

Two deployment modes kill adoption friction:

- **Inside the existing LMS** via LTI 1.3 / Advantage — one registration, works in Canvas, Moodle,
  Brightspace, Blackboard; syncs roster and grades automatically.
- **Standalone (Sage)** — a no-IT mini-LMS where an instructor shares a join code and starts in
  minutes. This is the wedge: a single professor can adopt it with zero institutional approval.

## 3. How it works (and the demo beat)

1. **Detect** — student misses "inheritance" on a formative quiz; the system flags the concept-level
   gap.
2. **Remediate** — it auto-launches a guided session: a Socratic prompt, a retrieval-practice
   question, a worked correction — active, not passive.
3. **Master** — the student re-attempts and recovers; the instructor's dashboard shows who was
   at-risk and who bounced back.

The "aha" is the 60-second loop: *miss → guided recovery → mastery → instructor sees it,* all
automatic, all inside the course they already use.

## 4. Why now

- **LLMs** make per-student, concept-level tutoring affordable at scale for the first time.
- **LTI 1.3** is now the universal standard — one integration reaches every major LMS.
- **Post-pandemic retention & equity pressure** plus tight budgets have universities actively
  hunting for scalable student-success tools.
- The **adaptive-learning market** is ~$1.4–3B in 2026 and growing ~17–20%/yr toward ~$12B by 2035,
  inside a ~$30B LMS market — a fast-moving wave with budget attached.

## 5. Differentiators / moat

- **Pedagogically constrained, not a chatbot.** It won't do the homework — which is exactly what
  makes faculty trust it and adopt it. This is a product *and* positioning moat against
  "just use ChatGPT."
- **Privacy-first & self-hostable.** Bring-your-own AI key, FERPA-aware, no telemetry. This dissolves
  the single biggest institutional blocker to AI adoption (student data + AI vendors).
- **Any-LMS *and* standalone.** Competitors are locked to one platform or require IT projects; we
  meet schools where they are and also bypass IT entirely via Sage.
- **Open-source.** Trust, no lock-in, auditability, and a contributor community — a credibility and
  distribution advantage closed competitors can't copy.
- **Built for reach.** Multilingual + RTL, low-resource friendly — opens the Global South and ESL
  markets others ignore.

## 6. Market (TAM / SAM / SOM — framework; validate the exact figures)

- **TAM:** the global adaptive-learning software market (~$1.4–3B in 2026 → ~$12B by 2035), sitting
  inside the ~$30B LMS market.
- **SAM:** higher-ed STEM gateway courses in LTI-1.3 institutions — thousands of universities, each
  with dozens of high-DFW courses and hundreds–thousands of at-risk students per term.
- **SOM (beachhead):** intro CS / data-science / quantitative courses at US R1s and their peers —
  the founder's domain, where the pain and the willingness to experiment are highest. Land a handful
  of departments via faculty, expand to site licenses.

> Note for the deck: present these as a labeled funnel with one bottom-up sanity check (e.g.
> "$X per student/term × at-risk students in our beachhead = $Y"), and flag the per-institution
> figures as estimates to validate during the pilot.

## 7. Business model

- **Free forever:** self-hosted open-source (drives adoption, trust, pilots, community).
- **LMS Bridge Cloud (paid):** managed, secured, auto-updated hosting for departments/institutions
  that don't want to run it — priced per active student/term or as a department/site license.
- **Institution add-ons:** SSO/SAML, admin analytics, content libraries, SLAs, priority support.
- **Services:** onboarding, training, custom LMS/integration work.

Land-and-expand: free Sage with one professor → paid department pilot → institution-wide contract.
AI inference is bring-your-own-key (cost passes through), keeping our gross margins software-like.

## 8. Go-to-market

- **Bottom-up, product-led:** a single instructor adopts Sage free, with no approval needed — the
  zero-friction wedge.
- **Faculty → admin:** convert enthusiastic faculty into internal champions (we've built an
  advocacy kit and a one-click "connect your LMS" admin flow) to reach the institutional buyer.
- **Pilot → evidence → contract:** small pilots produce outcome data that justify paid site
  licenses and anchor case studies.
- **Beachhead:** NYU + peer institutions' intro CS/data courses, then expand by discipline and
  campus.

## 9. Traction & status (honest)

- **Product:** a full, production-ready platform is **already built** — LTI 1.3/Advantage,
  multi-LMS roster/grade sync, the standalone Sage mini-LMS, a pedagogically constrained AI engine,
  multilingual/RTL UI, and security/compliance documentation. Open-source and deployable today.
- **Stage:** pre-pilot. **Next milestone:** design-partner pilots at NYU this coming term, producing
  the first concept-mastery outcome data.
- Framing: "We've de-risked *can we build it* — fully. The competition's funding and mentorship
  de-risk *will institutions adopt and pay,* which is exactly what the pilots will prove."

## 10. Competition

| | Closed adaptive platforms (ALEKS, Squirrel, etc.) | Generic AI chatbots (ChatGPT, Khanmigo) | LMS-native quiz tools | **LMS Bridge** |
|---|---|---|---|---|
| Works in *your* existing LMS | Sometimes | No | Yes | **Yes (any) + standalone** |
| Pedagogically constrained (won't give answers) | Partly | **No** | n/a | **Yes** |
| Privacy / self-hostable / FERPA | No | No | Varies | **Yes** |
| Open-source / no lock-in | No | No | No | **Yes** |
| Cost to adopt | High, per-seat | Low but unmanaged | Bundled | **Free core** |

The wedge: incumbents are expensive, closed, and content-locked; chatbots aren't trusted by faculty
because they do the work *for* students. We're the trusted, open, low-friction middle.

## 11. Team

- **Hasan Aljabbouli (NYU)** — founder; designed and built the full platform.
- **Honest gap & plan:** currently solo. Use the program to recruit a technical co-founder/engineer,
  a faculty pilot cohort (design partners), and an advisor in learning science. Naming this directly
  reads as self-aware, not weak — judges expect early teams to be forming.

## 12. The ask & use of funds

Seeking seed funding + mentorship to convert a finished product into proven, paying adoption:

- **Pilots:** run and instrument design-partner courses (incl. modest AI credits).
- **Team:** part-time engineer / co-founder; learning-science advisor.
- **Cloud:** stand up the managed hosting offering for the first paying departments.
- **Evidence & sales:** produce the outcome study + case studies that close institutional contracts.

**Milestone in one line:** "Fund the pilots; we return with mastery-gain data and our first paying
department." 

## 13. Vision

Every student in a hard, cumulative course gets a patient, private, always-available guide at the
exact moment they slip — regardless of class size, budget, or country. Start with STEM gateway
courses; expand across disciplines and into the under-served institutions that need it most.

---

## Appendix A — 90-second live demo script

1. *(5s)* "This is a real intro-CS quiz. Watch a student miss one concept — inheritance."
2. *(20s)* Submit a wrong answer. The system flags the concept gap and auto-opens a guided session.
3. *(25s)* Walk one Socratic prompt + one retrieval question. Point out: *"notice it never gives the
   answer — it makes the student reason. That's why faculty allow it."*
4. *(15s)* Student re-attempts, masters it.
5. *(15s)* Flip to the instructor dashboard: who was at risk, who recovered — class-wide, automatic.
6. *(10s)* "Same engine runs *inside* Canvas via one LTI registration, or standalone with a join
   code — no IT required. Free and open-source."

## Appendix B — judge Q&A prep (have crisp answers ready)

- **"How is a free product a business?"** Open-core: free to self-host, paid managed hosting +
  institutional add-ons. GitLab/Discourse model. Free is our distribution and trust engine.
- **"Isn't this just ChatGPT?"** No — it's constrained to diagnose and guide, never to answer, and
  it's wired into the LMS gradebook. That constraint is the whole reason faculty adopt it.
- **"What's the moat?"** Open-source trust + the privacy/self-host story + any-LMS-plus-standalone
  reach + faculty pedagogical trust + first-mover community. Hard for a closed vendor to copy without
  abandoning their model.
- **"Why won't Canvas/Google just build it?"** They optimize for the platform lock-in and won't go
  cross-LMS or open-source; and they're slow on the pedagogical-trust positioning. Our openness is
  precisely what they can't match.
- **"AI cost / unit economics?"** Bring-your-own-key passes inference cost to the institution;
  our margins stay software-like. Mock/non-AI modes keep entry cost near zero.
- **"Evidence it works?"** Not yet — that's what the pilots fund. The learning-science methods
  (retrieval practice, Socratic scaffolding, mastery) are themselves well-evidenced; we're testing
  *our* delivery of them. (See the pilot study design.)
- **"Biggest risk?"** Adoption/distribution and team depth — which is exactly what this program's
  funding, mentorship, and network address.
