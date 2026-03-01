from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.models import QueryRequest


@dataclass(frozen=True)
class RouteDecision:
    intent: str
    topic: str
    complexity: str
    specialists: list[str] = field(default_factory=list)
    retrieve_evidence: bool = True


class Router:
    TOPIC_KEYWORDS = {
        "economy": ("economy", "economic", "inflation", "gdp", "الاقتصاد", "الناتج"),
        "health": ("health", "hospital", "medical", "الصحة", "مستشفى"),
        "education": ("education", "school", "university", "التعليم", "جامعة"),
        "energy": ("energy", "electricity", "power", "الطاقة", "الكهرباء"),
        "water": ("water", "irrigation", "المياه", "الري"),
        "transport": ("transport", "traffic", "road", "النقل", "المرور"),
    }

    def route(self, req: QueryRequest) -> RouteDecision:
        question = req.question.lower()
        intent = self._intent(question, req.tasking.response_type)
        topic = self._topic(question)
        complexity = self._complexity(question, intent)
        specialists = self._specialists(intent, complexity)
        retrieve = req.require_evidence or intent in {"compare", "analysis", "policy"} or complexity == "high"
        return RouteDecision(
            intent=intent,
            topic=topic,
            complexity=complexity,
            specialists=specialists,
            retrieve_evidence=retrieve,
        )

    def _intent(self, question: str, response_type: str) -> str:
        if response_type == "comparison" or "compare" in question or "مقارنة" in question:
            return "compare"
        if "risk" in question or "impact" in question or "مخاطر" in question:
            return "analysis"
        return "policy"

    def _topic(self, question: str) -> str:
        for topic, keywords in self.TOPIC_KEYWORDS.items():
            if any(keyword in question for keyword in keywords):
                return topic
        return "general"

    def _complexity(self, question: str, intent: str) -> str:
        long_query = len(question.split()) > 22
        multi_domain = sum(1 for keys in self.TOPIC_KEYWORDS.values() if any(k in question for k in keys)) > 1
        if intent == "compare" or long_query or multi_domain:
            return "high"
        if len(question.split()) > 10:
            return "medium"
        return "low"

    def _specialists(self, intent: str, complexity: str) -> list[str]:
        if intent == "compare":
            return ["compare_specialist", "policy_specialist"]
        if complexity == "high":
            return ["policy_specialist", "risk_specialist", "fact_specialist"]
        return ["policy_specialist"]
