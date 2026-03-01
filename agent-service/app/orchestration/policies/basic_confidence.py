from __future__ import annotations

from typing import Any, Dict, List, Tuple

from app.schemas.artifacts import ValidationIssue


def score_confidence(
    valid: bool,
    issues: List[ValidationIssue],
    is_complex: bool,
    citations_count: int,
) -> Tuple[float, str, List[str], Dict[str, Any]]:
    # English comments only
    signals: Dict[str, Any] = {
        "validation_passed": valid,
        "issues_count": len(issues),
        "is_complex": is_complex,
        "citations_count": citations_count,
    }

    # Base score
    score = 0.8 if valid else 0.35

    # Penalties
    if is_complex:
        score -= 0.10
    if citations_count == 0:
        score -= 0.10

    # Extra penalty for high severity issues
    if any(i.severity == "high" for i in issues):
        score -= 0.20

    # Clamp
    score = max(0.0, min(1.0, score))

    # Level mapping
    if score < 0.45:
        level = "low"
    elif score < 0.75:
        level = "medium"
    else:
        level = "high"

    rationale = []
    rationale.append("Validation passed." if valid else "Validation failed.")
    if is_complex:
        rationale.append("Query complexity reduces confidence slightly.")
    if citations_count == 0:
        rationale.append("No citations available yet.")
    if issues:
        rationale.append(f"{len(issues)} validation issue(s) detected.")

    return score, level, rationale, signals