from fastapi import APIRouter
from pydantic import ValidationError

from app.schemas.confidence_models import ConfidenceRequest, ConfidenceResponse
from app.schemas.artifacts import Citation, ValidationIssue
from app.orchestration.policies.confidence_rubric import ConfidenceRubric

router = APIRouter()
confidence_rubric = ConfidenceRubric()


@router.post("/confidence", response_model=ConfidenceResponse)
def confidence(req: ConfidenceRequest) -> ConfidenceResponse:
    citations = _parse_citations(req.citations)
    signals = dict(req.signals or {})
    validation_issues = _extract_validation_issues(signals)

    scored = confidence_rubric.score(
        answer_draft=req.answer_draft,
        citations=citations,
        validation_issues=validation_issues,
        signals=signals,
    )

    return ConfidenceResponse(
        score=scored.score,
        level=scored.level,
        rationale=scored.rationale,
        signals=scored.signals,
    )


def _extract_validation_issues(signals: dict) -> list[ValidationIssue]:
    raw = signals.pop("validation_issues", None)
    if not raw:
        return []
    issues: list[ValidationIssue] = []
    for item in raw:
        try:
            issues.append(ValidationIssue(**item))
        except Exception:
            continue
    return issues


def _parse_citations(raw_list: list[dict]) -> list[Citation]:
    citations: list[Citation] = []
    for raw in raw_list:
        try:
            citations.append(Citation.model_validate(raw))
        except ValidationError:
            citations.append(
                Citation(
                    source_id=str(raw.get("source_id", "")),
                    chunk_id=str(raw.get("chunk_id", "")),
                    title=raw.get("title"),
                    publisher=raw.get("publisher"),
                    date=raw.get("date"),
                    relevance_score=float(raw.get("relevance_score", 0.0)),
                )
            )
    return citations
