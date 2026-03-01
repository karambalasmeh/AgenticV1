from __future__ import annotations

from typing import Any, Sequence

from app.domain.models import Citation, Confidence, ValidationIssue


class ConfidenceScorer:
    def score(
        self,
        answer: str,
        citations: Sequence[Citation],
        validation_issues: Sequence[ValidationIssue],
        signals: dict[str, Any] | None = None,
    ) -> Confidence:
        signals = dict(signals or {})
        score = 0.85
        reasons: list[str] = []

        high_issues = [issue for issue in validation_issues if issue.severity == "high"]
        medium_issues = [issue for issue in validation_issues if issue.severity == "medium"]
        low_issues = [issue for issue in validation_issues if issue.severity == "low"]

        score -= 0.30 * len(high_issues)
        score -= 0.15 * len(medium_issues)
        score -= 0.05 * len(low_issues)
        if high_issues:
            reasons.append(f"{len(high_issues)} high-severity validation issue(s).")
        if medium_issues:
            reasons.append(f"{len(medium_issues)} medium-severity validation issue(s).")

        answer_len = len((answer or "").split())
        citation_count = len(list(citations))
        if answer_len > 80 and citation_count < 2:
            score -= 0.10
            reasons.append("Long answer with low evidence coverage.")
        elif answer_len > 40 and citation_count == 0:
            score -= 0.08
            reasons.append("No evidence attached for multi-sentence answer.")

        repair_attempts = int(signals.get("repair_attempts", 0))
        if repair_attempts:
            score -= min(0.15, 0.05 * repair_attempts)
            reasons.append(f"{repair_attempts} repair attempt(s) were required.")

        if signals.get("missing_evidence"):
            score -= 0.08
            reasons.append("Expected evidence could not be retrieved.")

        score = max(0.0, min(1.0, score))
        if score >= 0.75:
            level = "high"
        elif score >= 0.45:
            level = "medium"
        else:
            level = "low"

        if not reasons:
            reasons.append("No major quality risks detected.")

        signals.update(
            {
                "answer_word_count": answer_len,
                "citation_count": citation_count,
                "high_issues": len(high_issues),
                "medium_issues": len(medium_issues),
                "low_issues": len(low_issues),
            }
        )
        return Confidence(score=score, level=level, rationale=reasons, reasons=reasons, signals=signals)
