from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List

from app.schemas.query_models import QueryRequest


@dataclass
class RouteDecision:
    # English comments only
    intent: str
    topic: str
    is_complex: bool
    missing_params: List[str]


class RouterAgent:
    # English comments only
    name = "RouterAgent"

    def route(self, req: QueryRequest) -> RouteDecision:
        q = (req.question or "").lower()

        # Basic intent/topic heuristics (placeholder)
        intent = "compare" if (" compare " in f" {q} " or " vs " in q) else "explain"
        topic = self._guess_topic(q)

        # Complexity: comparison/monitoring or multi-sector keywords => complex
        is_complex = req.tasking.response_type in ("comparison", "monitoring_summary") or self._is_multisector(q)

        missing = []
        if req.tasking.response_type in ("comparison", "monitoring_summary"):
            tr = req.constraints.time_range
            if not tr or not (tr.from_date and tr.to_date):
                missing.append("time_range.from & time_range.to")

        return RouteDecision(intent=intent, topic=topic, is_complex=is_complex, missing_params=missing)

    def _guess_topic(self, q: str) -> str:
        for t in ("water", "energy", "transport", "economy", "health", "education"):
            if t in q:
                return t
        return "general"

    def _is_multisector(self, q: str) -> bool:
        hits = sum(1 for t in ("water", "energy", "transport") if t in q)
        return hits >= 2