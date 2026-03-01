from __future__ import annotations

from typing import Any, Sequence

from app.application.confidence import ConfidenceScorer
from app.domain.models import Citation, Confidence, ValidationIssue


class ConfidenceRubric:
    def __init__(self) -> None:
        self.scorer = ConfidenceScorer()

    def score(
        self,
        answer_draft: str,
        citations: Sequence[Citation],
        validation_issues: Sequence[ValidationIssue] | None = None,
        signals: dict[str, Any] | None = None,
    ) -> Confidence:
        return self.scorer.score(
            answer=answer_draft,
            citations=citations,
            validation_issues=validation_issues or [],
            signals=signals or {},
        )
