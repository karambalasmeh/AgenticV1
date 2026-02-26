# app/llm/base.py
from abc import ABC, abstractmethod


class LLMProvider(ABC):
    # English comments only
    @abstractmethod
    def generate(self, prompt: str, system: str = "") -> str:
        raise NotImplementedError