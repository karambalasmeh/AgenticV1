import pytest

from app.application.ministry_classifier import MinistryClassifier
from app.infrastructure.llm import MockLLMProvider


@pytest.mark.asyncio
async def test_ministry_classifier_deterministic_match() -> None:
    classifier = MinistryClassifier(llm_provider=MockLLMProvider())
    result = await classifier.classify("How can we improve water irrigation policy?", "en")
    assert result.ministry_id == "mowi"
    assert result.confidence >= 0.55


@pytest.mark.asyncio
async def test_ministry_classifier_fallback_path() -> None:
    classifier = MinistryClassifier(llm_provider=MockLLMProvider())
    result = await classifier.classify("Classify this unusual request with no direct keyword.", "en")
    assert result.ministry_name
    assert 0.0 <= result.confidence <= 1.0
