import pytest

from app.application.confidence import ConfidenceScorer
from app.application.escalation import EscalationEngine
from app.application.ministry_classifier import MinistryClassifier
from app.application.orchestration_service import OrchestrationService
from app.application.router import Router
from app.application.validation import ResponseValidator
from app.domain.contracts import GuardrailCheckResponse, RetrieveResponse, TicketCreateResponse
from app.domain.models import QueryRequest
from app.infrastructure.clients import IntegrationResult
from app.infrastructure.llm import MockLLMProvider


class _NoEvidenceIntegrations:
    async def guardrail_check(self, request):
        return IntegrationResult(data=GuardrailCheckResponse(allowed=True, blocked=False, violations=[], risk_score=0.0))

    async def retrieve(self, query: str, top_k: int):
        return IntegrationResult(data=RetrieveResponse(chunks=[]))

    async def create_ticket(self, request):
        return IntegrationResult(data=TicketCreateResponse(ticket_id="T-1", status="open"))

    async def send_audit(self, request):
        return IntegrationResult(data={"success": True})


class _MemoryRepo:
    def __init__(self) -> None:
        self.count = 0

    def increment_violation(self, user_id: str, reason: str) -> int:
        self.count += 1
        return self.count

    def get_violation_count(self, user_id: str) -> int:
        return self.count

    def persist_query(self, payload):
        return None


@pytest.mark.asyncio
async def test_repair_loop_runs_and_escalates_when_evidence_required() -> None:
    service = OrchestrationService(
        llm=MockLLMProvider(),
        integrations=_NoEvidenceIntegrations(),
        repository=_MemoryRepo(),
        router=Router(),
        validator=ResponseValidator(),
        confidence_scorer=ConfidenceScorer(),
        escalation_engine=EscalationEngine(),
        ministry_classifier=MinistryClassifier(llm_provider=MockLLMProvider()),
    )
    request = QueryRequest(
        user_id="repair-user",
        conversation_id="repair-conv",
        question="Provide policy update on education reform.",
        require_evidence=True,
        output_controls={"include_evidence": True, "include_confidence": True},
    )

    execution = await service.execute_query(request)
    response = execution.response

    assert response.status == "needs_escalation"
    assert response.confidence is not None
    assert response.confidence.signals["repair_attempts"] == 2
    assert response.escalation.triggered is True
