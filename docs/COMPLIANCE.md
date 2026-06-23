# Compliance & Data-Processing Summary (HECVAT-lite)

A short, procurement-oriented summary to help an institution's IT, privacy, and security reviewers
evaluate LMS Bridge quickly. It complements the deeper
[`PRIVACY_AND_SELF_HOSTING.md`](PRIVACY_AND_SELF_HOSTING.md) and
[`../SECURITY.md`](../SECURITY.md). *Informational, not legal advice — have your counsel review any
agreement.*

## At a glance

| Question | Answer |
| --- | --- |
| What is it? | An LTI 1.3 tool that turns LMS assessment results into AI-guided remediation. |
| Hosting model | **Self-hosted** by the institution (Docker / your cloud). Optional vendor-managed hosting is available separately. |
| License | Open source, AGPL-3.0 — full source is auditable. |
| Where does student data live? | In **your** application database, within your boundary when self-hosted. |
| Third-party sub-processors | **None** required beyond the AI provider **you** choose (Anthropic / OpenAI / Azure OpenAI) under **your** key/contract. A deterministic mock provider needs no external calls. |
| Does it train AI on student data? | No. The tool does not train models; inference runs under your provider contract and settings. |
| PII sent to the AI | Minimized: concept, answer text, misconception, instructor material excerpts. **No** names, emails, or LMS ids. |
| Authentication | LTI 1.3 (no shared secrets; platform JWKS verification) + signed JWT app sessions. |
| Accessibility | Standards-based HTML UI; a VPAT can be produced for a specific release on request. |

## Data inventory

| Data | Source | Purpose | Storage | Sent to AI? |
| --- | --- | --- | --- | --- |
| Name, email, LMS user id | LMS via LTI/NRPS (or Sage signup) | Identify the user, render rosters/grades | App DB | No |
| Course / roster / enrollment | LMS (NRPS) or Sage | Scope content and analytics | App DB | No |
| Assessment scores, per-question/rubric detail | LMS (AGS) or Sage quizzes | Detect concept-level misconceptions | App DB | Concept + answer text + misconception only |
| Remediation activity & tutor transcripts | Generated in-app | Deliver and track guided practice | App DB | Yes (no identifiers) |
| Instructor course materials | Instructor upload / LMS import | Ground the AI in course content | App DB | Excerpts only |
| AI provider key (per tenant) | Institution admin | Run inference under your contract | App DB, **encrypted at rest** (Fernet) | n/a |

## FERPA notes

- Education records remain in systems the institution controls; with self-hosting the data does not
  leave the institutional boundary.
- The AI provider, when used, acts under the institution's own agreement (a "school official" /
  processor arrangement is the institution's to establish with its chosen provider).
- Mastery indicators are a **private learning aid** and are **not** grades; official grades remain
  solely the instructor's via the LMS.
- Access is role-based and per-course authorized; instructors see only their own courses.

## Security summary

LTI 1.3 (no shared secrets), JWT sessions, RBAC + per-course authorization (no cross-course/tenant
access), encrypted per-tenant secrets, HTTPS transport, no silent telemetry, reproducible Docker
builds, and CI that runs LTI-conformance and authorization tests. Full detail and the vulnerability
reporting process are in [`../SECURITY.md`](../SECURITY.md).

## Documents available on request

- VPAT (accessibility) for a named release.
- A completed full HECVAT (Higher Education Community Vendor Assessment Toolkit) for a deployment.
- A signed Data Processing Agreement (for vendor-managed hosting).
