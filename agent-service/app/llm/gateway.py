from app.core.config import settings
from app.infrastructure.clients import IntegrationClients
from app.infrastructure.llm import LLMProvider, MockLLMProvider, VertexGeminiProvider


def get_llm_gateway() -> LLMProvider:
    if settings.LLM_PROVIDER.lower() == "vertex":
        return VertexGeminiProvider(
            project_id=settings.VERTEX_PROJECT_ID,
            location=settings.VERTEX_LOCATION,
            model=settings.VERTEX_MODEL,
        )
    return MockLLMProvider()


def get_integration_clients() -> IntegrationClients:
    return IntegrationClients(
        use_mocks=settings.USE_MOCK_SERVICES,
        knowledge_base_url=settings.KNOWLEDGE_SERVICE_URL,
        governance_base_url=settings.GOVERNANCE_SERVICE_URL,
        workflow_base_url=settings.WORKFLOW_SERVICE_URL,
        timeout_s=settings.CLIENT_TIMEOUT_S,
        retries=settings.CLIENT_RETRIES,
    )
