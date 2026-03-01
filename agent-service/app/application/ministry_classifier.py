from __future__ import annotations

from dataclasses import dataclass

from app.application.language import language_instruction
from app.domain.models import MinistryClassification, OutputLanguage


@dataclass(frozen=True)
class _Rule:
    ministry_id: str
    ministry_name: str
    keywords: tuple[str, ...]


RULES = (
    _Rule("moe", "Ministry of Energy", ("energy", "electricity", "renewable", "الطاقة", "الكهرباء")),
    _Rule("moh", "Ministry of Health", ("health", "hospital", "medical", "الصحة", "مستشفى")),
    _Rule("moedu", "Ministry of Education", ("education", "school", "university", "التعليم", "جامعة")),
    _Rule("mowi", "Ministry of Water and Irrigation", ("water", "irrigation", "المياه", "الري")),
    _Rule("mot", "Ministry of Transport", ("transport", "road", "traffic", "النقل", "المرور")),
    _Rule("moec", "Ministry of Economy", ("economy", "investment", "inflation", "الاقتصاد", "الاستثمار")),
)


class MinistryClassifier:
    def __init__(self, llm_provider) -> None:
        self.llm = llm_provider

    async def classify(self, question: str, language: OutputLanguage) -> MinistryClassification:
        lowered = question.lower()
        scores: list[tuple[int, _Rule]] = []
        for rule in RULES:
            score = sum(1 for keyword in rule.keywords if keyword in lowered)
            if score:
                scores.append((score, rule))
        if scores:
            scores.sort(key=lambda pair: pair[0], reverse=True)
            top_score, top_rule = scores[0]
            confidence = min(0.95, 0.55 + (top_score * 0.12))
            return MinistryClassification(
                ministry_id=top_rule.ministry_id,
                ministry_name=top_rule.ministry_name,
                confidence=confidence,
                rationale="Deterministic keyword mapping.",
            )

        prompt = (
            "Classify the question into one Jordanian government ministry. "
            "Return one line as: ministry_id|ministry_name|confidence(0-1)|rationale.\n"
            f"Question: {question}"
        )
        completion = await self.llm.generate(
            system_prompt=f"You are a strict classifier. {language_instruction(language)}",
            user_prompt=prompt,
            temperature=0.0,
            max_tokens=120,
        )
        parts = [part.strip() for part in completion.split("|")]
        if len(parts) >= 4:
            try:
                confidence = float(parts[2])
            except ValueError:
                confidence = 0.45
            return MinistryClassification(
                ministry_id=parts[0] or "unknown",
                ministry_name=parts[1] or "Unknown Ministry",
                confidence=max(0.0, min(1.0, confidence)),
                rationale=parts[3] or "LLM fallback classification.",
            )

        return MinistryClassification(
            ministry_id="unknown",
            ministry_name="Unknown Ministry",
            confidence=0.3,
            rationale="No deterministic match and fallback parse failed.",
        )
