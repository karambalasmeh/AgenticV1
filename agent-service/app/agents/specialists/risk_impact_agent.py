from __future__ import annotations

from app.agents.base import AgentContext, Artifacts


class RiskImpactAgent:
    # English comments only
    name = "RiskImpactAgent"

    def run(self, ctx: AgentContext, artifacts: Artifacts) -> Artifacts:
        question = artifacts.get("question", "")
        topic = artifacts.get("topic", "general")

        draft = ctx.llm.generate(
            prompt=(
                "Perform a risk and impact assessment for the following policy question.\n"
                f"Question: {question}\n"
                f"Topic: {topic}\n"
                "Return a structured risk matrix with: Risk, Likelihood, Impact, Mitigation."
            ),
            system="You are a government-grade risk assessment specialist. Focus on policy impact and unintended consequences.",
        )

        # Store separately to avoid overwriting sector/merge drafts
        artifacts["risk_draft"] = draft
        artifacts.setdefault("citations", [])
        return artifacts