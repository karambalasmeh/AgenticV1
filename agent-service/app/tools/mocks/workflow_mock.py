from app.tools.contracts.workflow_contracts import (
    TicketCreateRequest,
    TicketCreateResponse,
    EscalationRequest,
    EscalationResponse,
)


class MockWorkflowClient:
    # English comments only
    def __init__(self, scenario: str = "SUCCESS_EVIDENCE"):
        self.scenario = scenario

    async def create_ticket(self, request: TicketCreateRequest) -> TicketCreateResponse:
        return TicketCreateResponse(ticket_id="TICKET-123", status="open")

    async def escalate(self, request: EscalationRequest) -> EscalationResponse:
        return EscalationResponse(success=True, new_status="escalated")
