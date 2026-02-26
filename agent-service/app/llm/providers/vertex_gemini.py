# app/llm/providers/vertex_gemini.py
from app.llm.base import LLMProvider


class VertexGeminiProvider(LLMProvider):
    # English comments only
    def __init__(self, project_id: str, location: str, model: str):
        self.project_id = project_id
        self.location = location
        self.model = model

    def generate(self, prompt: str, system: str = "") -> str:
        # Lazy import to keep dependency optional
        try:
            import vertexai
            from vertexai.generative_models import GenerativeModel
        except Exception as e:
            raise RuntimeError(
                "Vertex dependencies not installed. Install with: pip install google-cloud-aiplatform"
            ) from e

        if not self.project_id:
            raise RuntimeError("VERTEX_PROJECT_ID is required when LLM_PROVIDER=vertex")

        vertexai.init(project=self.project_id, location=self.location)
        model = GenerativeModel(self.model)

        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        resp = model.generate_content(full_prompt)
        return getattr(resp, "text", "") or ""