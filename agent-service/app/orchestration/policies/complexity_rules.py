from __future__ import annotations


def infer_complexity(question: str) -> str:
    lowered = (question or "").lower()
    if len(lowered.split()) > 22 or "compare" in lowered or "مقارنة" in lowered:
        return "high"
    if len(lowered.split()) > 10:
        return "medium"
    return "low"
