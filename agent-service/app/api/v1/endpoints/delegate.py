from fastapi import APIRouter
from app.schemas.delegate_models import DelegateRequest, DelegateResponse

router = APIRouter()


@router.post("/delegate", response_model=DelegateResponse)
def delegate(req: DelegateRequest) -> DelegateResponse:
    # Placeholder: delegation engine will be implemented by the owner later
    return DelegateResponse(
        task_id=req.task_id,
        status="accepted",
        artifacts={},
        decision_trace=[],
    )