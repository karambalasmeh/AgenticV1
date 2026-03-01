from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class KnowledgeChunk(BaseModel):
    source_id: str
    chunk_id: str
    text: str
    relevance_score: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RetrieveRequest(BaseModel):
    query: str
    top_k: int = 5


class RetrieveResponse(BaseModel):
    chunks: List[KnowledgeChunk] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SourceRecord(BaseModel):
    source_id: str
    name: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SourcesResponse(BaseModel):
    sources: List[SourceRecord] = Field(default_factory=list)


class VersionRecord(BaseModel):
    version_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VersionsResponse(BaseModel):
    versions: List[VersionRecord] = Field(default_factory=list)


class GuardrailCheckRequest(BaseModel):
    content: str
    check_types: List[str] = Field(default_factory=list)


class GuardrailCheckResponse(BaseModel):
    allowed: bool
    blocked: bool = False
    violations: List[str] = Field(default_factory=list)
    risk_score: float = 0.0
    details: Dict[str, Any] = Field(default_factory=dict)


class AuditLogRequest(BaseModel):
    request_id: str
    event: str
    payload: Dict[str, Any] = Field(default_factory=dict)


class AuditLogResponse(BaseModel):
    success: bool = True
    log_id: Optional[str] = None


class TicketCreateRequest(BaseModel):
    title: str
    description: str
    ministry: Dict[str, Any] = Field(default_factory=dict)
    payload: Dict[str, Any] = Field(default_factory=dict)


class TicketCreateResponse(BaseModel):
    ticket_id: str
    status: str = "open"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TicketStatusResponse(BaseModel):
    ticket_id: str
    status: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
