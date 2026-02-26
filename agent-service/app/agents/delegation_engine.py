from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class SubTask:
    # English comments only
    agent: str
    action: str
    inputs: Dict[str, Any]


class DelegationEngine:
    # English comments only
    name = "DelegationEngine"

    def build_plan(self, intent: str, topic: str, question: str) -> List[SubTask]:
        q = (question or "").lower()

        if intent == "compare":
            return [SubTask(agent="CompareAgent", action="run", inputs={"question": question})]

        # Multi-sector flow: Sector explains -> Risk/Impact -> Merge
        sectors = [s for s in ("energy", "water", "transport") if s in q]
        if len(sectors) >= 2:
            tasks: List[SubTask] = []
            for s in sectors:
                tasks.append(
                    SubTask(
                        agent="SectorExplainAgent",
                        action="run",
                        inputs={"sector": s, "question": question, "topic": topic},
                    )
                )

            tasks.append(
                SubTask(
                    agent="RiskImpactAgent",
                    action="run",
                    inputs={"question": question, "topic": topic},
                )
            )

            tasks.append(SubTask(agent="MergeAgent", action="run", inputs={"mode": "multisector"}))
            return tasks

        return [SubTask(agent="PolicyExplainAgent", action="run", inputs={"question": question, "topic": topic})]