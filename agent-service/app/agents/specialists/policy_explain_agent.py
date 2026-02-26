from __future__ import annotations

from app.agents.base import AgentContext, Artifacts


class PolicyExplainAgent:
    # English comments only
    name = "PolicyExplainAgent"

    def run(self, ctx: AgentContext, artifacts: Artifacts) -> Artifacts:
        question = artifacts.get("question", "")
        topic = artifacts.get("topic", "general")

        draft = ctx.llm.generate(
            prompt=f"Explain the policy topic: {topic}\nQuestion: {question}\nReturn structured bullets.",
            system="You are a government-grade policy analyst. Be concise and structured.",
        )
        artifacts["answer_draft"] = draft
        artifacts.setdefault("citations", [])  # will be filled later by tools integration
        return artifacts