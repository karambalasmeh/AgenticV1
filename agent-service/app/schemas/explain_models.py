from typing import List, Dict, Any
from pydantic import BaseModel


class ExplainDecisionRequest(BaseModel):
    # English comments only
    request_id: str
    decision_trace: List[Dict[str, Any]] = []
    confidence: Dict[str, Any] = {}


class ExplainDecisionResponse(BaseModel):
    # English comments only
    summary: str
    explanation: List[Dict[str, str]] = []
    audit_tags: List[str] = []