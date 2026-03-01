<<<<<<< HEAD
from __future__ import annotations

from typing import Any, Dict, List
from app.schemas.artifacts import Confidence, ValidationIssue
from app.orchestration.policies.basic_confidence import score_confidence

class ConfidenceRubric:
    def score(
        self,
        answer_draft: str,
        citations: List[Any],
        validation_issues: List[ValidationIssue],
        signals: Dict[str, Any] = None,
    ) -> Confidence:
        # We need to map the arguments to score_confidence
        # score_confidence(valid, issues, is_complex, citations_count)
        
        # Note: 'valid' is usually calculated externally, but here we can infer it
        valid = not any(i.severity == "high" for i in validation_issues)
        is_complex = signals.get("is_complex", False) if signals else False
        
        score, level, rationale, out_signals = score_confidence(
            valid=valid,
            issues=validation_issues,
            is_complex=is_complex,
            citations_count=len(citations),
        )
        
        # Merge input signals if provided
        if signals:
            out_signals.update(signals)
            
        return Confidence(
            score=score,
            level=level,
            rationale=rationale,
            signals=out_signals
        )
=======
"""Deterministic scoring rubric for confidence estimates."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Sequence
import math

from app.schemas.artifacts import Citation, ValidationIssue, Confidence


@dataclass(frozen=True)
class ConfidenceThresholds:
    """Thresholds that keep scoring explainable."""

    base_score: float = 0.85
    high_cutoff: float = 0.7
    low_cutoff: float = 0.35
    citation_word_ratio: int = 80
    issue_penalties: Dict[str, float] = None

    def __post_init__(self) -> None:
        if self.issue_penalties is None:
            object.__setattr__(self, "issue_penalties", {"high": 0.35, "medium": 0.2, "low": 0.1})


class ConfidenceRubric:
    """Scores confidence using transparent, mock-first heuristics."""

    def __init__(self, thresholds: ConfidenceThresholds | None = None) -> None:
        self.thresholds = thresholds or ConfidenceThresholds()

    def score(
        self,
        answer_draft: str,
        citations: Sequence[Citation],
        validation_issues: Sequence[ValidationIssue] | None = None,
        signals: Dict[str, Any] | None = None,
    ) -> Confidence:
        text = (answer_draft or "").strip()
        signals = signals or {}
        validation_issues = validation_issues or []

        score = self.thresholds.base_score
        rationale: List[str] = []
        derived_signals: Dict[str, Any] = {}

        # 1) Penalize for validation issues
        issue_counts = self._count_by_severity(validation_issues)
        issue_penalty = sum(
            issue_counts.get(level, 0) * self.thresholds.issue_penalties[level] for level in self.thresholds.issue_penalties
        )
        if issue_penalty:
            score -= issue_penalty
            rationale.append(f"Penalty for validation issues ({issue_counts}).")
        derived_signals["validation_issue_counts"] = issue_counts

        # 2) Evidence coverage
        word_count = len(text.split())
        citation_count = len(list(citations))
        required_citations = math.ceil(word_count / self.thresholds.citation_word_ratio) if word_count else 0
        if required_citations and citation_count < required_citations:
            gap = required_citations - citation_count
            coverage_penalty = min(0.15 * gap, 0.3)
            score -= coverage_penalty
            rationale.append("Insufficient citations for answer length.")
        derived_signals["word_count"] = word_count
        derived_signals["citation_count"] = citation_count
        derived_signals["required_citations"] = required_citations

        # 3) Repair & document signals from upstream pipeline
        repair_attempts = int(signals.get("repair_attempts", 0))
        if repair_attempts:
            score -= min(0.05 * repair_attempts, 0.2)
            rationale.append(f"{repair_attempts} repair attempt(s) reduced confidence.")
        derived_signals["repair_attempts"] = repair_attempts

        missing_documents = bool(signals.get("missing_documents"))
        if missing_documents:
            score -= 0.1
            rationale.append("Critical documents missing.")
        derived_signals["missing_documents"] = missing_documents

        # Clamp score to [0, 1]
        score = max(0.0, min(1.0, score))

        level = self._bucket_level(score)
        if not rationale:
            rationale.append("Meets baseline rubric expectations.")

        return Confidence(score=score, level=level, rationale=rationale, signals=derived_signals)

    def _bucket_level(self, score: float) -> str:
        if score >= self.thresholds.high_cutoff:
            return "high"
        if score <= self.thresholds.low_cutoff:
            return "low"
        return "medium"

    @staticmethod
    def _count_by_severity(issues: Sequence[ValidationIssue]) -> Dict[str, int]:
        counts = {"high": 0, "medium": 0, "low": 0}
        for issue in issues:
            if issue.severity in counts:
                counts[issue.severity] += 1
        return counts
>>>>>>> main
