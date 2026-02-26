import uuid

from app.core.config import settings
from app.schemas.query_models import QueryRequest, QueryResponse
from app.schemas.artifacts import Answer, Confidence, Validation, Escalation, Citation
from app.orchestration.decision_trace import trace
from app.orchestration.clarification import build_clarification_response
from app.llm.gateway import get_llm_gateway


def run_query(req: QueryRequest) -> QueryResponse:
    # English comments only

    request_id = str(uuid.uuid4())
    dt = []

    # 1) Router (minimal heuristic for now)
    dt.append(trace("route", "RouterAgent", "Classifying intent/topic/complexity (placeholder)."))

    missing = _detect_missing_required_params(req)
    if missing:
        return build_clarification_response(req, request_id, missing)

    # 2) Specialist draft (placeholder using LLM gateway)
    dt.append(trace("analyze", "SpecialistAgent:Draft", "Generating a draft answer (placeholder)."))
    llm = get_llm_gateway()

    draft = llm.generate(
        prompt=f"Answer the question briefly with structure.\n\nQuestion: {req.question}",
        system="You are a government-grade assistant. Use structured response.",
    )

    # 3) Validate + citations present? (placeholder)
    dt.append(trace("validate", "SelfVerifier", "Running validation checks (placeholder)."))
    validation = Validation(passed=True, issues=[])

    # 4) Confidence scoring (placeholder)
    dt.append(trace("score_confidence", "ConfidenceScorer", "Scoring confidence (placeholder)."))
    confidence = Confidence(
        score=0.7,
        level="medium",
        rationale=["Placeholder scoring until rubric is implemented."],
        signals={"validation_passed": True},
    )

    # 5) Escalation decision (placeholder)
    escalation = Escalation(triggered=False, reason=None, ticket=None)
    dt.append(trace("finalize", "Pipeline", "Finalizing response."))

    answer = Answer(
        format="structured",
        language="ar" if req.language == "ar" else "en",
        summary=draft[:200] if draft else "",
        sections=[{"title": "Answer", "content": draft}],
        actionable_points=[],
    )

    # Note: citations are empty until knowledge-service integration
    citations: list[Citation] = []

    return QueryResponse(
        request_id=request_id,
        status="success",
        answer=answer,
        citations=citations,
        confidence=confidence,
        validation=validation,
        decision_trace=dt if req.output_controls.include_decision_trace else [],
        escalation=escalation,
    )


def _detect_missing_required_params(req: QueryRequest) -> list[str]:
    # English comments only
    # Example: require timeframe for monitoring_summary or comparison
    missing: list[str] = []

    if req.tasking.response_type in ("monitoring_summary", "comparison"):
        if not req.constraints.time_range or not (req.constraints.time_range.from_date and req.constraints.time_range.to_date):
            missing.append("time_range.from & time_range.to")

    # Example: require policy identifiers for comparison (placeholder)
    if req.tasking.response_type == "comparison":
        # No strict requirement now; keep it loose to avoid conflicts
        pass

    return missing