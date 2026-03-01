from fastapi import APIRouter, BackgroundTasks, Depends

from app.api.dependencies import get_container
from app.domain.models import QueryRequest, QueryResponse
from app.infrastructure.bootstrap import ServiceContainer

router = APIRouter()


@router.post("/query", response_model=QueryResponse, response_model_exclude_none=True)
async def query(
    req: QueryRequest,
    background_tasks: BackgroundTasks,
    container: ServiceContainer = Depends(get_container),
) -> QueryResponse:
    execution = await container.orchestration.execute_query(req)
    background_tasks.add_task(container.orchestration.persist_execution, execution.persistence_payload)
    return execution.response
