from typing import Literal, Optional, List, Dict
from pydantic import BaseModel, Field


Language = Literal["ar", "en", "auto"]
Priority = Literal["low", "normal", "high"]
ResponseType = Literal["answer", "briefing", "comparison", "monitoring_summary"]


class UserContext(BaseModel):
    # English comments only
    role: str = "unknown"
    department: Optional[str] = None
    clearance_level: Optional[str] = None


class SessionContext(BaseModel):
    # English comments only
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None


class Tasking(BaseModel):
    # English comments only
    response_type: ResponseType = "answer"
    priority: Priority = "normal"


class TimeRange(BaseModel):
    # English comments only
    from_date: Optional[str] = Field(default=None, alias="from")
    to_date: Optional[str] = Field(default=None, alias="to")


class SourceFilters(BaseModel):
    # English comments only
    allowed_sources: List[str] = []
    blocked_sources: List[str] = []
    source_types: List[str] = []


class Constraints(BaseModel):
    # English comments only
    time_range: Optional[TimeRange] = None
    source_filters: Optional[SourceFilters] = None
    max_evidence: int = 10


class OutputControls(BaseModel):
    # English comments only
    include_decision_trace: bool = True
    include_evidence: bool = True
    include_validation_report: bool = False


class Meta(BaseModel):
    # English comments only
    request_id: str