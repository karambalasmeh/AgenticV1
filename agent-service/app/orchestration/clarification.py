from datetime import datetime, timezone

from app.schemas.query_models import QueryRequest, QueryResponse
from app.schemas.artifacts import Answer, Confidence, Validation, Escalation
from app.orchestration.decision_trace import trace
from app.utils.text import detect_language_from_text


def build_clarification_response(req: QueryRequest, request_id: str, missing: list[str]) -> QueryResponse:
    # English comments only

    response_lang = req.language if req.language in ("ar", "en") else detect_language_from_text(req.question)

    answer = Answer(
        format="structured",
        language=response_lang,
        summary="Clarification required.",
        sections=[
            {
                "title": "Missing parameters",
                "content": f"Please provide: {', '.join(missing)}",
            }
        ],
        actionable_points=[],
    )

    decision_trace = []
    if req.output_controls.include_decision_trace:
        decision_trace = [
            trace("route", "RouterAgent", "Detected missing required parameters."),
            trace("clarify", "ClarificationModule", "Returning clarification request."),
        ]

    # Respect include_validation_report (keep passed flag, hide details if requested)
    validation_issues = []  # clarification is failed anyway; keep issues empty unless you want to expose details later
    validation = Validation(passed=False, issues=validation_issues)

    return QueryResponse(
        request_id=request_id,
        status="failed",
        answer=answer,
        citations=[],  # clarification doesn't return evidence
        confidence=Confidence(score=0.0, level="low", rationale=["Missing required parameters."], signals={}),
        validation=validation,
        decision_trace=decision_trace,
        escalation=Escalation(triggered=False, reason=None, ticket=None),
    )