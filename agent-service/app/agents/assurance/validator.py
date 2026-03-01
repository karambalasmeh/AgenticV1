from __future__ import annotations

from typing import Sequence

from app.application.validation import ResponseValidator
from app.domain.models import Citation, Validation, ValidationIssue


class Validator:
    def __init__(self, validator: ResponseValidator | None = None) -> None:
        self.validator = validator or ResponseValidator()

    def run(self, answer_draft: str, citations: Sequence[Citation]) -> Validation:
        issues = self.validator.validate(
            answer=answer_draft,
            expected_language="ar" if any("\u0600" <= c <= "\u06ff" for c in answer_draft) else "en",
            citations=citations,
            include_evidence=bool(citations),
            evidence_chunks=[],
        )
        return Validation(passed=not issues, issues=issues)

    def recommend_actions(self, issues: Sequence[ValidationIssue]) -> list[str]:
        return self.validator.recommend_actions(issues)
