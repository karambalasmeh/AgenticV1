from __future__ import annotations

from app.domain.models import ValidationIssue


def has_blocking_issue(issues: list[ValidationIssue]) -> bool:
    return any(issue.severity == "high" for issue in issues)
