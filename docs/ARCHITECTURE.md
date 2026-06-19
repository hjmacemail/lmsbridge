# LMS Bridge — Architecture

This document describes the system design, data model, the remediation pipeline, and the
pedagogical guardrails that constrain the AI.

## 1. Design principles

1. **Just-in-time.** Remediation is generated automatically the moment a formative assessment
   reveals an at-risk concept — before the gap compounds in cumulative material.
2. **Pedagogically constrained, not a chatbot.** The model diagnoses and guides using retrieval
   practice, Socratic scaffolding, and mastery progression. It never supplies graded answers.
3. **Provider- and LMS-agnostic.** Business logic depends only on abstract interfaces, so the
   LLM vendor and the LMS can change via configuration without code changes. This is what keeps
   student-data processing inside institution-approved, FERPA-compliant infrastructure.
4. **Augmentation layer.** Faculty keep full control of content, grading, and outcomes.

## 2. Components

| Component | Module | Responsibility |
|-----------|--------|----------------|
| Brightspace adapter | `app/integrations/brightspace` | Read classlists + graded results (mock or Valence) |
| Sync service | `app/services/sync_service.py` | Pull results, upsert students/assessments, enroll |
| Ingestion pipeline | `app/services/ingestion_service.py` | Persist result → update mastery → trigger remediation |
| Mastery service | `app/services/mastery_service.py` | EWMA mastery estimate + status classification |
| Remediation engine | `app/services/remediation_engine.py` | Generate modules + evaluate responses via LLM |
| Pedagogy templates | `app/pedagogy/prompts.py` | The constrained system prompt + strategy guidance |
| LLM layer | `app/llm` | Provider-agnostic `complete()` contract + providers |
| API | `app/api/routes` | REST endpoints with JWT auth + RBAC |

## 3. Data model

```
User ──< Enrollment >── Course ──< Concept >──(self-ref prerequisites)
                          │            │
                          │            └──< ConceptMastery >── User(student)
                          │
                          └──< Assessment ──< Question >── Concept
                                   │
                                   └──< AssessmentResult (item_scores JSON) ── User(student)

RemediationModule ── Concept, User(student), Course, trigger AssessmentResult
   └──< RemediationActivity ──< StudentResponse
```

Key tables:

- **Concept** — a course learning objective with an ordered `sequence` and a self-referential
  `prerequisites` graph, encoding the cumulative structure of STEM material.
- **ConceptMastery** — one row per (student, concept); a 0–1 `mastery_score` plus status
  (`at_risk` / `developing` / `mastered`) and an `evidence_count`.
- **AssessmentResult.item_scores** — JSON list of per-item `{concept_key, earned, max}` used to
  derive concept-level signals.
- **RemediationModule / Activity / StudentResponse** — the generated remediation unit, its
  ordered activities, and the student's attempts with AI formative feedback.

## 4. The remediation pipeline

1. **Sync.** `sync_service` calls the Brightspace adapter's `fetch_new_results()`; for each
   result it ensures the student exists and is enrolled, and ensures the assessment exists.
2. **Ingest.** `ingestion_service.ingest_result()` persists the result and aggregates
   `item_scores` into a normalized score per concept.
3. **Update mastery.** For each concept, `mastery_service.update_mastery()` applies an
   exponentially-weighted moving average (`alpha = 0.5`) — transparent and explainable to
   instructors — and reclassifies status against the configured thresholds.
4. **Trigger.** When a concept becomes `at_risk` and the student has no open module for it, the
   remediation engine generates one.
5. **Generate.** `remediation_engine.generate_module()` builds a constrained prompt (system
   guardrails + concept + strategy + performance evidence) and asks the LLM for a JSON module of
   active-engagement activities, which are persisted.
6. **Practice & feedback.** As the student responds, `evaluate_response()` runs the constrained
   tutor to return formative feedback and judge whether the misconception is resolving — without
   revealing the answer.

## 5. Pedagogical guardrails

The system prompt (`TUTOR_SYSTEM_PROMPT` in `app/pedagogy/prompts.py`) encodes non-negotiable
rules: never give graded answers; ground everything in learning science; target the specific
demonstrated misconception; require active recall/reasoning/production; stay mastery-oriented and
aligned to course objectives. Three strategies are available and steer activity design:

- **Retrieval practice** — free recall and spaced self-testing before explanation.
- **Socratic scaffolding** — graduated probing questions that surface the hidden faulty assumption.
- **Mastery progression** — diagnostic → guided reasoning → independent application.

## 6. LLM abstraction

