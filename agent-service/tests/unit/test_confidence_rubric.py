from app.application.confidence import ConfidenceScorer
from app.domain.models import Citation, ValidationIssue


def test_confidence_low_with_high_severity_issues() -> None:
    scorer = ConfidenceScorer()
    issues = [
        ValidationIssue(type="missing_citations", severity="high", details="missing"),
        ValidationIssue(type="language_mismatch", severity="high", details="language mismatch"),
    ]
    score = scorer.score(
        answer="A policy answer without evidence",
        citations=[],
        validation_issues=issues,
        signals={"repair_attempts": 2},
    )

    assert score.level == "low"
    assert score.score <= 0.45
    assert score.signals["high_issues"] == 2


def test_confidence_high_when_clean_and_cited() -> None:
    scorer = ConfidenceScorer()
    citations = [
        Citation(source_id="s1", chunk_id="c1", relevance_score=0.9),
        Citation(source_id="s2", chunk_id="c2", relevance_score=0.88),
    ]
    score = scorer.score(
        answer="Policy reform improved service quality and reduced waiting times significantly.",
        citations=citations,
        validation_issues=[],
        signals={},
    )

    assert score.level == "high"
    assert score.score >= 0.75
