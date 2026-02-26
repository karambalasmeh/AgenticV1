# app/llm/gateway.py
from app.core.config import settings
from app.llm.base import LLMProvider
from app.llm.providers.mock_provider import MockProvider
from app.llm.providers.vertex_gemini import VertexGeminiProvider


def get_llm_gateway() -> LLMProvider:
    # English comments only
    if settings.LLM_PROVIDER == "vertex":
        return VertexGeminiProvider(
            project_id=settings.VERTEX_PROJECT_ID,
            location=settings.VERTEX_LOCATION,
            model=settings.VERTEX_MODEL,
        )
    return MockProvider()