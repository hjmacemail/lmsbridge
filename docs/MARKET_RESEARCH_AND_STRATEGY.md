# LMS Bridge — Market Research & Strategy

**Question:** Is there a marketplace where LTI tools are sold? Who are the competitors? How should LMS Bridge be positioned, packaged, and restructured?

**Short answer:** There is no "App Store" that *sells* LTI tools and closes deals for you. The LMS "marketplaces" are **discovery + install-enablement directories**; deals are won by **direct sales gated through institutional procurement**. The single most powerful distribution lever is being **written into procurement requirements** — i.e., certification and a clean security/accessibility review. The competitive field is crowded with *publisher courseware* (which replaces the textbook) and a fast-growing wave of *AI tutors*, but there's a real, defensible gap for a **lightweight, LMS-native, privacy-first, instructor-augmenting remediation layer that does not give answers**. That is precisely LMS Bridge — but it needs to be repackaged around **trust/compliance and pedagogy evidence**, not features.

> All figures below are sourced; market-size numbers are analyst estimates and are flagged. Citations are listed at the end.

> **Update (direction chosen):** after this analysis, LMS Bridge was set to ship **free and
> open-source under AGPL-3.0**, self-hosted by each institution with its own AI key (see
> [`../README.md`](../README.md), [`LICENSING.md`](LICENSING.md), [`COST_AND_FUNDING.md`](COST_AND_FUNDING.md)).
> The competitive positioning, procurement-gate, and pedagogy-evidence findings below still hold;
> the **pricing recommendation in §5 is superseded** — there is no per-student or institutional
> license fee. "Packaging/distribution" now means: free self-host, optional commercial
> support/hosting, and funding via grants + sponsorship rather than license sales.

---

## 1. Is there a marketplace? Distribution channels for LTI tools

There are four kinds of channel, and none of them is a transactional store:

**A. LMS vendor app directories (discovery + install).**
- **Canvas / Instructure — EduAppCenter** (free to list) is effectively an **LTI 1.1 catalog**; LTI 1.3 tools can be *shown* but must be installed by a Canvas admin via a Developer Key / Client ID, not self-installed by instructors. Canvas shipped a new "Discover" Apps UI in 2025. [C1][C2]
- **Anthology / Blackboard — App Catalog + Partner Directory.** Tiered partner program with **published pricing**: Community = free; **Developer Network = from $3,000/yr**; Bronze/Silver/Gold (marketing + events) are quote-based. [C3]
- **D2L Brightspace — IntegrationHub** (replaced the old App Finder). D2L is notably "the first LMS to offer **joint partner certification with 1EdTech**." Partner fees are not public. [C4]
- **Moodle — Plugins Directory** (free, community-reviewed; ~3-day manual review, most plugins bounce on first pass). Separately, a commercial **Certified Partner/Integration** track exists (revenue-share, community-estimated ~10%). [C5]

**B. Standards body — 1EdTech (formerly IMS Global).**
- **LTI Advantage certification** lists you in the **TrustEd Apps Directory**, "where institutions go first." Certification requires **1EdTech membership** (minimum the Learning Tools Alliance tier; dues are **not published** — "minimal, varies by revenue"), is **free per-product once you're a member**, and must be **re-certified annually**. [C6][C7]
- **TrustEd Apps data-privacy/security vetting** rates your public privacy policy/ToS against a rubric; HECVAT-adjacent trust signal. Certification is members-only. [C8]
- 1EdTech publishes **sample RFP language** telling institutions to *require* LTI Advantage certification in procurement — this is the real adoption mechanism. [C9]

**C. EdTech procurement/management platforms.**
- **LearnPlatform (owned by Instructure, acq. 2022)**: ~10,000+ app listings, but it's a **procurement/compliance/usage-analytics layer, marketed primarily to K-12** — not a higher-ed install store. **GG4L→SchoolDay** and **Clever** are essentially **K-12 SSO/rostering**; low higher-ed relevance. [C10][C11]

**D. Direct sales (the channel that actually closes).** Pilot with a department/instructor → prove outcomes → expand to a campus license, with IT security/accessibility review as the gate.

> **Takeaway:** "Getting listed" is necessary table-stakes credibility, not a growth engine. **Independent evidence that any directory *measurably* drives adoption vs. direct sales does not exist** — every "drives adoption" claim traces back to the channel operator's own marketing. Budget for direct/bottom-up sales and treat certification as a **procurement key**, not a storefront.

---

## 2. Competitive landscape