`app/llm/base.py` defines `LLMProvider.complete(messages, json_mode)`. Concrete providers:
`mock` (deterministic, no network — used for dev/CI and as a safe fallback), `anthropic`,
`openai`, and `azure_openai`. `app/llm/factory.py` selects one from configuration and degrades
gracefully to the mock if credentials are missing. JSON outputs are parsed defensively
(`extract_json`) with a safe fallback module so a malformed completion never breaks a request.

## 7. Brightspace integration

The `mock` adapter seeds three realistic STEM courses (computer architecture, OOP, statistics)
with per-concept item scores, deliberately weak on early concepts to exercise remediation.

To go live with the `valence` adapter, complete these extension points in
`app/integrations/brightspace/valence.py`:

1. **Auth** — D2L app/user-key HMAC signing (`x_a/x_b/x_c/x_d/x_t` params) or OAuth2 bearer.
2. **Classlist** — `GET /d2l/api/le/{version}/{orgUnitId}/classlist/`.
3. **Grades** — poll `…/grades/` and `…/grades/{id}/values/`; maintain a per-course cursor
   (last-seen grade timestamp) for incremental pulls.
4. **Quiz answers (MCQ)** — pull per-question responses via the Quizzing API
   (`…/quizzing/{orgUnit}/quizzes/{id}/attempts/`) to populate each `BSItemScore` with the
   student's `selected` option, the `correct` option, and `is_correct`. Map each distractor to a
   misconception in the course's question metadata so the adaptive engine can cite it.
5. **Concept mapping** — map each Brightspace grade item / question to a concept key (configured
   by the instructor at course onboarding) via `_map_grade_item`.

The chosen wrong option is the highest-value diagnostic signal: `_evidence_summary` in the
remediation engine lists each incorrectly-answered MCQ for the concept — the question, the option
the student chose vs. the correct one, and the misconception that distractor reveals — and injects
it into the generation prompt, so remediation is justified by the student's actual answers.

## 8. API surface (`/api/v1`)

| Method | Path | Role | Purpose |
|--------|------|------|---------|
| GET | `/health` | public | Liveness + dependency status |
| POST | `/auth/login` | public | OAuth2 password grant → JWT |
| GET | `/auth/me` | any | Current user |
| GET | `/courses`, `/courses/{id}` | any | Courses + concepts |
| GET | `/assessments` | instructor | List assessments |
| POST | `/assessments/results` | instructor | Manual/CSV result ingest |
| POST | `/assessments/sync` | instructor | Pull from Brightspace + remediate |
| PATCH | `/assessments/{id}/adaptive` | instructor | Enable/disable an assessment for adaptive learning |
| POST | `/assessments/recompute` | instructor | Rebuild mastery + remediation from enabled assessments |
| GET | `/remediation/modules` | any | List own (student) or all (instructor) modules |
| POST | `/remediation/modules/{id}/start\|complete` | owner | Lifecycle |
| POST | `/remediation/activities/{id}/respond` | owner | Submit response → AI feedback |
| POST | `/remediation/generate` | instructor | Manually generate a module |
| GET | `/students/me/dashboard`, `/students/{id}/dashboard` | self/instructor | Mastery + open modules |
| GET | `/analytics/courses/{id}` | instructor | Class-level concept risk |
| GET | `/analytics/courses/{id}/roster` | instructor | Per-student mastery + remediation summary |
| GET | `/analytics/courses/{id}/students/{sid}` | instructor | Drill-down: mastery, results, modules |
| GET | `/analytics/courses/{id}/assessments` | instructor | Per-assessment, per-concept + rubric breakdown |
| GET | `/analytics/courses/{id}/remediation` | instructor | Every module with activities + responses |
| GET | `/analytics/courses/{id}/export.csv` | instructor | CSV export of mastery + remediation |
| GET/POST | `/materials` | any/instructor | List / upload course material |
| GET | `/materials/{id}/download` | any | Download original file |
| DELETE | `/materials/{id}` | instructor | Remove material |

Course materials are stored with extracted text; `material_service.grounding_excerpts` selects the
most relevant excerpts per concept (concept-tag first, then keyword overlap) and the remediation
engine injects them into the generation prompt. Each `RemediationModule.grounded_on` records the
material titles used, for transparency.

## 9. Scaling notes

- The pipeline is synchronous for clarity. For large cohorts, move `generate_module` and
  `sync_course_results` onto a task queue (Celery/RQ/Arq) and schedule periodic polls.
- Mastery estimation is intentionally simple (EWMA). It can be replaced with a richer model
  (e.g. Bayesian Knowledge Tracing) behind the same `mastery_service` interface.
- Postgres + stateless API containers scale horizontally behind a load balancer.
