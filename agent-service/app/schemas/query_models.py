from typing import Optional
from pydantic import BaseModel

from app.schemas.common import Language, UserContext, SessionContext, Tasking, Constraints, OutputControls
from app.schemas.artifacts import Answer, Citation, Confidence, Validation, DecisionTraceStep, Escalation, Status


class QueryRequest(BaseModel):
    # English comments only
    question: str
    language: Language = "auto"
    user_context: UserContext = UserContext()
    session: SessionContext = SessionContext()
    tasking: Tasking = Tasking()
    constraints: Constraints = Constraints()
    output_controls: OutputControls = OutputControls()


class QueryResponse(BaseModel):
    # English comments only
    request_id: str
    status: Status
    answer: Answer
    citations: list[Citation] = []
    confidence: Confidence
    validation: Validation
    decision_trace: list[DecisionTraceStep] = []
    escalation: Escalation = Escalation()