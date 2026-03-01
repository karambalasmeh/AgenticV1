from app.tools.base_client import BaseClient
from app.tools.contracts.workflow_contracts import TicketCreateRequest, TicketCreateResponse, EscalationRequest, EscalationResponse


class WorkflowClient(BaseClient):
    # English comments only
    async def create_ticket(self, request: TicketCreateRequest) -> TicketCreateResponse:
        data = await self._request("POST", "/tickets", payload=request)
        return TicketCreateResponse(**data)

    async def escalate(self, request: EscalationRequest) -> EscalationResponse:
        data = await self._request("POST", "/escalate", payload=request)
        return EscalationResponse(**data)
