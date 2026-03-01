from fastapi import APIRouter, Depends

from app.api.dependencies import get_container
from app.application.language import detect_language
from app.domain.models import ValidateRequest, ValidateResponse
from app.infrastructure.bootstrap import ServiceContainer

router = APIRouter()


@router.post("/validate", response_model=ValidateResponse)
async def validate(req: ValidateRequest, container: ServiceContainer = Depends(get_container)) -> ValidateResponse:
    language = req.language if req.language in {"ar", "en"} else detect_language(req.answer_draft)
    issues = container.validator.validate(
        answer=req.answer_draft,
        expected_language=language,
        citations=req.citations,
        include_evidence=req.require_evidence,
        evidence_chunks=[],
    )
    return ValidateResponse(
        valid=not issues,
        issues=issues,
        recommended_actions=container.validator.recommend_actions(issues),
        escalation_recommended=any(issue.severity in {"high", "medium"} for issue in issues),
    )
