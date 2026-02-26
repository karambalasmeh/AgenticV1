import uuid

from app.core.config import settings
from app.schemas.query_models import QueryRequest, QueryResponse
from app.schemas.artifacts import Answer, Confidence, Validation, Escalation, Citation
from app.orchestration.decision_trace import trace
from app.orchestration.clarification import build_clarification_response
from app.llm.gateway import get_llm_gateway
from app.agents.assurance.validator import Validator
from app.orchestration.policies.confidence_rubric import ConfidenceRubric
from app.orchestration.escalation import EscalationEngine


validator_agent = Validator()
confidence_rubric = ConfidenceRubric()
escalation_engine = EscalationEngine()


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

    # Note: citations are empty until knowledge-service integration
    citations: list[Citation] = []

    # 3) Validation orchestration
    dt.append(trace("validate", "ValidationSuite", "Running deterministic assurance checks."))
    validation = validator_agent.run(draft, citations)

    # 4) Confidence scoring
    dt.append(trace("score_confidence", "ConfidenceRubric", "Scoring confidence deterministically."))
    confidence = confidence_rubric.score(
        answer_draft=draft,
        citations=citations,
        validation_issues=validation.issues,
        signals={"repair_attempts": 0},
    )

    # 5) Escalation decision
    escalation = escalation_engine.evaluate(validation=validation, confidence=confidence, signals={"repair_failures": 0})
    if escalation.triggered:
        dt.append(trace("escalate", "EscalationEngine", f"Escalation triggered ({escalation.reason})."))

    dt.append(trace("finalize", "Pipeline", "Finalizing response."))

    answer = Answer(
        format="structured",
        language="ar" if req.language == "ar" else "en",
        summary=draft[:200] if draft else "",
        sections=[{"title": "Answer", "content": draft}],
        actionable_points=[],
    )

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
