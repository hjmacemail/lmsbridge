# LMS Bridge — LMS Integration & Sustainability Model

LMS Bridge is **free and open source (AGPL-3.0)**: any institution self-hosts it for free, using
its own AI key — no per-student fee, no paid tier required to run it. This document covers how the
LTI integration works (Part 1) and how the project sustains itself **without charging institutions
to use it** (Part 2). *Certification, marketplace, and compliance specifics should be confirmed
with 1EdTech and each LMS partner program before committing.*

---

## Part 1 — Making it a plug-in for any LMS

### The key idea: integrate once, run everywhere via LTI 1.3 / LTI Advantage

You do **not** build a separate connector for Blackboard, Brightspace, Canvas, Moodle, etc.
Instead you implement one open standard — **LTI 1.3 / LTI Advantage**, maintained by **1EdTech**
(formerly IMS Global). It is the universal "app store" protocol for the LMS world: Blackboard
(Anthology), Brightspace (D2L), Canvas (Instructure), Moodle, and Schoology all support LTI 1.3
Advantage, and LTI 1.1 is being deprecated. A tool that is LTI 1.3 Advantage–certified launches
inside any of these LMSs with no per-vendor code.

This fits the architecture you already have. The codebase deliberately hides the LMS behind one
interface (`BrightspaceAdapter` / the adapter factory). **LTI becomes "the real adapter"** that
sits beside the mock — the remediation engine, mastery model, tutor sessions, and UI don't change.

### The four LTI Advantage services you implement

| Standard | What it does for LMS Bridge |
|----------|------------------------------|
| **LTI 1.3 Core** (OIDC launch + signed JWT) | Single sign-on: a student or instructor clicks LMS Bridge inside a course and lands authenticated — no separate login. |
| **Deep Linking 2.0** | The instructor places LMS Bridge (the student tutor, or a per-topic remediation) into a course module from the LMS's "add content / add tool" menu. |
| **Assignment & Grade Services (AGS)** | Read assessment scores from the LMS gradebook, and optionally write back a **non-graded** "mastery/engagement" column. Reinforces the "mastery is not a grade" stance you already built in. |
| **Names & Role Provisioning Services (NRPS)** | Pull the roster and roles (who is a student vs. instructor) automatically, so no manual setup. |

Add **Caliper Analytics** (also 1EdTech) to receive a real-time event stream of learning activity
— the richest source for the adaptive signals you use.

### Handling the multiple-choice answer detail

AGS exposes **scores at the line-item level**, not per-question answers. For the
distractor-level misconception diagnosis that powers your remediation, use one of:

1. **Deliver the formative quizzes through LMS Bridge itself** (launched via LTI) — then you own
   the per-question responses natively. This is the cleanest path and the strongest data.
2. **Caliper events** where the LMS emits per-item interaction data.
3. **Vendor REST APIs as a supplement** (Brightspace Valence, Canvas API, Blackboard REST) for
   quiz attempt detail — your existing adapter pattern already anticipates this.

### What you'd add to the current system

- **An LTI tool-provider service**: OIDC login + launch endpoints, JWT signing, a **JWKS** key
  endpoint, and a **platform registration store** (each institution registers as a "platform"
  with its issuer, `client_id`, `deployment_id`, and keys).
