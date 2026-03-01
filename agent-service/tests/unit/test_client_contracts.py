import pytest

from app.domain.contracts import GuardrailCheckRequest, TicketCreateRequest
from app.infrastructure.clients import IntegrationClients


@pytest.mark.asyncio
async def test_mock_knowledge_contract_shapes() -> None:
    clients = IntegrationClients(
        use_mocks=True,
        knowledge_base_url="http://localhost:9999",
        governance_base_url="http://localhost:9999",
        workflow_base_url="http://localhost:9999",
        timeout_s=0.1,
        retries=0,
    )
    result = await clients.retrieve("education policy", top_k=2)
    assert result.data.chunks
    first = result.data.chunks[0]
    assert first.source_id
    assert first.chunk_id


@pytest.mark.asyncio
async def test_mock_governance_contract_shapes() -> None:
    clients = IntegrationClients(
        use_mocks=True,
        knowledge_base_url="http://localhost:9999",
        governance_base_url="http://localhost:9999",
        workflow_base_url="http://localhost:9999",
        timeout_s=0.1,
        retries=0,
    )
    result = await clients.guardrail_check(GuardrailCheckRequest(content="normal policy question", check_types=[]))
    assert result.data.allowed is True
    assert isinstance(result.data.violations, list)


@pytest.mark.asyncio
async def test_mock_workflow_contract_shapes() -> None:
    clients = IntegrationClients(
        use_mocks=True,
        knowledge_base_url="http://localhost:9999",
        governance_base_url="http://localhost:9999",
        workflow_base_url="http://localhost:9999",
        timeout_s=0.1,
        retries=0,
    )
    result = await clients.create_ticket(
        TicketCreateRequest(
            title="Escalation",
            description="Need review",
            ministry={"id": "m1"},
            payload={"k": "v"},
        )
    )
    assert result.data.ticket_id
    assert result.data.status == "open"
