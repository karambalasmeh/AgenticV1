from __future__ import annotations

from app.agents.base import AgentContext, Artifacts


class MergeAgent:
    # English comments only
    name = "MergeAgent"

    def run(self, ctx: AgentContext, artifacts: Artifacts) -> Artifacts:
        sector_drafts = artifacts.get("sector_drafts", [])
        risk_draft = artifacts.get("risk_draft", "")

        parts = []

        # Merge sector analyses
        if sector_drafts:
            parts.append("# Sector Analyses\n" + "\n\n".join(sector_drafts))

        # Append risk/impact section if present
        if risk_draft:
            parts.append("# Risk & Impact Assessment\n" + risk_draft)

        merged = "\n\n".join(parts).strip()

        # Final output draft
        artifacts["answer_draft"] = merged if merged else artifacts.get("answer_draft", "")
        return artifacts    