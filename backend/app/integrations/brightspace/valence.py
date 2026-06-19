"""Brightspace (D2L) Valence API adapter — live integration scaffold.

This is a structured stub showing exactly where real Valence calls go. It uses the
documented Valence endpoints for org units, classlists and grades. Authentication
uses D2L's app/user-key HMAC signing scheme. Wire in real credentials via env vars
(BRIGHTSPACE_*) and a poll cursor before enabling in production.

Reference: https://docs.valence.desire2learn.com/
"""
from __future__ import annotations

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.integrations.brightspace.base import (
    BrightspaceAdapter,
    BSCourse,
    BSItemScore,
    BSResult,
    BSStudent,
)

logger = get_logger("brightspace.valence")
_LP = "/d2l/api/lp/1.40"   # Learning Platform
_LE = "/d2l/api/le/1.67"   # Learning Environment


class ValenceBrightspaceAdapter(BrightspaceAdapter):
    name = "valence"

    def __init__(self) -> None:
        if not settings.brightspace_base_url:
            raise RuntimeError("BRIGHTSPACE_BASE_URL is required for the valence adapter.")
        self.base_url = settings.brightspace_base_url.rstrip("/")
        self._client = httpx.Client(timeout=30.0)
        # In production, build a D2LSigner / OAuth2 token here from the app+user keys.

    def _get(self, path: str) -> dict | list:
        # NOTE: real implementation must append D2L HMAC auth query params
        # (x_a, x_b, x_c, x_d, x_t) or an OAuth2 bearer token.
        url = f"{self.base_url}{path}"
        resp = self._client.get(url)
        resp.raise_for_status()
        return resp.json()

    def list_courses(self) -> list[BSCourse]:
        data = self._get(f"{_LP}/enrollments/myenrollments/")
        courses: list[BSCourse] = []
        for item in data.get("Items", []):  # type: ignore[union-attr]
            ou = item.get("OrgUnit", {})
            if ou.get("Type", {}).get("Code") == "Course Offering":
                courses.append(
                    BSCourse(
                        external_id=str(ou.get("Id")),
                        code=ou.get("Code", ""),
                        title=ou.get("Name", ""),
                        term=str(ou.get("Semester", {}).get("Name", "")),
                    )
                )
        return courses

    def list_students(self, course_external_id: str) -> list[BSStudent]:
        data = self._get(f"{_LE}/{course_external_id}/classlist/")
        return [
            BSStudent(
                external_id=str(u.get("Identifier")),
                full_name=u.get("DisplayName", ""),
                email=u.get("Email", ""),
            )
            for u in data  # type: ignore[union-attr]
        ]

    def fetch_new_results(self, course_external_id: str) -> list[BSResult]:
        """Pull grade objects + rubric feedback, map grade items -> concept keys.

        Production notes:
          * Use the Grades API: {_LE}/{orgUnit}/grades/ and /grades/{id}/values/
          * Maintain a per-course poll cursor (last-seen grade timestamp).
          * Map each Brightspace grade item to a concept key via a stored mapping
            (configured by the instructor when onboarding the course).
        """
        logger.warning(
            "ValenceBrightspaceAdapter.fetch_new_results is a scaffold; "
            "implement grade polling + concept mapping before production use."
        )
        _ = self._map_grade_item  # referenced to document the extension point
        return []

    @staticmethod
    def _map_grade_item(grade_item_name: str, concept_map: dict[str, str]) -> BSItemScore | None:
        key = concept_map.get(grade_item_name)
        return BSItemScore(concept_key=key, earned=0.0, max=0.0) if key else None
