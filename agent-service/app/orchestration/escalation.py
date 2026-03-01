<<<<<<< HEAD
from __future__ import annotations

from typing import Any, Dict, Optional
from app.schemas.artifacts import Escalation, Validation, Confidence

class EscalationEngine:
=======
"""Escalation rules triggered by validation and confidence outcomes."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Sequence, List

from app.schemas.artifacts import Escalation, Validation, ValidationIssue, Confidence


@dataclass(frozen=True)
class EscalationPolicy:
    """Deterministic quality triggers."""

    low_confidence_score: float = 0.35
    max_repair_failures: int = 2
    conflict_issue_types: tuple[str, ...] = ("conflicting_evidence", "conflicting_sources")


class EscalationEngine:
    """Evaluates whether a ticket should be created."""

    def __init__(self, policy: EscalationPolicy | None = None) -> None:
        self.policy = policy or EscalationPolicy()

>>>>>>> main
    def evaluate(
        self,
        validation: Validation,
        confidence: Confidence,
<<<<<<< HEAD
        signals: Dict[str, Any] = None
    ) -> Escalation:
        # Ported logic from karam:
        # if (not valid_after_repair) or (confidence.level == "low"):
        #     triggered = True
        
        triggered = False
        reason = None
        
        if not validation.passed:
            triggered = True
            reason = "invalid_output"
        elif confidence.level == "low":
            triggered = True
            reason = "low_confidence"
            
        return Escalation(
            triggered=triggered,
            reason=reason,
            ticket=None
        )
=======
        signals: Dict[str, int | bool] | None = None,
    ) -> Escalation:
        signals = signals or {}
        triggers: List[str] = []

        if confidence.level == "low" or confidence.score <= self.policy.low_confidence_score:
            triggers.append("low_confidence")

        high_severity = any(issue.severity == "high" for issue in validation.issues)
        if high_severity:
            triggers.append("high_severity_issue")

        if self._has_conflicts(validation.issues):
            triggers.append("evidence_conflict")

        repair_failures = int(signals.get("repair_failures", 0))
        if repair_failures >= self.policy.max_repair_failures:
            triggers.append("repeated_repairs")

        if signals.get("missing_documents"):
            triggers.append("missing_documents")

        triggered = bool(triggers)
        reason = ", ".join(triggers) if triggered else None
        return Escalation(triggered=triggered, reason=reason, ticket=None)

    def _has_conflicts(self, issues: Sequence[ValidationIssue]) -> bool:
        return any(issue.type in self.policy.conflict_issue_types for issue in issues)
>>>>>>> main
