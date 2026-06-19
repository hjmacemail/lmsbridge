"""Shared enumerations for the domain model."""
from __future__ import annotations

import enum


class UserRole(str, enum.Enum):
    student = "student"
    instructor = "instructor"
    admin = "admin"


class AssessmentType(str, enum.Enum):
    quiz = "quiz"
    assignment = "assignment"
    exam = "exam"
    problem_set = "problem_set"


class MasteryStatus(str, enum.Enum):
    at_risk = "at_risk"
    developing = "developing"
    mastered = "mastered"


class RemediationStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    dismissed = "dismissed"


class ActivityType(str, enum.Enum):
    socratic = "socratic"          # Socratic scaffolding question
    retrieval = "retrieval"        # retrieval-practice question
    debugging = "debugging"        # structured debugging task
    explanation = "explanation"    # short explanatory sequence (requires active step)
    practice = "practice"          # adaptive practice problem


class PedagogyStrategy(str, enum.Enum):
    retrieval_practice = "retrieval_practice"
    socratic_scaffolding = "socratic_scaffolding"
    mastery_progression = "mastery_progression"
