from typing import List, Optional, Any
from pydantic import BaseModel


class GuardrailCheckRequest(BaseModel):
    # English comments only
    content: str
    check_types: List[str] = ["pii", "toxic", "safety"]


class GuardrailCheckResponse(BaseModel):
    # English comments only
    passed: bool
    violations: List[str] = []
    risk_score: float = 0.0


class AuditLogRequest(BaseModel):
    # English comments only
    event: str
    actor: str
    details: dict[str, Any] = {}


class AuditLogResponse(BaseModel):
    # English comments only
    success: bool
    log_id: str
