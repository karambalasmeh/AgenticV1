from fastapi import APIRouter
from app.schemas.query_models import QueryRequest, QueryResponse
from app.orchestration.pipeline import run_query

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
def query(req: QueryRequest) -> QueryResponse:
    # English comments only
    return run_query(req)