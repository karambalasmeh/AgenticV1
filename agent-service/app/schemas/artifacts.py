from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field


Status = Literal["success", "needs_escalation", "failed"]
ConfidenceLevel = Literal["low", "medium", "high"]
IssueSeverity = Literal["low", "medium", "high"]


class AnswerSection(BaseModel):
    # English comments only
    title: str
    content: str


class Answer(BaseModel):
    # English comments only
    format: Literal["structured", "narrative"] = "structured"
    language: Literal["ar", "en"] = "en"
    summary: str = ""
    sections: List[AnswerSection] = Field(default_factory=list)
    actionable_points: List[str] = Field(default_factory=list)


class Citation(BaseModel):
    # English comments only
    source_id: str
    chunk_id: str
    title: Optional[str] = None
    publisher: Optional[str] = None
    date: Optional[str] = None
    relevance_score: float = 0.0


class Confidence(BaseModel):
    # English comments only
    score: float
    level: ConfidenceLevel
    rationale: List[str] = Field(default_factory=list)
    signals: Dict[str, Any] = Field(default_factory=dict)


class ValidationIssue(BaseModel):
    # English comments only
    type: str
    severity: IssueSeverity
    details: str


class Validation(BaseModel):
    # English comments only
    passed: bool
    issues: List[ValidationIssue] = Field(default_factory=list)


class DecisionTraceStep(BaseModel):
    # English comments only
    step: str
    component: str
    reason: str


class EscalationTicket(BaseModel):
    # English comments only
    ticket_id: Optional[str] = None
    status: Optional[str] = None


class Escalation(BaseModel):
    # English comments only
    triggered: bool = False
    reason: Optional[str] = None
    ticket: Optional[EscalationTicket] = None