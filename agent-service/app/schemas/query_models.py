from pydantic import BaseModel, Field

from app.schemas.common import Language, UserContext, SessionContext, Tasking, Constraints, OutputControls
from app.schemas.artifacts import Answer, Citation, Confidence, Validation, DecisionTraceStep, Escalation, Status


class QueryRequest(BaseModel):
    # English comments only
    question: str
    language: Language = "auto"
    user_context: UserContext = Field(default_factory=UserContext)
    session: SessionContext = Field(default_factory=SessionContext)
    tasking: Tasking = Field(default_factory=Tasking)
    constraints: Constraints = Field(default_factory=Constraints)
    output_controls: OutputControls = Field(default_factory=OutputControls)


class QueryResponse(BaseModel):
    # English comments only
    request_id: str
    status: Status
    answer: Answer
    citations: list[Citation] = Field(default_factory=list)
    confidence: Confidence
    validation: Validation
    decision_trace: list[DecisionTraceStep] = Field(default_factory=list)
    escalation: Escalation = Field(default_factory=Escalation)