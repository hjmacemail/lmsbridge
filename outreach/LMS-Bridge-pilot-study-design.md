# LMS Bridge — lightweight pilot study design

**Goal:** generate credible, competition- and publication-grade evidence that AI-guided remediation
improves foundational concept mastery — using a design one instructor can run in a single course,
with data Sage already captures.

> Targeted at the next **Learning Engineering Tools Competition** cycle (and a short paper at
> SIGCSE / Learning @ Scale / ASEE). These reward *evidence of learning impact* — what works, for
> whom, under what conditions — not just a working product. This design is built to produce exactly
> that.

---

## 1. Research questions

- **RQ1 (efficacy):** Does just-in-time, AI-guided remediation (retrieval practice + Socratic
  scaffolding) increase students' mastery of a foundational concept, compared with business-as-usual
  on a matched concept?
- **RQ2 (for whom):** Is the effect larger for students who started the term lower-performing
  (i.e. does it narrow the gap)?
- **RQ3 (engagement):** How much of the remediation do students actually complete, and does
  completion predict mastery gain?

RQ1 is the headline. RQ2 (equity) and RQ3 (dosage) are what make an entry stand out, and Sage
already logs the data for both.

---

## 2. Design — within-student concept-level randomization (the key idea)

A separate control *section* is hard to run solo and confounds easily. Instead, **randomize at the
concept level within one course**, so each student is their own control.

1. Identify the term's foundational concepts (e.g. 10–16: binary arithmetic, inheritance,
   recursion, probability, …).
2. Randomly split them into two matched sets, **A** and **B** (stratify by expected difficulty so
   the sets are comparable).
3. For the first half of the term, **remediation is ON for set A, OFF for set B**; switch halfway
   (**crossover**), so every concept gets the treatment in some window and every student
   experiences both conditions. (Crossover also means no student is denied the tool overall — an
   ethics plus.)
4. "OFF" = the normal course experience (existing resources, no Sage module). "ON" = when a student
   misses the concept on a formative quiz, Sage auto-delivers its guided remediation module.

**Why this is strong yet cheap:** within-student randomization controls for student ability,
motivation, and course/instructor effects — the usual confounders — so you get clean internal
validity with a modest sample (one class). It is the same logic that makes A/B tests credible.

**Minimum viable version (if randomization isn't feasible):** a **stepped-wedge** rollout — turn
remediation on for the whole class after week N, and compare each concept's re-assessment gain
before vs after rollout. Weaker, but still defensible and trivial to run.

---

## 3. Measures

**Primary (RQ1):** change in concept-level mastery from first attempt to re-assessment — Sage's
`at-risk → developing → mastered` states plus the raw re-attempt quiz score. Compare ON vs OFF
concepts.

**Secondary:**
- *Equity (RQ2):* effect split by students' baseline tertile (from an early diagnostic / first
  quiz).
- *Engagement / dosage (RQ3):* remediation modules started and completed, time spent, attempts —
  all already logged. Test whether completion predicts gain.
- *Perception:* a short (5-item) student survey and a brief instructor reflection.

**What to add to the product (small):** make sure each remediation event and re-assessment is
timestamped and concept-tagged in the export. The existing `grades.csv` export plus the analytics
endpoints cover most of this; add an event-level export if not already present.

---

## 4. Participants & scale

- **Minimum:** 1 instructor, 1 introductory STEM course, ~40–80 students, one term (or a focused
  4–6 week module).
- **Stronger:** 2–3 courses/instructors (adds replicability — a criterion judges reward).
- No separate control group needed (the within-student design supplies the comparison).

A rough power note: within-student designs detect moderate effects with ~40–50 students across
~10 concepts. More concepts and students = more statistical power; recruit what you can.

---

## 5. Procedure & timeline (maps to the next competition cycle)

| Phase | Weeks | Activity |
| --- | --- | --- |
| Setup | 0–2 | IRB determination (below); build the course in Sage; author quizzes tagged to concepts; randomize concepts into A/B; baseline diagnostic. |
| Run – period 1 | 3 to mid | Remediation ON for set A, OFF for set B. Quizzes → auto-remediation → re-assessment. |
| Crossover | mid | Switch: ON for B, OFF for A. |
| Run – period 2 | mid–end | Continue; collect surveys near the end. |
| Analysis | +1–3 | Export data, run analysis, write up. |
| Submit | fall | Tools Competition abstract (Catalyst tier) + short paper. |

Running this through a fall or spring term lines the results up with the next Tools Competition
window — which is why the now-closed 2026 deadline is not a loss.

---

## 6. Analysis plan

- **Primary:** mixed-effects model of mastery gain with a fixed effect for condition (ON/OFF) and
  random effects for student and concept. (Equivalently, a paired comparison of each student's
  average gain on ON vs OFF concepts.) Report effect size (Cohen's d / odds ratio) and CI, not just
  a p-value — competitions and reviewers care about magnitude.
- **RQ2:** add a condition × baseline-tertile interaction.
- **RQ3:** regress mastery gain on remediation completion (dosage–response).
- Pre-register the primary analysis (even a short OSF entry) before data collection — it materially
  strengthens credibility.

---

## 7. Ethics / IRB

- File for **IRB determination at NYU** before starting. Education research using normal
  instructional practice and de-identified records is commonly **exempt**, but get the
  determination in writing — competitions and journals will ask.
- Crossover design means no student is denied the intervention overall.
- Consent for use of data; analyze de-identified data; FERPA-aligned handling (the platform is
  built for this).

---

## 8. What to report (mapped to what judges/reviewers want)

- **Impact:** the effect size on concept mastery, with CIs.
- **For whom:** the equity result (does it help lower-performing students more?).
- **Mechanism/dosage:** engagement → outcome link.
- **Replicability:** that it ran across courses/instructors with minimal setup; open-source so
  others can reproduce it.
- **Cost & scalability:** near-zero marginal cost, BYO-key, no IT — a strong differentiator.
- A short anonymized **dataset + the analysis code**, published — this directly fits the
  competition's "learning engineering / open data" ethos.

---

## 9. Deliverables this produces

1. A results report (the evidence core of a Tools Competition entry).
2. A short paper for SIGCSE / L@S / ASEE.
3. An anonymized dataset + analysis notebook.
4. A reusable pilot playbook other instructors (or TYAN members) can follow.

These four assets are reusable across *every* funding, prize, and adoption conversation — they are
the single highest-leverage thing to build next.
