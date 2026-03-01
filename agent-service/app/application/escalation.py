from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from app.domain.models import Confidence, Escalation, ValidationIssue


@dataclass(frozen=True)
class EscalationPolicy:
    low_confidence_threshold: float = 0.45
    high_risk_issue_types: tuple[str, ...] = (
        "conflicting_evidence",
        "answer_evidence_conflict",
        "missing_citations",
        "language_mismatch",
    )


class EscalationEngine:
    def __init__(self, policy: EscalationPolicy | None = None) -> None:
        self.policy = policy or EscalationPolicy()

    def evaluate(
        self,
        confidence: Confidence,
        validation_issues: Sequence[ValidationIssue],
        signals: dict[str, Any] | None = None,
    ) -> Escalation:
        signals = signals or {}
        triggers: list[str] = []

        if confidence.score < self.policy.low_confidence_threshold or confidence.level == "low":
            triggers.append("low_confidence")

        if any(issue.type in self.policy.high_risk_issue_types for issue in validation_issues):
            triggers.append("validation_risk")

        if signals.get("policy_uncertainty"):
            triggers.append("policy_uncertainty")
        if signals.get("repeat_violations"):
            triggers.append("repeat_violations")
        if signals.get("evidence_missing_when_required"):
            triggers.append("missing_required_evidence")

        triggered = bool(triggers)
        return Escalation(
            triggered=triggered,
            reason=", ".join(triggers) if triggers else None,
            triggers=triggers,
        )