- **Multi-tenancy**: one deployment serving many institutions, each isolated. Add a
  `Platform`/`Registration` table; scope all data by tenant. Your config already supports
  per-tenant LLM endpoints (e.g., the institution's own Azure OpenAI) for data governance.
- **Embedded UI modes**: the student tutor session and instructor console render inside the LMS
  iframe; SSO via LTI means there's no second password.
- **Scale-out**: move AI calls (session turns, generation, recompute) onto a job queue and keep
  the provider abstraction so inference can run on institution-approved infrastructure.

Good news: roughly 80% of this is the LTI provider plumbing; the pedagogy, mastery model, tutor
engine, and analytics you've already built are unchanged.

### Distribution & compliance (the real gatekeepers for institutional sales)

- **Certify**: join the **1EdTech Alliance**, pass **LTI Advantage certification**, and list in
  the **TrustEd Apps Directory** (the recognized catalog of vetted tools).
- **List in each LMS's partner marketplace**: Anthology/Blackboard, D2L/Brightspace, and
  Instructure/Canvas all run partner programs and in-product app catalogs.
- **Clear the procurement checklist**: **FERPA** alignment, a **data-privacy** posture (1EdTech
  also offers a TrustEd Apps Data Privacy rubric), **SOC 2**, and **accessibility (WCAG / VPAT)**.
  These are non-negotiable gates for university buyers and are worth building toward early.

---

## Part 2 — How the project sustains itself (without charging to use it)

LMS Bridge is **free to download, self-host, and use at any size** (AGPL-3.0). There is no
per-student fee and no paid tier required to run it. Because each institution brings **its own AI
key**, your marginal cost to let them use it is ~zero. Sustainability comes from *optional*
services and non-dilutive funding layered on top of the free software:

1. **Grants & research funding (primary).** The open-source + higher-ed-STEM profile fits
   **NLnet NGI Zero**, **NSF IUSE: EDU** (via a faculty PI), the **Learning Engineering Tools
   Competition**, and AI/cloud **researcher credit programs**. Published efficacy evidence from
   pilots is the engine. See [`COST_AND_FUNDING.md`](COST_AND_FUNDING.md) for the full shortlist.
2. **Donations / sponsorship.** Individuals who value the project can sponsor it via **GitHub
   Sponsors** or **Open Collective** (a fiscal host handles the legal/tax wrapper — no company
   needed). Institutions generally *can't* donate easily; for them, see commercial support below.
3. **Optional commercial support & managed hosting.** Institutions that want an SLA, managed
   hosting, onboarding, or help clearing security/accessibility review (HECVAT/VPAT/DPA) can pay
   for **services** — on top of the free software. This is the procurement-friendly way an
   institution "pays" (an invoice for support, not a license-to-use fee).
4. **Optional commercial / OEM license (dual licensing).** Anyone who wants to build a proprietary
   product on top *without* AGPL's share-back terms can buy a separate license. AGPL preserves this
   path for you while keeping the tool free for ordinary self-hosters. See
   [`../COMMERCIAL.md`](../COMMERCIAL.md).

**What this is _not_:** no per-student courseware fee, no "pay if you're over N students" gate, and
nothing blocks a self-hoster's students. The subscription/seat/signed-license mechanisms exist in
the code only for an *optional* `hosted` (multi-tenant SaaS) deployment that most institutions will
never use — see [`LICENSING.md`](LICENSING.md).

### Why it gets adopted (the moat)

Pedagogically constrained (won't do the student's work — *not* a cheating tool), misconception-level
diagnosis from the actual wrong answers, grounding in the instructor's own materials, LMS-native
(frictionless via LTI), and **privacy-first** (self-hosted, bring-your-own-key, FERPA-friendly).
Being **free and open source** is itself a major adoption and procurement advantage — institutions
can read the code, run it in their own boundary, and avoid vendor lock-in. These are exactly the
things procurement offices and faculty senates screen for.

### Adoption sequence (not a sales funnel)

1. **Pilot at your own institution** (the NYU deployment), instrumented for outcomes.
2. **Measure efficacy** — mastery gains, DFW-rate change, engagement — and **publish**.
3. **Make it trivially easy for a peer department to self-host** (great docs, one-command install),
   and **certify + list** in the 1EdTech TrustEd Apps Directory and LMS app catalogs for credibility.
4. **Offer optional support/hosting** to institutions that want a hand — funding the project while
   keeping the software free.

---

## One-paragraph summary

Implement **LTI 1.3 / LTI Advantage** once (Core launch + Deep Linking + AGS + NRPS, optionally
Caliper) and LMS Bridge installs into Blackboard, Brightspace, Canvas, Moodle, and more from a
single codebase. It is **free and open source (AGPL-3.0)**: institutions **self-host it for free**
with **their own AI key**, so there's no per-student fee and nothing to meter. The project sustains
itself through **grants/research funding**, **donations/sponsorship**, and **optional** commercial
**support, managed hosting, and OEM/dual licensing** — layered on top of the free software, never
gating ordinary use. Get **1EdTech-certified**, list in the **TrustEd Apps Directory** and LMS
catalogs, and clear **FERPA / accessibility (VPAT) / security (HECVAT)** so the free tool is easy to
adopt — converting published efficacy evidence into adoption rather than sales.

---

### Sources

- [1EdTech — LTI Advantage final release & market adoption](https://www.1edtech.org/article/1edtech-consortium-announces-final-release-and-market-adoption-next-generation-learning)
- [1EdTech — first solutions to achieve LTI Advantage certification](https://www.1edtech.org/article/1edtech-consortium-announces-first-edtech-solutions-achieve-lti-advantage-certification)
- [1EdTech — Procure Certified Products / TrustEd Apps](https://www.1edtech.org/certification/procure-certified)
- [1EdTech — Learning Tools & Content Alliance (LTI)](https://www.1edtech.org/about/membership/alliance/lti)
- [CompTIA — Why move from LTI 1.1 to 1.3 with Advantage (LMS support + 1.1 deprecation)](https://help.comptia.org/hc/en-us/articles/29155702699156-Why-is-CompTIA-Moving-from-LTI-1-1-to-1-3-with-Advantage)
- [Microsoft 365 LTI — supported LMS platforms (Canvas, Schoology, Blackboard, Brightspace, Moodle)](https://techcommunity.microsoft.com/blog/educationblog/microsoft-365-lti-is-now-generally-available/4453739)
- [Monetizely — EdTech pricing models](https://www.getmonetizely.com/articles/edtech-pricing-models-monetizing-education-technology-effectively)
- [Monetizely — How much should AI education agents cost](https://www.getmonetizely.com/articles/how-much-should-ai-education-agents-cost-a-pricing-guide-for-learning-platforms)
- [EdTech Global Market Forecast Report 2025](https://www.globenewswire.com/fr/news-release/2025/08/21/3136953/28124/en/EdTech-Global-Market-Forecast-Report-2025.html)
