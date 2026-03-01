from typing import Optional, Any
from pydantic import BaseModel


class TicketCreateRequest(BaseModel):
    # English comments only
    title: str
    description: str
    priority: str = "normal"
    metadata: dict[str, Any] = {}


class TicketCreateResponse(BaseModel):
    # English comments only
    ticket_id: str
    status: str


class EscalationRequest(BaseModel):
    # English comments only
    ticket_id: str
    reason: str
    context: dict[str, Any] = {}


class EscalationResponse(BaseModel):
    # English comments only
    success: bool
    new_status: str
