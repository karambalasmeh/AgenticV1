from __future__ import annotations

from dataclasses import dataclass

from app.application import (
    ConfidenceScorer,
    DecisionExplainer,
    DelegationService,
    EscalationEngine,
    MinistryClassifier,
    OrchestrationService,
    ResponseValidator,
    Router,
)
from app.core.config import settings
from app.infrastructure.clients import IntegrationClients
from app.infrastructure.llm import LLMProvider, MockLLMProvider, VertexGeminiProvider
from app.infrastructure.persistence.repository import PersistenceRepository


@dataclass
class ServiceContainer:
    llm: LLMProvider
    integrations: IntegrationClients
    repository: PersistenceRepository
    router: Router
    validator: ResponseValidator
    confidence: ConfidenceScorer
    escalation: EscalationEngine
    classifier: MinistryClassifier
    orchestration: OrchestrationService
    delegation: DelegationService
    explainer: DecisionExplainer


def _build_llm() -> LLMProvider:
    if settings.LLM_PROVIDER.lower() == "vertex":
        return VertexGeminiProvider(
            project_id=settings.VERTEX_PROJECT_ID,
            location=settings.VERTEX_LOCATION,
            model=settings.VERTEX_MODEL,
        )
    return MockLLMProvider()


def build_container() -> ServiceContainer:
    llm = _build_llm()
    integrations = IntegrationClients(
        use_mocks=settings.USE_MOCK_SERVICES,
        knowledge_base_url=settings.KNOWLEDGE_SERVICE_URL,
        governance_base_url=settings.GOVERNANCE_SERVICE_URL,
        workflow_base_url=settings.WORKFLOW_SERVICE_URL,
        timeout_s=settings.CLIENT_TIMEOUT_S,
        retries=settings.CLIENT_RETRIES,
    )
    repository = PersistenceRepository()
    router = Router()
    validator = ResponseValidator()
    confidence = ConfidenceScorer()
    escalation = EscalationEngine()
    classifier = MinistryClassifier(llm_provider=llm)
    orchestration = OrchestrationService(
        llm=llm,
        integrations=integrations,
        repository=repository,
        router=router,
        validator=validator,
        confidence_scorer=confidence,
        escalation_engine=escalation,
        ministry_classifier=classifier,
    )
    delegation = DelegationService(router=router)
    explainer = DecisionExplainer()
    return ServiceContainer(
        llm=llm,
        integrations=integrations,
        repository=repository,
        router=router,
        validator=validator,
        confidence=confidence,
        escalation=escalation,
        classifier=classifier,
        orchestration=orchestration,
        delegation=delegation,
        explainer=explainer,
    )