### 2a. Publisher courseware & adaptive platforms (the incumbents)

| Vendor | Model | LMS via LTI | STEM focus | Price (where public) |
|---|---|---|---|---|
| **ALEKS** (McGraw Hill) | Adaptive, **replaces the homework/practice layer**; Knowledge Space Theory | Yes (MH integration) | Math, Chemistry | Self-study $179.95/yr; institutional negotiated |
| **Knewton Alta** (Wiley) | **Replaces the textbook** (OER courseware) | Yes (Bb/D2L/Canvas/Moodle; cert lapsed) | Math, Stats, Chem | ~$50/sem (figures conflict) |
| **MindTap / WebAssign** (Cengage) | **Augments** (publisher bundle); WebAssign = STEM homework | Yes | WebAssign: math/physics/chem | Cengage Unlimited $124.99/4mo |
| **MyLab / Mastering** (Pearson) | **Augments** (publisher bundle) | **Yes — LTI 1.3 "Access Pearson", 6 LMSs, certified** | Mastering = science/eng | Negotiated / Inclusive Access |
| **Realizeit / Skillwell** | **Content-agnostic** adaptive engine — bring your own content | Yes (all LMSs) | Discipline-agnostic | Usage-based, custom |
| **CogBooks** (Cambridge, acq. 2021) | Adaptive courseware (replaces) | Unverified | Biology/STEM | Unverified |
| Smart Sparrow | Authoring tool — **defunct**, absorbed into Pearson ($25M, 2020) | — | — | — |
| Carnegie MATHia | Cognitive-tutor, **K-12** (not higher ed) | Listed, cert inactive | K-12 math | ~$35/student/yr (K-12) |

**Pattern:** the big money is **publisher courseware tied to content/textbook sales**. They want to *own the course materials*. Most charge a **per-student courseware fee ($35–$180/yr)** and are sold through the bookstore / Inclusive Access. The one model closest to LMS Bridge is **Realizeit** (content-agnostic engine), which validates "we don't sell content, we add a layer" — but Realizeit is enterprise/courseware-heavy and custom-priced, not lightweight or self-serve.

### 2b. AI-native tutors (the fast-moving wave)

- **Khanmigo (Khan Academy)** is the flagship "**Socratic, won't-give-the-answer**" tutor with content grounding and cheating guardrails — exactly LMS Bridge's pedagogy. Reporting notes the trade-off: the Socratic approach is "slower and sometimes frustrating" for answer-seeking students — a UX problem to design around. [C12]
- **Research-grade scaffolded CS tutors** (e.g., "SocraticAI", 2025) show query-validation + RAG course-grounding + usage limits moving students from vague help-seeking to problem decomposition — but on small pilots. [C13]
- The defining competitive threat is **build-your-own**: **Harvard** faculty built a course-tuned GPT tutor (engagement reportedly doubled) and Harvard/Stanford now run infrastructure (AI Sandbox, workshops) so any instructor can spin one up. **The easy 80% — "a chatbot that knows the syllabus" — is now a faculty weekend project.** [C14][C15]

> **Implication:** You don't win on "an AI tutor." You win on the things a DIY GPT can't do: **LTI 1.3 grade/roster integration, guardrails that hold at scale, mastery/retrieval instrumentation, FERPA-safe self-hosting, and cross-course analytics.** LMS Bridge already has these — that's the moat. Lead with it.

---

## 3. What buyers actually require (the real gates)

These are not "nice to have" — they are **pass/fail procurement gates** in US higher ed:

1. **Security review → HECVAT.** The Higher Education Community Vendor Assessment Toolkit (EDUCAUSE/Internet2/REN-ISAC) is the standard questionnaire. **HECVAT 4** consolidated Full/Lite/On-Premise into one workbook and **added dedicated AI + privacy questions**. Having a completed HECVAT is the artifact that lets security/IT/privacy/legal/procurement say yes. [C16][C17]
2. **Accessibility → VPAT/ACR + the ADA Title II web rule.** DOJ's 2024 rule makes **WCAG 2.1 AA mandatory** for public institutions' web content *and the third-party tools they license*. Deadlines (per the April 2026 extension): **April 26, 2027** (pop. 50k+) / **April 26, 2028** (smaller). A current **VPAT/ACR is increasingly required for any LTI tool.** [C18][C19]
3. **FERPA + a Data Processing Agreement.** The vendor must qualify as a "school official," use data **only** for the contracted purpose, **not train models on student data**, and support retention limits + deletion-on-request. Enterprise LLM tiers (Azure OpenAI / OpenAI enterprise with DPAs / Zero-Data-Retention) are what institutions demand for FERPA data. [C20][C21]
4. **SSO + gradebook.** SAML/InCommon federation institution-wide; **LTI 1.3 launch + AGS grade passback** for the tool. Integration effort (SIS/SSO/gradebook) "consistently takes longer than vendor timelines suggest" — make it turnkey. [C22]
5. **Faculty adoption** is gated by **ease + not increasing workload + gradebook fit + evidence it works** — not by feature lists. [C23]

