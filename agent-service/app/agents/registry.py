from __future__ import annotations

from typing import Dict

from app.agents.base import Agent


class AgentRegistry:
    # English comments only
    def __init__(self) -> None:
        self._agents: Dict[str, Agent] = {}

    def register(self, agent: Agent) -> None:
        # English comments only
        self._agents[agent.name] = agent

    def get(self, name: str) -> Agent:
        # English comments only
        if name not in self._agents:
            raise KeyError(f"Agent not registered: {name}")
        return self._agents[name]

    def has(self, name: str) -> bool:
        # English comments only
        return name in self._agents

    def list(self) -> list[str]:
        # English comments only
        return list(self._agents.keys())