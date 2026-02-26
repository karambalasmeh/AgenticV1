from typing import Any, Dict, List
from pydantic import BaseModel
from app.schemas.artifacts import DecisionTraceStep


class DelegatePlanStep(BaseModel):
    # English comments only
    agent: str
    action: str
    inputs: Dict[str, Any] = {}


class DelegateRequest(BaseModel):
    # English comments only
    task_id: str
    plan: List[DelegatePlanStep]
    context: Dict[str, Any] = {}


class DelegateResponse(BaseModel):
    # English comments only
    task_id: str
    status: str
    artifacts: Dict[str, Any] = {}
    decision_trace: List[DecisionTraceStep] = []