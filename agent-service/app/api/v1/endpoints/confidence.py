from fastapi import APIRouter, Depends

from app.api.dependencies import get_container
from app.domain.models import ConfidenceRequest, ConfidenceResponse
from app.infrastructure.bootstrap import ServiceContainer

router = APIRouter()


@router.post("/confidence", response_model=ConfidenceResponse)
async def confidence(req: ConfidenceRequest, container: ServiceContainer = Depends(get_container)) -> ConfidenceResponse:
    scored = container.confidence.score(
        answer=req.answer_draft,
        citations=req.citations,
        validation_issues=req.validation_issues,
        signals=req.signals,
    )
    return ConfidenceResponse(
        score=scored.score,
        level=scored.level,
        rationale=scored.rationale,
        reasons=scored.reasons,
        signals=scored.signals,
    )
