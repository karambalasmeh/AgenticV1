from __future__ import annotations

import asyncio

from app.domain.models import QueryRequest, QueryResponse
from app.infrastructure.bootstrap import build_container


def run_query(req: QueryRequest) -> QueryResponse:
    container = build_container()
    execution = asyncio.run(container.orchestration.execute_query(req))
    container.repository.persist_query(execution.persistence_payload)
    return execution.response
