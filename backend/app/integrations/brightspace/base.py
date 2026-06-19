"""Brightspace integration adapter interface.

The rest of the system depends only on this interface, so the pilot can run on a
realistic mock today and switch to the live Brightspace Valence API later by
flipping BRIGHTSPACE_ADAPTER — with no changes to business logic.

The dataclasses below mirror the shape of the detailed performance data and learning
analytics an LMS provides: per-item scores tagged to concepts, rubric-level criteria
with feedback, and engagement signals (attempts, time-on-task, lateness).
"""
from __future__ import annotations

import abc
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class BSStudent:
    external_id: str
    full_name: str
    email: str


@dataclass
class BSCourse:
    external_id: str
    code: str
    title: str
    term: str


@dataclass
class BSItemScore:
    """A single graded question/item, tagged to a concept.

    For multiple-choice questions (quizzes, exams) the LMS exposes the student's
    selected option and the correct option. The chosen distractor is the key
    diagnostic signal — each wrong option maps to a specific misconception.
    """
    concept_key: str
    earned: float
    max: float
    question: str | None = None
    choices: list[str] | None = None       # MCQ options as shown to the student
    selected: str | None = None            # the option the student selected
    correct: str | None = None             # the correct option
    is_correct: bool | None = None
    # What the student's chosen (wrong) option reveals — drives targeted remediation.
    misconception: str | None = None


@dataclass
class BSRubricCriterion:
    """A rubric line item: a criterion scored at a level, with instructor feedback."""
    criterion: str
    concept_key: str
    level: str            # e.g. "Proficient", "Developing", "Beginning"
    points: float
    max_points: float
    comment: str | None = None


@dataclass
class BSResult:
    """A graded assessment outcome pulled from the LMS, with full analytics detail."""
    assessment_external_id: str
    student_external_id: str
    score: float  # normalized 0..1
    # Assessment metadata (lets us materialize realistic assessments).
    assessment_title: str = ""
    assessment_type: str = "quiz"           # quiz | assignment | exam | problem_set
    assessment_max_score: float = 100.0
    available_at: datetime | None = None
    # Detailed analytics.
    item_scores: list[BSItemScore] = field(default_factory=list)
    rubric_criteria: list[BSRubricCriterion] = field(default_factory=list)
    rubric_feedback: str | None = None
    # Engagement signals.
    attempts: int = 1
    time_on_task_minutes: float | None = None
    submitted_late: bool = False


class BrightspaceAdapter(abc.ABC):
    """Read-only access to LMS analytics needed to drive remediation."""

    name = "base"

    @abc.abstractmethod
    def list_courses(self) -> list[BSCourse]: ...

    @abc.abstractmethod
    def list_students(self, course_external_id: str) -> list[BSStudent]: ...

    @abc.abstractmethod
    def fetch_new_results(self, course_external_id: str) -> list[BSResult]:
        """Return graded results available since the last poll (newest formative data)."""
