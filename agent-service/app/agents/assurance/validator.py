from __future__ import annotations

from typing import List
from app.schemas.artifacts import Validation, Citation
from app.agents.assurance.basic_validator import basic_validate
from app.core.config import settings

class Validator:
    def __init__(self):
        self.require_citations = getattr(settings, "REQUIRE_CITATIONS", False)

    def run(self, answer_draft: str, citations: List[Citation]) -> Validation:
        passed, issues = basic_validate(answer_draft, citations, self.require_citations)
        return Validation(passed=passed, issues=issues)
