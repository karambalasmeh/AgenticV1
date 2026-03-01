from __future__ import annotations

from typing import List

from app.schemas.artifacts import ValidationIssue, Citation


def basic_validate(answer_draft: str, citations: List[Citation], require_citations: bool) -> tuple[bool, list[ValidationIssue]]:
    # English comments only
    issues: list[ValidationIssue] = []

    if not answer_draft or not answer_draft.strip():
        issues.append(
            ValidationIssue(
                type="empty_answer",
                severity="high",
                details="Answer draft is empty.",
            )
        )

    if require_citations and (not citations or len(citations) == 0):
        issues.append(
            ValidationIssue(
                type="missing_citation",
                severity="high",
                details="No citations provided while citations are required.",
            )
        )

    valid = len([i for i in issues if i.severity == "high"]) == 0
    return valid, issues