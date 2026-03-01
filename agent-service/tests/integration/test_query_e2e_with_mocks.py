import time

from fastapi.testclient import TestClient

from app.main import create_app


def test_query_returns_chat_answer_and_respects_output_controls() -> None:
    app = create_app()
    with TestClient(app) as client:
        payload = {
            "user_id": "u_123",
            "conversation_id": "c_456",
            "question": "What is the current energy policy objective?",
            "output_controls": {
                "include_evidence": False,
                "include_decision_trace": False,
                "include_confidence": False,
            },
        }
        response = client.post("/api/v1/query", json=payload)
        assert response.status_code == 200
        body = response.json()
        assert body["request_id"]
        assert body["answer"]
        assert body["citations"] == []
        assert body["trace"] == []
        assert body["decision_trace"] == []
        assert "confidence" not in body or body["confidence"] is None


def test_query_language_matches_arabic_input() -> None:
    app = create_app()
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/query",
            json={
                "user_id": "u_ar",
                "conversation_id": "c_ar",
                "question": "ما هي سياسة التعليم الحالية؟",
                "output_controls": {
                    "include_evidence": False,
                    "include_decision_trace": False,
                    "include_confidence": False,
                },
            },
        )
        assert response.status_code == 200
        body = response.json()
        assert body["language"] == "ar"
        assert any("\u0600" <= char <= "\u06ff" for char in body["answer"])


def test_query_path_not_blocked_by_background_persistence() -> None:
    app = create_app()
    with TestClient(app) as client:
        start = time.perf_counter()
        response = client.post(
            "/api/v1/query",
            json={
                "user_id": "u_async",
                "conversation_id": "c_async",
                "question": "Explain transport policy briefly.",
            },
        )
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        assert response.status_code == 200
        assert elapsed_ms < 2500
