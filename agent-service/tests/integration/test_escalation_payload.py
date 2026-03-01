from fastapi.testclient import TestClient

from app.main import create_app


def test_escalation_ticket_contains_required_fields_when_triggered() -> None:
    app = create_app()
    with TestClient(app) as client:
        payload = {
            "user_id": "u_escalate",
            "conversation_id": "c_escalate",
            "question": "Provide uncertain policy analysis with strict evidence requirement.",
            "require_evidence": True,
            "output_controls": {
                "include_evidence": True,
                "include_decision_trace": True,
                "include_confidence": True,
                "include_validation_report": True,
            },
        }

        container = app.state.container

        async def empty_retrieve(query: str, top_k: int):
            from app.domain.contracts import RetrieveResponse
            from app.infrastructure.clients import IntegrationResult

            return IntegrationResult(data=RetrieveResponse(chunks=[]))

        container.integrations.retrieve = empty_retrieve

        response = client.post("/api/v1/query", json=payload)
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "needs_escalation"
        assert body["escalation"]["triggered"] is True
        assert body["escalation"]["ticket"]["ticket_id"]
        assert body["ministry"]["ministry_name"]
        assert body["confidence"]["reasons"]


def test_auxiliary_endpoints_contracts() -> None:
    app = create_app()
    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200

        validate = client.post(
            "/api/v1/validate",
            json={"answer_draft": "A draft answer", "language": "en", "require_evidence": True, "citations": []},
        )
        assert validate.status_code == 200
        assert "valid" in validate.json()

        confidence = client.post(
            "/api/v1/confidence",
            json={"answer_draft": "A short answer", "citations": [], "signals": {}, "validation_issues": []},
        )
        assert confidence.status_code == 200
        assert "score" in confidence.json()

        explain = client.post(
            "/api/v1/explain_decision",
            json={"request_id": "r1", "decision_trace": [], "validation_issues": []},
        )
        assert explain.status_code == 200
        assert "summary" in explain.json()
