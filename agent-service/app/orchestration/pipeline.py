from __future__ import annotations

import uuid

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

from app.agents.specialists.policy_explain_agent import PolicyExplainAgent
from app.agents.specialists.compare_agent import CompareAgent
from app.agents.specialists.merge_agent import MergeAgent
from app.agents.specialists.sector_explain_agent import SectorExplainAgent
from app.agents.specialists.risk_impact_agent import RiskImpactAgent

from app.utils.text import detect_language_from_text


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

    # Evidence output control
    raw_citations: list[Citation] = artifacts.get("citations", []) or []
    citations: list[Citation] = raw_citations if req.output_controls.include_evidence else []

    # Validation output control
    validation_issues = issues if req.output_controls.include_validation_report else []
    validation = Validation(passed=valid_after_repair, issues=validation_issues)

    # Confidence scoring
    ctx.trace.append(trace("score_confidence", "ConfidenceScorer", f"attempts={attempts}"))
    score, level, rationale, signals = score_confidence(
        valid=valid_after_repair,
        issues=issues,
        is_complex=decision.is_complex,
        citations_count=len(citations),
    )
    confidence = Confidence(score=score, level=level, rationale=rationale, signals=signals)

    # Escalation decision
    escalation = Escalation(triggered=False, reason=None, ticket=None)
    if (not valid_after_repair) or (confidence.level == "low"):
        ctx.trace.append(trace("escalate", "EscalationTrigger", "Escalation due to low confidence or invalid output."))
        escalation = Escalation(triggered=True, reason="low_confidence_or_invalid", ticket=None)
        status = "needs_escalation"
    else:
        status = "success"

    # Decision trace output control
    decision_trace = ctx.trace if req.output_controls.include_decision_trace else []

    # Final answer packaging
    ctx.trace.append(trace("finalize", "Pipeline", "Returning final response."))
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