from app.application.router import Router
from app.domain.models import QueryRequest


def test_router_detects_comparison_and_high_complexity() -> None:
    router = Router()
    request = QueryRequest(
        user_id="u1",
        conversation_id="c1",
        question="Compare energy and water policy impacts on growth and jobs in Jordan",
    )

    decision = router.route(request)

    assert decision.intent == "compare"
    assert decision.complexity == "high"
    assert decision.retrieve_evidence is True
    assert "compare_specialist" in decision.specialists


def test_router_detects_simple_policy_question() -> None:
    router = Router()
    request = QueryRequest(
        user_id="u1",
        conversation_id="c1",
        question="What is the latest education policy objective?",
    )

    decision = router.route(request)

    assert decision.intent == "policy"
    assert decision.topic == "education"
    assert decision.complexity in {"low", "medium"}
    assert decision.specialists == ["policy_specialist"]
