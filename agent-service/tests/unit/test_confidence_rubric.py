from app.orchestration.policies.confidence_rubric import ConfidenceRubric
from app.schemas.artifacts import Citation, ValidationIssue


def test_confidence_low_with_high_severity_issues() -> None:
    rubric = ConfidenceRubric()
    issues = [
        ValidationIssue(type="missing_citations", severity="high", details=""),
        ValidationIssue(type="unsupported_claims", severity="medium", details=""),
    ]
    draft = "Summary: Claims without sources."

    score = rubric.score(draft, [], validation_issues=issues, signals={"repair_attempts": 1})

    assert score.level == "low"
    assert score.score < 0.35
    assert any("validation" in reason.lower() for reason in score.rationale)


def test_confidence_high_when_clean_and_cited() -> None:
    rubric = ConfidenceRubric()
    draft = "Summary: Growth steady. Analysis: Production up 3%. Recommendation: stay course."
    citations = [
        Citation(source_id="src-1", chunk_id="a1", relevance_score=0.9),
        Citation(source_id="src-2", chunk_id="b2", relevance_score=0.8),
    ]

    score = rubric.score(draft, citations, validation_issues=[], signals={})

    assert score.level == "high"
    assert score.score >= 0.7
