from app.application.escalation import EscalationEngine
from app.domain.models import Confidence, ValidationIssue


def test_escalation_triggered_on_low_confidence() -> None:
    engine = EscalationEngine()
    confidence = Confidence(score=0.31, level="low", rationale=["low"], reasons=["low"], signals={})
    escalation = engine.evaluate(confidence=confidence, validation_issues=[], signals={})
    assert escalation.triggered is True
    assert "low_confidence" in escalation.triggers


def test_escalation_triggered_on_validation_risk() -> None:
    engine = EscalationEngine()
    confidence = Confidence(score=0.78, level="high", rationale=["ok"], reasons=["ok"], signals={})
    issues = [ValidationIssue(type="missing_citations", severity="high", details="missing")]
    escalation = engine.evaluate(confidence=confidence, validation_issues=issues, signals={})
    assert escalation.triggered is True
    assert "validation_risk" in escalation.triggers
