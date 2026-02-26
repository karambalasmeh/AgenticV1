from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel


class ConfidenceRequest(BaseModel):
    # English comments only
    answer_draft: str
    citations: List[Dict[str, Any]] = []
    signals: Optional[Dict[str, Any]] = None


class ConfidenceResponse(BaseModel):
    # English comments only
    score: float
    level: Literal["low", "medium", "high"]
    rationale: List[str] = []
    signals: Dict[str, Any] = {}