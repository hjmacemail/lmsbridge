"""Material extraction + AI grounding."""
from sqlalchemy import select

from app.models.concept import Concept
from app.models.course import Course
from app.services.extraction_service import extract_text
from app.services.material_service import create_material, grounding_excerpts


def test_extract_markdown_and_text():
    assert "carry" in extract_text("notes.md", "text/markdown", b"add and carry the 1").lower()
    assert extract_text("x.bin", "application/octet-stream", b"\x00\x01") is not None


def test_grounding_selects_relevant_material(db, seeded):
    course = db.scalar(select(Course))
    concept = db.scalar(
        select(Concept).where(
            Concept.course_id == course.id, Concept.key == "binary_arithmetic"
        )
    )
    create_material(
        db, course_id=course.id, title="Binary Notes", filename="b.md",
        content_type="text/markdown",
        data=b"Binary arithmetic: when a column sums to two, write 0 and carry the 1.",
        concept_id=concept.id,
    )
    db.commit()
    excerpts = grounding_excerpts(db, course_id=course.id, concept=concept)
    assert excerpts, "should find the tagged material"
    assert "carry" in excerpts[0]["excerpt"].lower()
