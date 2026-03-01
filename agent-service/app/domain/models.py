from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


Language = Literal["auto", "ar", "en"]
OutputLanguage = Literal["ar", "en"]
IssueSeverity = Literal["low", "medium", "high"]
ConfidenceLevel = Literal["low", "medium", "high"]
Status = Literal["success", "needs_escalation", "failed", "ok", "blocked", "escalated"]
ResponseType = Literal["answer", "briefing", "comparison", "monitoring_summary"]
Priority = Literal["low", "normal", "high"]


class UserContext(BaseModel):
    role: str = "unknown"
    department: Optional[str] = None
    clearance_level: Optional[str] = None


class SessionContext(BaseModel):
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None


class Tasking(BaseModel):
    response_type: ResponseType = "answer"
    priority: Priority = "normal"


class TimeRange(BaseModel):
    from_date: Optional[str] = Field(default=None, alias="from")
    to_date: Optional[str] = Field(default=None, alias="to")

    model_config = ConfigDict(populate_by_name=True)


class SourceFilters(BaseModel):
    allowed_sources: List[str] = Field(default_factory=list)
    blocked_sources: List[str] = Field(default_factory=list)
    source_types: List[str] = Field(default_factory=list)


class Constraints(BaseModel):
    time_range: Optional[TimeRange] = None
    source_filters: Optional[SourceFilters] = None
    max_evidence: int = 5


class OutputControls(BaseModel):
    include_decision_trace: bool = False
    include_evidence: bool = False
    include_confidence: bool = False
    include_validation_report: bool = False


class AnswerSection(BaseModel):
    title: str
    content: str


class Answer(BaseModel):
    format: Literal["structured", "narrative"] = "narrative"
    language: OutputLanguage = "en"
    summary: str = ""
    sections: List[AnswerSection] = Field(default_factory=list)
    actionable_points: List[str] = Field(default_factory=list)


class Citation(BaseModel):
    source_id: str
    chunk_id: str
    relevance_score: float = 0.0
    text: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ValidationIssue(BaseModel):
    type: str
    severity: IssueSeverity
    details: str


class Validation(BaseModel):
    passed: bool
    issues: List[ValidationIssue] = Field(default_factory=list)


class Confidence(BaseModel):
    score: float
    level: ConfidenceLevel
    rationale: List[str] = Field(default_factory=list)
    reasons: List[str] = Field(default_factory=list)
    signals: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def sync_reasons(self) -> "Confidence":
        if self.reasons and not self.rationale:
            self.rationale = list(self.reasons)
        if self.rationale and not self.reasons:
            self.reasons = list(self.rationale)
        return self


class DecisionTraceStep(BaseModel):
    step: str
    component: str
    reason: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EscalationTicket(BaseModel):
    ticket_id: Optional[str] = None
    status: Optional[str] = None


class Escalation(BaseModel):
    triggered: bool = False
    reason: Optional[str] = None
    ticket: Optional[EscalationTicket] = None
    triggers: List[str] = Field(default_factory=list)


class MinistryClassification(BaseModel):
    ministry_id: str
    ministry_name: str
    confidence: float
    rationale: str


class QueryRequest(BaseModel):
    user_id: Optional[str] = None
    conversation_id: Optional[str] = None
    question: str = Field(min_length=1, max_length=4000)
    language: Language = "auto"
    check_types: List[str] = Field(default_factory=lambda: ["safety", "sexual", "weapons"])
    require_evidence: bool = False
    max_chunks: int = Field(default=5, ge=1, le=20)
    user_context: UserContext = Field(default_factory=UserContext)
    session: SessionContext = Field(default_factory=SessionContext)
    tasking: Tasking = Field(default_factory=Tasking)
    constraints: Constraints = Field(default_factory=Constraints)
    output_controls: OutputControls = Field(default_factory=OutputControls)

    @model_validator(mode="after")
    def hydrate_legacy_fields(self) -> "QueryRequest":
        if not self.user_id:
            self.user_id = "anonymous"
        if not self.conversation_id:
            self.conversation_id = self.session.conversation_id or "default"
        if self.constraints.max_evidence and self.max_chunks == 5:
            self.max_chunks = max(1, min(20, self.constraints.max_evidence))
        return self


class QueryResponse(BaseModel):
    request_id: str
    answer: str | Answer
    status: Optional[Status] = None
    language: Optional[OutputLanguage] = None
    citations: Optional[List[Citation]] = None
    confidence: Optional[Confidence] = None
    validation: Optional[Validation] = None
    validation_issues: Optional[List[ValidationIssue]] = None
    decision_trace: Optional[List[DecisionTraceStep]] = None
    trace: Optional[List[DecisionTraceStep]] = None
    escalation: Optional[Escalation] = None
    ministry: Optional[MinistryClassification] = None

    @model_validator(mode="after")
    def sync_trace_fields(self) -> "QueryResponse":
        if self.trace and not self.decision_trace:
            self.decision_trace = list(self.trace)
        if self.decision_trace and not self.trace:
            self.trace = list(self.decision_trace)
        if self.validation and not self.validation_issues:
            self.validation_issues = list(self.validation.issues)
        return self


class DelegatePlanStep(BaseModel):
    agent: str
    action: str
    inputs: Dict[str, Any] = Field(default_factory=dict)


class DelegateRequest(BaseModel):
    task_id: str
    question: Optional[str] = None
    plan: List[DelegatePlanStep] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)


class DelegateResponse(BaseModel):
    task_id: str
    status: str
    artifacts: Dict[str, Any] = Field(default_factory=dict)
    decision_trace: List[DecisionTraceStep] = Field(default_factory=list)


class ValidateRequest(BaseModel):
    answer_draft: str
    language: Language = "auto"
    citations: List[Citation] = Field(default_factory=list)
    require_evidence: bool = False


class ValidateResponse(BaseModel):
    valid: bool
    issues: List[ValidationIssue] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    escalation_recommended: bool = False


class ConfidenceRequest(BaseModel):
    answer_draft: str
    citations: List[Citation] = Field(default_factory=list)
    signals: Dict[str, Any] = Field(default_factory=dict)
    validation_issues: List[ValidationIssue] = Field(default_factory=list)


class ConfidenceResponse(BaseModel):
    score: float
    level: ConfidenceLevel
    rationale: List[str] = Field(default_factory=list)
    reasons: List[str] = Field(default_factory=list)
    signals: Dict[str, Any] = Field(default_factory=dict)


class ExplainDecisionRequest(BaseModel):
    request_id: str
    decision_trace: List[DecisionTraceStep] = Field(default_factory=list)
    confidence: Optional[Confidence] = None
    validation_issues: List[ValidationIssue] = Field(default_factory=list)


class ExplainDecisionResponse(BaseModel):
    summary: str
    explanation: List[Dict[str, str]] = Field(default_factory=list)
    audit_tags: List[str] = Field(default_factory=list)


class APIErrorResponse(BaseModel):
    error_code: str
    message: str
    details: Optional[Any] = None
    request_id: str
    timestamp: str
