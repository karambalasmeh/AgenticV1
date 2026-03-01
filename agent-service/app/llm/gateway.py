# app/llm/gateway.py
from app.core.config import settings
from app.llm.base import LLMProvider
from app.llm.providers.mock_provider import MockProvider
from app.llm.providers.vertex_gemini import VertexGeminiProvider
from app.core.config import settings
from app.tools.knowledge_client import KnowledgeClient
from app.tools.workflow_client import WorkflowClient
from app.tools.governance_client import GovernanceClient
from app.tools.mocks.knowledge_mock import MockKnowledgeClient
from app.tools.mocks.workflow_mock import MockWorkflowClient
from app.tools.mocks.governance_mock import MockGovernanceClient


def get_llm_gateway() -> LLMProvider:
    # English comments only
    if settings.LLM_PROVIDER == "vertex":
        return VertexGeminiProvider(
            project_id=settings.VERTEX_PROJECT_ID,
            location=settings.VERTEX_LOCATION,
            model=settings.VERTEX_MODEL,
        )
    return MockProvider()



def get_knowledge_client(scenario: str = "SUCCESS_EVIDENCE"):
    # English comments only
    if settings.ENV == "test" or settings.LLM_PROVIDER == "mock":
        return MockKnowledgeClient(scenario=scenario)
    return KnowledgeClient(base_url=settings.KNOWLEDGE_SERVICE_URL)


def get_workflow_client(scenario: str = "SUCCESS_EVIDENCE"):
    # English comments only
    if settings.ENV == "test" or settings.LLM_PROVIDER == "mock":
        return MockWorkflowClient(scenario=scenario)
    return WorkflowClient(base_url=settings.WORKFLOW_SERVICE_URL)


def get_governance_client(scenario: str = "SUCCESS_EVIDENCE"):
    # English comments only
    if settings.ENV == "test" or settings.LLM_PROVIDER == "mock":
        return MockGovernanceClient(scenario=scenario)
    return GovernanceClient(base_url=settings.GOVERNANCE_SERVICE_URL)
