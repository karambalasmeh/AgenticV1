from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Protocol, runtime_checkable, Optional, List

from app.llm.base import LLMProvider
from app.schemas.artifacts import DecisionTraceStep


Artifacts = Dict[str, Any]


@dataclass
class AgentContext:
    # English comments only
    request_id: str
    llm: LLMProvider
    trace: List[DecisionTraceStep] = field(default_factory=list)


@runtime_checkable
class Agent(Protocol):
    # English comments only
    name: str

    def run(self, ctx: AgentContext, artifacts: Artifacts) -> Artifacts:
        ...