> **The procurement stall is the opportunity.** Many AI deployments "stall at the intersection of FERPA, data residency, and the contractual status of commercial cloud APIs." LMS Bridge's **bring-your-own-key + PII minimization + self-hosting** is a direct answer to the #1 reason AI tools *don't* get approved. [C24]

---

## 4. Where LMS Bridge can win (the gap)

Synthesizing all of the above, the defensible position is the intersection of five things almost no competitor combines:

1. **Augments, doesn't replace.** No textbook lock-in, no content to license. (Publishers can't follow you here without cannibalizing courseware revenue; Realizeit is the only close analog and it's heavy/custom.)
2. **Pedagogy-first, answer-refusing.** Retrieval practice (meta-analytic g ≈ 0.5–0.7), intelligent tutoring (g ≈ 0.4–0.7), mastery learning — **the evidence base is real and peer-reviewed**; lead with it instead of "adaptive AI = better grades" (which the data does *not* support). [C25][C26][C27]
3. **Privacy/compliance as a feature, not a footnote.** BYO-AI key, PII minimization, self-hosting → clears the FERPA/HECVAT/data-residency gate that kills most AI tools.
4. **LMS-native (LTI 1.3 across all four majors).** Turnkey launch + grade passback is the thing faculty can't build themselves.
5. **Priced as an institutional layer**, not per-student courseware — easier for a CTO/CTL to buy than a bookstore fee.

