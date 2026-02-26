from typing import List, Optional
from pydantic import BaseModel
from app.schemas.artifacts import Citation, ValidationIssue


class ValidateRequest(BaseModel):
    # English comments only
    answer_draft: str
    citations: List[Citation] = []
    validation_mode: Optional[str] = "standard"


class ValidateResponse(BaseModel):
    # English comments only
    valid: bool
    issues: List[ValidationIssue] = []
    recommended_actions: List[str] = []
    escalation_recommended: bool = False