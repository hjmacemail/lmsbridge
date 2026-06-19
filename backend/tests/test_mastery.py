from app.models.enums import MasteryStatus
from app.services.mastery_service import _status_for, concept_scores_from_result


class _R:
    item_scores = [
        {"concept_key": "a", "earned": 1, "max": 5},
        {"concept_key": "a", "earned": 3, "max": 5},
        {"concept_key": "b", "earned": 5, "max": 5},
    ]
    rubric_criteria = [
        {"concept_key": "b", "points": 4, "max_points": 5},
    ]


def test_concept_scores_aggregate():
    scores = concept_scores_from_result(_R())
    assert round(scores["a"], 2) == 0.40   # mean of item scores 0.2 and 0.6
    assert scores["b"] == 0.9              # mean of item 1.0 and rubric 0.8


def test_status_thresholds():
    assert _status_for(0.95) == MasteryStatus.mastered
    assert _status_for(0.5) == MasteryStatus.at_risk
    assert _status_for(0.8) == MasteryStatus.developing
