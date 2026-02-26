from fastapi import APIRouter
from app.schemas.confidence_models import ConfidenceRequest, ConfidenceResponse

router = APIRouter()


@router.post("/confidence", response_model=ConfidenceResponse)
def confidence(req: ConfidenceRequest) -> ConfidenceResponse:
    # Placeholder: confidence rubric will be implemented later
    return ConfidenceResponse(
        score=0.5,
        level="medium",
        rationale=["Placeholder confidence score."],
        signals=req.signals or {},
    )