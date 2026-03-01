from __future__ import annotations

from app.agents.base import AgentContext, Artifacts


class CompareAgent:
    # English comments only
    name = "CompareAgent"

    def run(self, ctx: AgentContext, artifacts: Artifacts) -> Artifacts:
        question = artifacts.get("question", "")

        draft = ctx.llm.generate(
            prompt=f"Compare the policies mentioned in the question.\nQuestion: {question}\nReturn a structured comparison table.",
            system="You are a government-grade policy comparison assistant. Use structured output.",
        )
        artifacts["answer_draft"] = draft
        artifacts.setdefault("citations", [])
        return artifacts