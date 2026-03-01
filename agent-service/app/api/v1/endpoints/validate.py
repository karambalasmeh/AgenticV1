from fastapi import APIRouter

from app.schemas.validate_models import ValidateRequest, ValidateResponse
from app.agents.assurance.validator import Validator

router = APIRouter()
validator_agent = Validator()


@router.post("/validate", response_model=ValidateResponse)
def validate(req: ValidateRequest) -> ValidateResponse:
    result = validator_agent.run(req.answer_draft, req.citations)
    recommended_actions = validator_agent.recommend_actions(result.issues)
    escalation_recommended = any(issue.severity == "high" for issue in result.issues)

    return ValidateResponse(
        valid=result.passed,
        issues=result.issues,
        recommended_actions=recommended_actions,
        escalation_recommended=escalation_recommended,
    )
