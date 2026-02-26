# app/llm/providers/mock_provider.py
from app.llm.base import LLMProvider


class MockProvider(LLMProvider):
    # English comments only
    def generate(self, prompt: str, system: str = "") -> str:
        return (
            "Mock answer (deterministic).\n"
            "- Point 1\n"
            "- Point 2\n"
            "Citations: [pending integration]"
        )