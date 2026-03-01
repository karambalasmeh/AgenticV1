from fastapi import APIRouter, Depends

from app.api.dependencies import get_container
from app.domain.models import ExplainDecisionRequest, ExplainDecisionResponse
from app.infrastructure.bootstrap import ServiceContainer

router = APIRouter()


@router.post("/explain_decision", response_model=ExplainDecisionResponse)
async def explain_decision(
    req: ExplainDecisionRequest,
    container: ServiceContainer = Depends(get_container),
) -> ExplainDecisionResponse:
    return container.explainer.explain(req)
