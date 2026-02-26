from fastapi import APIRouter
from app.schemas.explain_models import ExplainDecisionRequest, ExplainDecisionResponse

router = APIRouter()


@router.post("/explain_decision", response_model=ExplainDecisionResponse)
def explain_decision(req: ExplainDecisionRequest) -> ExplainDecisionResponse:
    # Placeholder: will be derived from decision_trace later
    return ExplainDecisionResponse(
        summary="Decision explanation placeholder.",
        explanation=[],
        audit_tags=[],
    )