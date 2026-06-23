"""Realistic mock Brightspace adapter with seeded sample data.

Simulates the detailed performance data and learning analytics a real LMS provides:
multiple assessments per course (quizzes, assignments, exams), per-question item
scores tagged to concepts, rubric-level criteria with instructor feedback, and
engagement signals (attempts, time-on-task, lateness).

When a real Brightspace/LMS feed is wired in (Valence API or export tools), it only
needs to populate the same `BSResult` shape — no downstream changes required.
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

from app.integrations.brightspace.base import (
    BrightspaceAdapter,
    BSCourse,
    BSItemScore,
    BSResult,
    BSRubricCriterion,
    BSStudent,
)

# Ordered concepts per course (key, human label).
_COURSE_CONCEPTS: dict[str, list[tuple[str, str]]] = {
    "BS-CS201": [
        ("binary_representation", "binary representation"),
        ("binary_arithmetic", "binary arithmetic"),
        ("boolean_logic", "boolean logic"),
        ("machine_code", "machine-level computation"),
    ],
    "BS-CS310": [
        ("encapsulation", "encapsulation"),
        ("inheritance", "inheritance"),
        ("polymorphism", "polymorphism"),
        ("data_structures", "data structures"),
    ],
    "BS-DS200": [
        ("probability_basics", "probability basics"),
        ("conditional_probability", "conditional probability"),
        ("distributions", "distributions"),
        ("hypothesis_testing", "hypothesis testing"),
    ],
}

# Standard assessment plan applied to every course, in chronological order:
# 5 assignments (A01–A05), 2 quizzes, 2 exams (midterm + final).
# Each row: (suffix, title, type, max_score, week_offset, concept_indices)
_ASSESSMENT_PLAN: list[tuple[str, str, str, float, int, list[int]]] = [
    ("A01", "Assignment A01", "assignment", 50, 2, [0]),
    ("QUIZ1", "Quiz 1", "quiz", 20, 3, [0, 1]),
    ("A02", "Assignment A02", "assignment", 50, 4, [1]),
    ("A03", "Assignment A03", "assignment", 50, 6, [2]),
    ("EXAM-MID", "Midterm Exam", "exam", 100, 7, [0, 1, 2]),
    ("A04", "Assignment A04", "assignment", 50, 9, [3]),
    ("QUIZ2", "Quiz 2", "quiz", 20, 10, [2, 3]),
    ("A05", "Assignment A05", "assignment", 50, 12, [2, 3]),
    ("EXAM-FINAL", "Final Exam", "exam", 100, 14, [0, 1, 2, 3]),
]


def _assessments_for(course_external_id: str) -> list[tuple[str, str, str, float, int, list[int]]]:
    """Materialize the standard plan with course-scoped external ids."""
    return [
        (f"{course_external_id}-{suffix}", title, atype, mx, week, idxs)
        for suffix, title, atype, mx, week, idxs in _ASSESSMENT_PLAN
    ]

_RUBRIC_LEVELS = [
    (0.9, "Proficient"),
    (0.75, "Competent"),
    (0.6, "Developing"),
    (0.0, "Beginning"),
]

_RUBRIC_COMMENTS = {
    "Proficient": "Demonstrates secure command of {c}; reasoning is correct and complete.",
    "Competent": "Generally solid on {c}, with minor slips that don't undermine the approach.",
    "Developing": "Partial grasp of {c}; the central step is applied without justification.",
    "Beginning": ("Foundational misconception in {c} — revisit the underlying rule "
                  "before moving on."),
}

# Multiple-choice bank per concept. Each question has one correct option and several
# distractors; every distractor is authored to reveal a SPECIFIC misconception, which is
# exactly the signal the adaptive engine uses to justify what the student should focus on.
# Shape: concept_key -> [ {stem, correct, distractors: [(option_text, misconception), ...]} ]
_MCQ_BANK: dict[str, list[dict]] = {
    "binary_representation": [
        {"stem": "What is the unsigned decimal value of the binary number 1011?",
         "correct": "11",
         "distractors": [
             ("4", "Counts only the number of 1-bits instead of summing place values."),
             ("1011", "Reads the bits as base-10 digits rather than powers of two."),
             ("13", "Mis-assigns place values (uses 8+4+1 with the wrong columns)."),
         ]},
        {"stem": "How many distinct values can 4 bits represent?",
         "correct": "16",
         "distractors": [
             ("8", "Uses 2×n instead of 2^n for the number of combinations."),
             ("4", "Confuses the number of bits with the number of values."),
             ("15", "Forgets that zero is one of the representable values."),
         ]},
    ],
    "binary_arithmetic": [
        {"stem": "Compute 0111 + 0001 in 4-bit binary.",
         "correct": "1000",
         "distractors": [
             ("0112", "Treats binary like base-10 — writes a digit '2' instead of carrying."),
             ("0110", "Drops the carry when a column sums to two."),
             ("1110", "Carries into the wrong column."),
         ]},
        {"stem": "What is the two's-complement representation of -3 in 4 bits?",
         "correct": "1101",
         "distractors": [
             ("1011", "Only inverts the bits and forgets to add 1."),
             ("0011", "Ignores the sign and just encodes +3."),
             ("1100", "Adds 1 before inverting instead of after."),
         ]},
    ],
    "boolean_logic": [
        {"stem": "For A=1, B=0, what is (A AND B) OR (NOT B)?",
         "correct": "1",
         "distractors": [
             ("0", "Evaluates NOT before grouping, or treats OR as AND."),
             ("undefined", "Believes mixed operators can't be combined."),
         ]},
        {"stem": "Which expression is equivalent to NOT (A OR B)?",
         "correct": "(NOT A) AND (NOT B)",
         "distractors": [
             ("(NOT A) OR (NOT B)", "Misapplies De Morgan's law — keeps OR instead of AND."),
             ("A AND B", "Drops the negation entirely."),
         ]},
    ],
    "machine_code": [
        {"stem": "A register holds 0xFF (8-bit). After adding 1, the register holds:",
         "correct": "0x00 (with carry/overflow)",
         "distractors": [
             ("0x100", "Ignores fixed register width — assumes unbounded integers."),
             ("0xFF", "Believes the register saturates instead of wrapping."),
         ]},
    ],
    "encapsulation": [
        {"stem": "Why make a class field private and expose a getter/setter?",
         "correct": "To control and validate access to internal state",
         "distractors": [
             ("To make the program run faster", "Confuses encapsulation with performance."),
             ("Because private fields use less memory", "Invents a non-existent memory effect."),
         ]},
    ],
    "inheritance": [
        {"stem": "Base b = new Derived(); b.speak() is called. Derived overrides speak(). "
                 "Which runs?",
         "correct": "Derived.speak()",
         "distractors": [
             ("Base.speak()", "Thinks the reference (declared) type picks the method, "
                              "not the actual object — misses dynamic dispatch."),
             ("Neither — compile error", "Believes overriding hides the method from a base ref."),
         ]},
    ],
    "polymorphism": [
        {"stem": "A list holds Shape references to Circle and Square objects. Calling area() "
                 "on each gives:",
         "correct": "Each subclass's own area() implementation",
         "distractors": [
             ("Shape.area() for all", "Expects the base implementation regardless of object type."),
             ("A type error", "Doesn't see subclasses as substitutable for the base type."),
         ]},
    ],
    "data_structures": [
        {"stem": "Average-case lookup time in a well-sized hash map is:",
         "correct": "O(1)",
         "distractors": [
             ("O(n)", "Confuses hash-map lookup with linear search in a list."),
             ("O(log n)", "Confuses a hash map with a balanced binary search tree."),
         ]},
    ],
    "probability_basics": [
        {"stem": "Two fair coins are flipped. P(at least one head) = ?",
         "correct": "3/4",
         "distractors": [
             ("1/2", "Adds P(head) of a single coin and ignores the joint sample space."),
             ("1/4", "Computes P(both heads) instead of at-least-one."),
         ]},
    ],
    "conditional_probability": [
        {"stem": "If P(A∩B)=0.2 and P(B)=0.5, then P(A|B) = ?",
         "correct": "0.4",
         "distractors": [
             ("0.2", "Forgets to divide by P(B) — reports the joint probability."),
             ("0.1", "Multiplies P(A∩B)·P(B) instead of dividing."),
             ("0.7", "Adds the probabilities instead of conditioning."),
         ]},
    ],
    "distributions": [
        {"stem": "For X ~ Binomial(n=10, p=0.5), the expected value E[X] is:",
         "correct": "5",
         "distractors": [
             ("0.5", "Reports p instead of n·p."),
             ("10", "Reports n instead of n·p."),
         ]},
    ],
    "hypothesis_testing": [
        {"stem": "A p-value of 0.03 at α=0.05 means:",
         "correct": "Reject the null hypothesis",
         "distractors": [
             ("The null hypothesis is true with probability 0.03",
              "Misreads the p-value as P(H0 is true)."),
             ("Fail to reject the null", "Compares the p-value against α in the wrong direction."),
         ]},
    ],
}

MCQ_TYPES = ("quiz", "exam")
RUBRIC_TYPES = ("assignment", "problem_set")


def _level_for(frac: float) -> str:
    for threshold, label in _RUBRIC_LEVELS:
        if frac >= threshold:
            return label
    return "Beginning"


def _make_mcq_items(
    rng: random.Random, ckey: str, clabel: str, frac: float, n_q: int,
    assessment_id: str, student_id: str,
) -> list[BSItemScore]:
    """Generate `n_q` MCQ answers for a concept.

    The student answers each correctly with probability ~`frac`; on a wrong answer they
    select a distractor (deterministically), and we record which misconception it reveals.
    """
    bank = _MCQ_BANK.get(ckey)
    items: list[BSItemScore] = []
    for qi in range(n_q):
        if not bank:
            correct = "Correct option"
            stem = f"Multiple choice on {clabel}"
            distractors = [(f"A common error in {clabel}", f"Misconception about {clabel}.")]
        else:
            mcq = bank[qi % len(bank)]
            stem, correct, distractors = mcq["stem"], mcq["correct"], mcq["distractors"]

        is_correct = rng.random() < frac
        if is_correct:
            selected, misconception = correct, None
        else:
            selected, misconception = rng.choice(distractors)

        # Present options in a stable but non-trivial order.
        opt_rng = random.Random(f"{student_id}:{assessment_id}:{ckey}:{qi}")
        choices = [correct] + [d[0] for d in distractors]
        opt_rng.shuffle(choices)

        items.append(
            BSItemScore(
                concept_key=ckey,
                earned=1.0 if is_correct else 0.0,
                max=1.0,
                question=stem,
                choices=choices,
                selected=selected,
                correct=correct,
                is_correct=is_correct,
                misconception=misconception,
            )
        )
    return items


class MockBrightspaceAdapter(BrightspaceAdapter):
    name = "mock"

    def __init__(self, seed: int = 7) -> None:
        self._seed = seed

    def list_courses(self) -> list[BSCourse]:
        return [
            BSCourse("BS-CS201", "CS-UY 2110", "Computer Architecture & Digital Logic", "2026SP"),
            BSCourse("BS-CS310", "CS-UY 2124", "Object-Oriented Programming", "2026SP"),
            BSCourse("BS-DS200", "DS-UY 2003", "Statistical Reasoning for Data Science", "2026SP"),
        ]

    def list_students(self, course_external_id: str) -> list[BSStudent]:
        names = [
            "Ava Chen", "Marcus Lopez", "Priya Patel", "Diego Santos", "Lena Müller",
            "Omar Haddad", "Grace Kim", "Noah Williams",
        ]
        return [
            BSStudent(
                external_id=f"{course_external_id}-S{i:03d}",
                full_name=n,
                email=f"{n.split()[0].lower()}.{n.split()[1].lower()}@student.example.edu",
            )
            for i, n in enumerate(names, start=1)
        ]

    def fetch_new_results(self, course_external_id: str) -> list[BSResult]:
        concepts = _COURSE_CONCEPTS.get(course_external_id, [])
        assessments = _assessments_for(course_external_id)
        students = self.list_students(course_external_id)
        term_start = datetime(2026, 1, 26, tzinfo=timezone.utc)
        results: list[BSResult] = []

        for si, s in enumerate(students):
            # Deterministic per-student RNG so re-syncs are stable.
            rng = random.Random(f"{self._seed}:{s.external_id}")
            # Each student is persistently weaker on SEVERAL concepts, so multiple review
            # topics surface (richer demo). The first student (the one the demo signs in as)
            # always has 3 weak topics so "Recommended to review" is well populated.
            n_weak = min(len(concepts), 3 if si == 0 else rng.choice([2, 3]))
            weak_idxs = set(rng.sample(range(len(concepts)), n_weak)) if concepts else set()
            weak_keys = {concepts[i][0] for i in weak_idxs}
            weak_label = (concepts[min(weak_idxs)][1] if weak_idxs else None)

            for ext_id, title, atype, max_score, week, concept_idxs in assessments:
                available_at = term_start + timedelta(weeks=week)
                item_scores: list[BSItemScore] = []
                rubric: list[BSRubricCriterion] = []

                for ci in concept_idxs:
                    if ci >= len(concepts):
                        continue
                    ckey, clabel = concepts[ci]
                    base = 0.42 if ckey in weak_keys else rng.uniform(0.72, 0.97)
                    frac = max(0.05, min(1.0, base + rng.uniform(-0.07, 0.07)))

                    # Quizzes & exams are multiple-choice: emit per-question answers where the
                    # chosen distractor reveals a misconception. Assignments are rubric-graded.
                    if atype in MCQ_TYPES:
                        n_q = 3 if atype == "exam" else 2
                        item_scores.extend(
                            _make_mcq_items(rng, ckey, clabel, frac, n_q, ext_id, s.external_id)
                        )
                    if atype in RUBRIC_TYPES:
                        level = _level_for(frac)
                        crit_max = round(max_score / max(1, len(concept_idxs)), 1)
                        rubric.append(
                            BSRubricCriterion(
                                criterion=f"Correct application of {clabel}",
                                concept_key=ckey,
                                level=level,
                                points=round(frac * crit_max, 1),
                                max_points=crit_max,
                                comment=_RUBRIC_COMMENTS[level].format(c=clabel),
                            )
                        )

                # Overall normalized score.
                if item_scores:
                    overall = sum(i.earned for i in item_scores) / sum(i.max for i in item_scores)
                elif rubric:
                    overall = sum(r.points for r in rubric) / sum(r.max_points for r in rubric)
                else:
                    overall = rng.uniform(0.6, 0.9)

                summary = (
                    f"Strong overall, but watch your handling of {weak_label}."
                    if overall >= 0.7 and weak_label
                    else (f"Review {weak_label} — it's holding back the rest."
                          if weak_label else None)
                )

                results.append(
                    BSResult(
                        assessment_external_id=ext_id,
                        student_external_id=s.external_id,
                        score=round(overall, 3),
                        assessment_title=title,
                        assessment_type=atype,
                        assessment_max_score=max_score,
                        available_at=available_at,
                        item_scores=item_scores,
                        rubric_criteria=rubric,
                        rubric_feedback=summary,
                        attempts=rng.choice([1, 1, 1, 2]) if atype == "quiz" else 1,
                        time_on_task_minutes=round(rng.uniform(12, 95), 1),
                        submitted_late=rng.random() < 0.12,
                    )
                )
        return results
