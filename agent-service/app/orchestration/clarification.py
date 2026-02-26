from datetime import datetime, timezone

from app.schemas.query_models import QueryRequest, QueryResponse
from app.schemas.artifacts import Answer, Confidence, Validation, Escalation
from app.orchestration.decision_trace import trace


def build_clarification_response(req: QueryRequest, request_id: str, missing: list[str]) -> QueryResponse:
    # English comments only
    answer = Answer(
        format="structured",
        language="ar" if req.language == "ar" else "en",
        summary="Clarification required.",
        sections=[
            {
                "title": "Missing parameters",
                "content": f"Please provide: {', '.join(missing)}",
            }
        ],
        actionable_points=[],
    )

    return QueryResponse(
        request_id=request_id,
        status="failed",
        answer=answer,
        citations=[],
        confidence=Confidence(score=0.0, level="low", rationale=["Missing required parameters."], signals={}),
        validation=Validation(passed=False, issues=[]),
        decision_trace=[
            trace("route", "RouterAgent", "Detected missing required parameters."),
            trace("clarify", "ClarificationModule", "Returning clarification request."),
        ],
        escalation=Escalation(triggered=False, reason=None, ticket=None),
    )