from app.agents.assurance.validator import Validator
from app.schemas.artifacts import Citation, ValidationIssue


def test_validator_flags_missing_structure_and_citations() -> None:
    validator = Validator()
    draft = "Economic outlook remains uncertain. Data indicates a decline."

    result = validator.run(draft, [])

    issue_types = {issue.type for issue in result.issues}
    assert not result.passed
    assert "missing_citations" in issue_types
    assert "incomplete_structure" in issue_types


def test_validator_accepts_structured_answer_with_citations() -> None:
    validator = Validator()
    draft = """Summary: Growth is steady.
Analysis: Production increased 5% in Q1 with matching exports.
Recommendation: Maintain subsidy caps and re-run audit in 60 days.
"""
    citations = [
        Citation(source_id="src-1", chunk_id="chunk-1", relevance_score=0.8),
        Citation(source_id="src-2", chunk_id="chunk-5", relevance_score=0.7),
    ]

    result = validator.run(draft, citations)

    assert result.passed
    assert result.issues == []


def test_validator_detects_unsupported_numeric_claims() -> None:
    validator = Validator()
    draft = "Summary: Inflation reached 12% and unemployment hit 18% with no sources."

    result = validator.run(draft, [])

    issue_types = {issue.type for issue in result.issues}
    assert "unsupported_claims" in issue_types


def test_validator_detects_conflicting_language_and_sources() -> None:
    validator = Validator()
    draft = "Summary: Production will increase by 4% yet decrease by 2% due to shortages."
    citations = [
        Citation(source_id="src-1", chunk_id="a", title="Report supports expansion", publisher="ThinkLab", relevance_score=0.9),
        Citation(source_id="src-1", chunk_id="b", title="Audit refutes expansion", publisher="AuditLab", relevance_score=0.4),
    ]

    result = validator.run(draft, citations)

    issue_types = {issue.type for issue in result.issues}
    assert "conflicting_evidence" in issue_types
    assert "conflicting_sources" in issue_types


def test_validator_recommendations_are_unique_and_mapped() -> None:
    validator = Validator()
    issues = [
        ValidationIssue(type="missing_citations", severity="high", details=""),
        ValidationIssue(type="missing_citations", severity="high", details="duplicate instance"),
        ValidationIssue(type="conflicting_evidence", severity="medium", details=""),
    ]

    actions = validator.recommend_actions(issues)

    assert actions == [
        "Attach at least one trusted source that backs key claims.",
        "Resolve contradictory statements or clarify timeframe.",
    ]


def test_validator_flags_invalid_and_duplicate_citations() -> None:
    validator = Validator()
    draft = "Summary: GDP grew 3% quarter over quarter."
    citations = [
        Citation(source_id="src-1", chunk_id="", relevance_score=0.01),
        Citation(source_id="src-1", chunk_id="", relevance_score=0.01),
    ]

    result = validator.run(draft, citations)

    issue_types = {issue.type for issue in result.issues}
    assert "invalid_citations" in issue_types
    assert "duplicate_citations" in issue_types