**Honesty anchors (use these — they build trust the way Knewton's black box did not):** adaptive-alone has a *mixed* efficacy record (11 of 15 courses showed no grade impact in one multi-college study); what moves outcomes is **implementation + pedagogy**, per CMU's Open Learning Initiative (½ the time, equal/better outcomes). Position as **pedagogy-and-implementation-led, with measured claims.** [C28][C29]

---

## 5. Recommended restructuring & positioning

### 5.1 Reframe the product narrative (one line)
> *"LMS Bridge is the FERPA-safe remediation layer for your existing courses — it turns LMS assessment data into Socratic, answer-free practice that strengthens prerequisites, installs via LTI 1.3 in minutes, and runs on your own AI key or inside your own walls."*

Three pillars, in this order: **(1) Trust/compliance → (2) Pedagogy/evidence → (3) Effortless LMS integration.** Features come after.

### 5.2 Build a "Trust Center" — the highest-ROI work you can do now
This is what unlocks procurement, and most of it is content/process, not code:
- Pre-fill a **HECVAT 4** workbook and publish a **security one-pager**.
- Produce a **VPAT/ACR** (WCAG 2.1 AA) and commit to it in the product (accessibility is now a legal deadline, not a nicety).
- Ship a **standard DPA / FERPA "school official" addendum** template and a **sub-processor list**.
- A public `/trust` page summarizing data flows, BYO-key, PII-minimization, self-hosting, retention/deletion.
- **Pursue 1EdTech LTI Advantage certification** (you already implement LTI 1.3/AGS/NRPS/Deep Linking/Dynamic Registration — you are close) so you can be *written into RFPs*.

### 5.3 Productize the two delivery models you already built
- **Managed SaaS** (BYO-AI key) for fast pilots.
- **Self-hosted / in-your-VPC** for FERPA-strict institutions — make this a **named, priced tier** (you already have the licensing + signed-license-file machinery). This is a genuine differentiator vs. ALEKS/Knewton/Khanmigo, none of which you can run inside your own boundary.

### 5.4 Packaging & pricing
- Sell an **institutional/departmental subscription** (per active student band or per course, annual), **not** a bookstore per-student fee. Land with a **free/low-cost single-course pilot** (your manual no-LMS course-setup path is perfect for this), expand to campus.
- Keep the **answer-refusal + retrieval/mastery instrumentation** as the headline; that's the integrity story CTLs want post-ChatGPT.

### 5.5 Product roadmap priorities (highest leverage first)
1. **Accessibility pass to WCAG 2.1 AA** + VPAT. (Legal gate; do first.)
2. **Efficacy instrumentation**: built-in pre/post mastery deltas and an exportable "impact report" per course — institutions buy *evidence*, and it counters the "adaptive doesn't work" skepticism with *your own* data.
3. **Enterprise AI connectors**: first-class **Azure OpenAI / OpenAI-enterprise (DPA/ZDR)** support in the BYO-key UI, since that's the FERPA-approved path institutions already have.
4. **1EdTech certification + HECVAT/VPAT artifacts.**
5. **LMS depth**: rock-solid AGS grade passback and NRPS roster sync as a selling point ("no extra faculty workload").
6. **Anti-gaming UX**: address the "Socratic is slower/frustrating" tension (hint pacing, scaffolds, "reveal worked example after genuine attempt") so students don't bounce.

### 5.6 Go-to-market sequence
Department pilot (one instructor, one high-DFW gateway STEM course) → measured impact report → CTL/Provost + IT security review (hand them the pre-built HECVAT/VPAT/DPA) → campus license → list in EduAppCenter/IntegrationHub/Blackboard catalog + 1EdTech directory for credibility → repeat by discipline.

---

## 6. Bottom line
- **No storefront will sell this for you.** Win bottom-up with pilots, and make procurement frictionless with a Trust Center + certifications.
- **Don't compete with publishers on courseware.** Compete on being the **augmenting, content-free, privacy-first, answer-refusing** layer they structurally can't offer.
- **Your moat is the boring, hard stuff you've already built** (LTI 1.3 depth, BYO-AI, self-hosting, licensing) plus the compliance artifacts you haven't yet — not the chatbot. Lead with trust and evidence.

---

## Sources
[C1] Canvas community — LTI 1.3 vs EduAppCenter install: community.canvaslms.com (Canvas Developers) · [C2] developerdocs.instructure.com — LTI registration · [C3] blackboard.com/integration-partnerships/program-faqs (tiers + $3,000/yr DN) · [C4] d2l.com/partners + integrationhub.brightspace.com · [C5] moodledev.io/general/community/plugincontribution; moodle.com/become-moodle-partner · [C6] 1edtech.org/certification/lti; /get-certified · [C7] 1edtech.org/about/membership/technology-provider · [C8] 1edtech.org/program/trustedapps; /certification/data-privacy/faq · [C9] 1edtech.org/standards/lti/suggested-lti-advantage-requirements-rfps · [C10] instructure.com/learnplatform; press release (LearnPlatform acq., 2022) · [C11] gg4l.com / schoolday.com · [C12] freethink.com/consumer-tech/khanmigo-ai-tutor · [C13] arXiv:2512.03501 (SocraticAI, 2025) · [C14] news.harvard.edu — tailored AI tutor, engagement doubled (2024) · [C15] huit.harvard.edu/ai-sandbox; uit.stanford.edu · [C16] educause.edu — HECVAT overview + FAQs (HECVAT 4, AI questions) · [C17] saltycloud.com/blog/what-is-the-hecvat (legacy question counts) · [C18] ada.gov/resources/2024-03-08-web-rule (WCAG 2.1 AA, Title II) · [C19] federalregister.gov 2026-07663 (deadline extension to 2027/2028) · [C20] studentprivacy.ed.gov — PTAC third-party vendor FAQ (FERPA school-official exception) · [C21] learn.microsoft.com — Azure OpenAI data privacy; help.openai.com — training/DPA · [C22] 1edtech.org/standards/lti/why-adopt-lti-1p3; incommon.org · [C23] TAM literature (PMC4605370); eLearning Industry evaluation framework · [C24] arXiv:2605.05410 (FERPA local-LLM procurement stall; preprint) · [C25] Rowland 2014 / Adesope 2017 (retrieval practice meta-analyses) · [C26] VanLehn 2011; Ma et al. 2014 (ITS meta-analyses) · [C27] Lovett, Meyer & Thille 2008 (CMU OLI) · [C28] insidehighered.com 2016 — adaptive courseware mixed efficacy · [C29] edsurge.com 2019 — Knewton/Wiley; insidehighered.com 2019 — adaptive shakeout

*Market-size estimates (all analyst figures, cite as ranges): adaptive learning ~$4–5B (2024–25), 17–32% CAGR (Precedence, Mordor/M&M); AI-in-education ~$8.3B (2025) → ~$32B by 2030 at ~31% CAGR (Grand View). Methodologies are proprietary and diverge 2–4× between firms.*
