from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass

from app.application.language import detect_language, language_instruction
from app.application.router import RouteDecision, Router
from app.domain.contracts import AuditLogRequest, GuardrailCheckRequest, KnowledgeChunk, TicketCreateRequest
from app.domain.models import (
    Citation,
    Confidence,
    DecisionTraceStep,
    Escalation,
    EscalationTicket,
    MinistryClassification,
    OutputLanguage,
    QueryRequest,
    QueryResponse,
    Validation,
)
from app.infrastructure.clients import IntegrationClients
from app.infrastructure.llm import LLMProvider
from app.infrastructure.persistence.repository import PersistencePayload, PersistenceRepository

logger = logging.getLogger(__name__)

PROHIBITED_KEYWORDS = {
    "weapons": ("weapon", "explosive", "gun", "bomb", "سلاح", "متفجر"),
    "sexual": ("porn", "sexual", "explicit", "اباحي", "إباحي"),
}


@dataclass
class QueryExecution:
    response: QueryResponse
    persistence_payload: PersistencePayload


class OrchestrationService:
    def __init__(
        self,
        *,
        llm: LLMProvider,
        integrations: IntegrationClients,
        repository: PersistenceRepository,
        router: Router,
        validator,
        confidence_scorer,
        escalation_engine,
        ministry_classifier,
    ) -> None:
        self.llm = llm
        self.integrations = integrations
        self.repository = repository
        self.router = router
        self.validator = validator
        self.confidence_scorer = confidence_scorer
        self.escalation_engine = escalation_engine
        self.ministry_classifier = ministry_classifier

    async def execute_query(self, req: QueryRequest) -> QueryExecution:
        started = time.perf_counter()
        request_id = str(uuid.uuid4())
        trace: list[DecisionTraceStep] = []
        fallback_used = False

        trace.append(self._trace("request_received", "OrchestrationService", "Accepted query request."))

        language: OutputLanguage = req.language if req.language in {"ar", "en"} else detect_language(req.question)
        user_id = req.user_id or "anonymous"
        conversation_id = req.conversation_id or "default"

        local_violation_reason = self._local_guardrail_violation(req.question)
        if local_violation_reason:
            current_count = self.repository.increment_violation(user_id, local_violation_reason)
            trace.append(
                self._trace(
                    "local_guardrail",
                    "Guardrail",
                    f"Local guardrail matched `{local_violation_reason}` (count={current_count}).",
                )
            )
            if current_count >= 3:
                response = self._refusal_response(
                    request_id=request_id,
                    language=language,
                    trace=trace,
                    reason="repeated_prohibited_content",
                )
                payload = self._build_payload(
                    req=req,
                    response=response,
                    trace=trace,
                    started=started,
                    result="blocked",
                    fallback_used=fallback_used,
                    policy_flags={"local_violation": local_violation_reason, "repeat_violations": True},
                )
                return QueryExecution(response=response, persistence_payload=payload)

        guardrail_result = await self.integrations.guardrail_check(
            GuardrailCheckRequest(content=req.question, check_types=req.check_types)
        )
        fallback_used = fallback_used or guardrail_result.used_fallback
        governance = guardrail_result.data
        trace.append(self._trace("governance_check", "GovernanceClient", "Guardrail check completed."))
        if governance.blocked or not governance.allowed:
            current_count = self.repository.increment_violation(user_id, ",".join(governance.violations or ["blocked"]))
            response = self._refusal_response(
                request_id=request_id,
                language=language,
                trace=trace,
                reason="governance_block",
            )
            payload = self._build_payload(
                req=req,
                response=response,
                trace=trace,
                started=started,
                result="blocked",
                fallback_used=fallback_used,
                policy_flags={"governance_block": True, "violations": governance.violations, "count": current_count},
            )
            return QueryExecution(response=response, persistence_payload=payload)

        route = self.router.route(req)
        trace.append(
            self._trace(
                "routing",
                "Router",
                f"intent={route.intent}, topic={route.topic}, complexity={route.complexity}",
            )
        )

        evidence: list[KnowledgeChunk] = []
        missing_evidence = False
        retrieval = None
        if route.retrieve_evidence:
            retrieval = await self.integrations.retrieve(req.question, req.max_chunks)
            fallback_used = fallback_used or retrieval.used_fallback
            evidence = retrieval.data.chunks
            trace.append(
                self._trace(
                    "retrieval",
                    "KnowledgeClient",
                    f"Retrieved {len(evidence)} chunk(s).",
                    {"fallback": retrieval.used_fallback},
                )
            )
            if req.require_evidence and not evidence:
                missing_evidence = True

        evidence_summary = self._summarize_evidence(evidence)
        drafts = await self._run_specialists(req.question, route, language, evidence_summary)
        answer = await self._merge_drafts(req.question, route, language, drafts, evidence_summary)

        citations = self._build_citations(evidence)
        validation_issues = self.validator.validate(
            answer=answer,
            expected_language=language,
            citations=citations,
            include_evidence=req.output_controls.include_evidence or req.require_evidence,
            evidence_chunks=evidence,
        )
        repair_attempts = 0
        max_repairs = 2
        while validation_issues and repair_attempts < max_repairs:
            repair_attempts += 1
            answer = await self._repair_answer(
                answer=answer,
                issues=validation_issues,
                language=language,
                evidence_summary=evidence_summary,
            )
            validation_issues = self.validator.validate(
                answer=answer,
                expected_language=language,
                citations=citations,
                include_evidence=req.output_controls.include_evidence or req.require_evidence,
                evidence_chunks=evidence,
            )
        trace.append(self._trace("validation", "Validator", f"Validation issues={len(validation_issues)}."))

        validation = Validation(passed=not validation_issues, issues=validation_issues)
        confidence: Confidence = self.confidence_scorer.score(
            answer=answer,
            citations=citations,
            validation_issues=validation_issues,
            signals={
                "repair_attempts": repair_attempts,
                "missing_evidence": missing_evidence,
                "complexity": route.complexity,
            },
        )
        trace.append(self._trace("confidence", "ConfidenceScorer", f"score={confidence.score:.2f}"))

        escalation: Escalation = self.escalation_engine.evaluate(
            confidence=confidence,
            validation_issues=validation_issues,
            signals={
                "repeat_violations": self.repository.get_violation_count(user_id) >= 3,
                "evidence_missing_when_required": missing_evidence,
                "policy_uncertainty": route.topic == "general" and route.complexity == "high",
            },
        )
        ministry: MinistryClassification | None = None
        ticket_payload: dict | None = None
        if escalation.triggered:
            ministry = await self.ministry_classifier.classify(req.question, language)
            ticket_result = await self.integrations.create_ticket(
                TicketCreateRequest(
                    title=f"Escalation for request {request_id}",
                    description=req.question,
                    ministry=ministry.model_dump(),
                    payload={
                        "request_id": request_id,
                        "question": req.question,
                        "confidence_reasons": confidence.reasons,
                        "validation_issues": [issue.model_dump() for issue in validation_issues],
                        "evidence_pack": [chunk.model_dump() for chunk in evidence],
                        "decision_trace": [step.model_dump() for step in trace],
                        "user_context": {
                            "user_id": user_id,
                            "conversation_id": conversation_id,
                        },
                    },
                )
            )
            fallback_used = fallback_used or ticket_result.used_fallback
            ticket = ticket_result.data
            escalation.ticket = EscalationTicket(ticket_id=ticket.ticket_id, status=ticket.status)
            trace.append(self._trace("ticket", "WorkflowClient", f"ticket={ticket.ticket_id}"))
            ticket_payload = {
                "ticket_id": ticket.ticket_id,
                "status": ticket.status,
                "ministry": ministry.ministry_name,
                "payload": {
                    "confidence_reasons": confidence.reasons,
                    "validation_issues": [issue.model_dump() for issue in validation_issues],
                    "evidence_pack": [chunk.model_dump() for chunk in evidence],
                    "decision_trace": [step.model_dump() for step in trace],
                },
            }

        answer_only_mode = (
            "output_controls" not in req.model_fields_set
            and not req.output_controls.include_evidence
            and not req.output_controls.include_decision_trace
            and not req.output_controls.include_confidence
            and not req.output_controls.include_validation_report
        )

        citations_output = None
        trace_output = None
        confidence_output = None
        validation_output = None
        validation_issues_output = None
        escalation_output = None
        status_output = None
        language_output = None

        if not answer_only_mode:
            citations_output = citations if req.output_controls.include_evidence else []
            trace_output = trace if req.output_controls.include_decision_trace else []
            confidence_output = confidence if req.output_controls.include_confidence else None
            validation_output = validation if req.output_controls.include_validation_report else None
            validation_issues_output = validation_issues if req.output_controls.include_validation_report else []
            escalation_output = escalation
            status_output = "needs_escalation" if escalation.triggered else "success"
            language_output = language

        response = QueryResponse(
            request_id=request_id,
            answer=answer,
            status=status_output,
            language=language_output,
            citations=citations_output,
            confidence=confidence_output,
            validation=validation_output,
            validation_issues=validation_issues_output,
            decision_trace=trace_output,
            trace=trace_output,
            escalation=escalation_output,
            ministry=ministry if not answer_only_mode else None,
        )

        payload = self._build_payload(
            req=req,
            response=response,
            trace=trace,
            started=started,
            result="escalated" if escalation.triggered else "ok",
            fallback_used=fallback_used,
            policy_flags={
                "local_violation": bool(local_violation_reason),
                "missing_evidence": missing_evidence,
                "governance_fallback": guardrail_result.used_fallback,
            },
            ticket_payload=ticket_payload,
            citations=[citation.model_dump() for citation in citations],
            evidence=[chunk.model_dump() for chunk in evidence],
            confidence=confidence.model_dump(),
            validation_issues=[issue.model_dump() for issue in validation_issues],
        )
        await self.integrations.send_audit(
            AuditLogRequest(
                request_id=request_id,
                event="query_processed",
                payload={
                    "result": payload.result,
                    "latency_ms": payload.latency_ms,
                    "fallback_used": payload.fallback_used,
                },
            )
        )
        return QueryExecution(response=response, persistence_payload=payload)

    async def persist_execution(self, payload: PersistencePayload) -> None:
        try:
            self.repository.persist_query(payload)
        except Exception as exc:
            logger.exception("Background persistence failed: %s", exc)

    async def _run_specialists(
        self,
        question: str,
        route: RouteDecision,
        language: OutputLanguage,
        evidence_summary: str,
    ) -> list[str]:
        prompt_template = (
            "Question: {question}\n"
            "Intent: {intent}\n"
            "Topic: {topic}\n"
            "Evidence summary:\n{evidence}\n"
            "Provide a policy-focused answer section."
        )
        system = f"You are a specialist policy agent. {language_instruction(language)}"
        prompts = [
            prompt_template.format(
                question=question,
                intent=route.intent,
                topic=route.topic,
                evidence=evidence_summary or "No evidence provided.",
            )
            + f"\nSpecialist role: {specialist}"
            for specialist in route.specialists
        ]
        if len(prompts) == 1:
            return [await self.llm.generate(system_prompt=system, user_prompt=prompts[0], temperature=0.2)]
        return await asyncio.gather(
            *[
                self.llm.generate(system_prompt=system, user_prompt=prompt, temperature=0.2)
                for prompt in prompts
            ]
        )

    async def _merge_drafts(
        self,
        question: str,
        route: RouteDecision,
        language: OutputLanguage,
        drafts: list[str],
        evidence_summary: str,
    ) -> str:
        if len(drafts) == 1:
            return drafts[0].strip()
        merge_prompt = (
            f"Question: {question}\nIntent: {route.intent}\n"
            "Combine the following specialist outputs into one coherent answer:\n"
            + "\n\n".join(f"- Draft {idx + 1}: {text}" for idx, text in enumerate(drafts))
            + f"\nEvidence summary:\n{evidence_summary}\n"
        )
        return (
            await self.llm.generate(
                system_prompt=f"You are a merge agent. {language_instruction(language)}",
                user_prompt=merge_prompt,
                temperature=0.1,
                max_tokens=700,
            )
        ).strip()

    async def _repair_answer(
        self,
        *,
        answer: str,
        issues,
        language: OutputLanguage,
        evidence_summary: str,
    ) -> str:
        issue_lines = "\n".join(f"- {issue.type}: {issue.details}" for issue in issues)
        prompt = (
            "Rewrite the answer and fix all issues.\n"
            f"Issues:\n{issue_lines}\n"
            f"Current draft:\n{answer}\n"
            f"Evidence summary:\n{evidence_summary}\n"
        )
        return await self.llm.generate(
            system_prompt=f"You are a strict repair assistant. {language_instruction(language)}",
            user_prompt=prompt,
            temperature=0.0,
            max_tokens=700,
        )

    def _refusal_response(
        self,
        *,
        request_id: str,
        language: OutputLanguage,
        trace: list[DecisionTraceStep],
        reason: str,
    ) -> QueryResponse:
        message = (
            "لا أستطيع المساعدة في هذا الطلب لأنه يتضمن محتوى غير مسموح."
            if language == "ar"
            else "I cannot help with this request because it contains disallowed content."
        )
        return QueryResponse(
            request_id=request_id,
            answer=message,
            status="blocked",
            language=language,
            citations=[],
            confidence=None,
            validation=None,
            validation_issues=[],
            decision_trace=trace,
            trace=trace,
            escalation=Escalation(triggered=False, reason=reason),
        )

    def _local_guardrail_violation(self, question: str) -> str | None:
        lowered = question.lower()
        for category, terms in PROHIBITED_KEYWORDS.items():
            if any(term in lowered for term in terms):
                return category
        return None

    def _summarize_evidence(self, chunks: list[KnowledgeChunk]) -> str:
        if not chunks:
            return ""
        lines = []
        for chunk in chunks[:3]:
            snippet = " ".join(chunk.text.split())[:220]
            lines.append(f"[{chunk.source_id}/{chunk.chunk_id}] {snippet}")
        return "\n".join(lines)

    def _build_citations(self, chunks: list[KnowledgeChunk]) -> list[Citation]:
        citations: list[Citation] = []
        for chunk in chunks:
            citations.append(
                Citation(
                    source_id=chunk.source_id,
                    chunk_id=chunk.chunk_id,
                    relevance_score=chunk.relevance_score,
                    text=chunk.text[:240],
                    metadata=chunk.metadata,
                )
            )
        return citations

    def _build_payload(
        self,
        *,
        req: QueryRequest,
        response: QueryResponse,
        trace: list[DecisionTraceStep],
        started: float,
        result: str,
        fallback_used: bool,
        policy_flags: dict,
        ticket_payload: dict | None = None,
        citations: list[dict] | None = None,
        evidence: list[dict] | None = None,
        confidence: dict | None = None,
        validation_issues: list[dict] | None = None,
    ) -> PersistencePayload:
        latency_ms = int((time.perf_counter() - started) * 1000)
        answer_text = response.answer if isinstance(response.answer, str) else response.answer.summary
        response_citations = response.citations or []
        return PersistencePayload(
            request_id=response.request_id,
            user_id=req.user_id or "anonymous",
            conversation_id=req.conversation_id or "default",
            route="/api/v1/query",
            latency_ms=latency_ms,
            result=result,
            policy_flags=policy_flags,
            question=req.question,
            answer=answer_text,
            language=response.language or "en",
            decision_trace=[step.model_dump() for step in trace],
            confidence=confidence or (response.confidence.model_dump() if response.confidence else {}),
            citations=citations or [citation.model_dump() for citation in response_citations],
            evidence_refs=evidence or [],
            validation_issues=validation_issues or [],
            explanation={},
            ticket=ticket_payload,
            fallback_used=fallback_used,
        )

    @staticmethod
    def _trace(step: str, component: str, reason: str, metadata: dict | None = None) -> DecisionTraceStep:
        return DecisionTraceStep(step=step, component=component, reason=reason, metadata=metadata or {})
