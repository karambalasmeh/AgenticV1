from app.application.validation import ResponseValidator
from app.domain.contracts import KnowledgeChunk
from app.domain.models import Citation


def test_validator_requires_citations_when_evidence_requested() -> None:
    validator = ResponseValidator()
    issues = validator.validate(
        answer="This policy increases growth by 10%.",
        expected_language="en",
        citations=[],
        include_evidence=True,
        evidence_chunks=[],
    )
    assert any(issue.type == "missing_citations" for issue in issues)


def test_validator_detects_language_mismatch() -> None:
    validator = ResponseValidator()
    issues = validator.validate(
        answer="This answer is in English.",
        expected_language="ar",
        citations=[],
        include_evidence=False,
        evidence_chunks=[],
    )
    assert any(issue.type == "language_mismatch" for issue in issues)


def test_validator_detects_answer_evidence_conflict() -> None:
    validator = ResponseValidator()
    citations = [Citation(source_id="s1", chunk_id="c1", relevance_score=0.9)]
    evidence = [
        KnowledgeChunk(
            source_id="s1",
            chunk_id="c1",
            text="The policy is forbidden under current regulation.",
            relevance_score=0.9,
        )
    ]
    issues = validator.validate(
        answer="The policy is fully allowed and encouraged.",
        expected_language="en",
        citations=citations,
        include_evidence=True,
        evidence_chunks=evidence,
    )
    assert any(issue.type == "answer_evidence_conflict" for issue in issues)
