from __future__ import annotations

from app.agents.base import AgentContext, Artifacts


class SectorExplainAgent:
    # English comments only
    name = "SectorExplainAgent"

    def run(self, ctx: AgentContext, artifacts: Artifacts) -> Artifacts:
        question = artifacts.get("question", "")
        sector = artifacts.get("sector", "general")

        draft = ctx.llm.generate(
            prompt=f"Explain the policy implications for the {sector} sector.\nQuestion: {question}\nReturn structured bullets.",
            system=f"You are a specialist government analyst for the {sector} sector. Be deep but concise.",
        )
        
        # Collect sector drafts for MergeAgent to use
        sector_drafts = artifacts.get("sector_drafts", [])
        sector_drafts.append(f"### {sector.capitalize()} Sector Analysis\n{draft}")
        artifacts["sector_drafts"] = sector_drafts
        
        # Set current draft (will be overwritten if multiple sectors run, then MergeAgent fixes it)
        artifacts["answer_draft"] = draft
        artifacts.setdefault("citations", [])
        return artifacts
