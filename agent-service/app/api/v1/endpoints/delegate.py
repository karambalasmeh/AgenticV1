from fastapi import APIRouter, Depends

from app.api.dependencies import get_container
from app.domain.models import DelegateRequest, DelegateResponse
from app.infrastructure.bootstrap import ServiceContainer

router = APIRouter()


@router.post("/delegate", response_model=DelegateResponse)
async def delegate(req: DelegateRequest, container: ServiceContainer = Depends(get_container)) -> DelegateResponse:
    return container.delegation.execute(req)
