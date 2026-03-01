from __future__ import annotations

import uuid
from typing import List

from app.core.config import settings
from app.core.tracing import get_request_id
from app.llm.gateway import get_llm_gateway

from app.schemas.query_models import QueryRequest, QueryResponse
from app.schemas.artifacts import Answer, Confidence, Validation, Escalation, Citation

from app.orchestration.decision_trace import trace
from app.orchestration.clarification import build_clarification_response
from app.orchestration.repair_loop import run_with_repair
from app.orchestration.policies.basic_confidence import score_confidence

from app.agents.base import AgentContext, Artifacts
from app.agents.registry import AgentRegistry
from app.agents.router_agent import RouterAgent
from app.agents.delegation_engine import DelegationEngine

from app.agents.assurance.basic_validator import basic_validate
from app.agents.assurance.validator import Validator
from app.orchestration.policies.confidence_rubric import ConfidenceRubric
from app.orchestration.escalation import EscalationEngine

from app.agents.specialists.policy_explain_agent import PolicyExplainAgent
from app.agents.specialists.compare_agent import CompareAgent
from app.agents.specialists.merge_agent import MergeAgent
from app.agents.specialists.sector_explain_agent import SectorExplainAgent
from app.agents.specialists.risk_impact_agent import RiskImpactAgent

from app.utils.text import detect_language_from_text

# Global orchestration components

validator_agent = Validator()
confidence_rubric = ConfidenceRubric()
escalation_engine = EscalationEngine()


def run_query(req: QueryRequest) -> QueryResponse:
    # English comments only
    rid = get_request_id()
    request_id = rid if rid != "unknown" else str(uuid.uuid4())

    llm = get_llm_gateway()
    ctx = AgentContext(request_id=request_id, llm=llm, trace=[])

    # Decide response language:
    # - if user explicitly set ar/en -> honor it
    # - else auto -> detect from question
    response_lang = req.language if req.language in ("ar", "en") else detect_language_from_text(req.question)

    reg = _build_registry()

    router = RouterAgent()
    decision = router.route(req)

    ctx.trace.append(trace("route", "RouterAgent", f"intent={decision.intent}, topic={decision.topic}"))

    # Clarification scenario
    if decision.missing_params:
        return build_clarification_response(req, request_id, decision.missing_params)

    # Initial artifacts
    artifacts: Artifacts = {
        "question": req.question,
        "topic": decision.topic,
        "response_language": response_lang,  # IMPORTANT: let all agents/LLM use it
    }

    ctx.trace.append(trace("complexity_check", "RouterAgent", f"is_complex={decision.is_complex}"))

    # First run to produce initial draft
    artifacts = _run_specialists(ctx, artifacts, decision, reg)

    # Validation function used by the repair loop
    require_citations = getattr(settings, "REQUIRE_CITATIONS", False)

    def _validate_fn(draft: str, cits: list[Citation]):
        return basic_validate(draft, cits, require_citations)

    # Repair loop
    ctx.trace.append(trace("validate", "SelfVerifier", "Running validation with repair loop."))
    artifacts, valid_after_repair, issues, attempts = run_with_repair(
        ctx=ctx,
        artifacts=artifacts,
        run_specialists=lambda c, a: _run_specialists(c, a, decision, reg),
        validate=_validate_fn,
        max_attempts=2,
    )


    answer_draft = str(artifacts.get("answer_draft", "")).strip()

    # 3) Validation orchestration
    ctx.trace.append(trace("validate", "ValidationSuite", "Running deterministic assurance checks."))
    validation = validator_agent.run(answer_draft, raw_citations)

    # 4) Confidence scoring
    ctx.trace.append(trace("score_confidence", "ConfidenceRubric", f"Scoring confidence (attempts={attempts})."))
    confidence = confidence_rubric.score(
        answer_draft=answer_draft,
        citations=raw_citations,
        validation_issues=validation.issues,
        signals={"repair_attempts": attempts, "is_complex": decision.is_complex},
    )

    # 5) Escalation decision
    escalation = escalation_engine.evaluate(
        validation=validation,
        confidence=confidence,
        signals={"repair_failures": 0 if valid_after_repair else 1}
    )
    
    if escalation.triggered:
        ctx.trace.append(trace("escalate", "EscalationEngine", f"Escalation triggered ({escalation.reason})."))
        status = "needs_escalation"
    else:
        status = "success"

    # Decision trace output control
    decision_trace = ctx.trace if req.output_controls.include_decision_trace else []

    # Final answer packaging
    ctx.trace.append(trace("finalize", "Pipeline", "Returning final response."))
    
    # Evidence output control (citations filtered for final response)
    citations: list[Citation] = raw_citations if req.output_controls.include_evidence else []

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
        language=response_lang,
        summary=answer_draft[:200],
        sections=[{"title": "Answer", "content": answer_draft}],
        actionable_points=[],
    )

    return QueryResponse(
        request_id=request_id,
        status=status,
        answer=answer,
        citations=citations,
        confidence=confidence,
        validation=validation,
        decision_trace=decision_trace,
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
