from typing import Any, Optional
from pydantic import BaseModel


class APIErrorResponse(BaseModel):
    # English comments only
    error_code: str
    message: str
    details: Optional[Any] = None
    request_id: str
    timestamp: str