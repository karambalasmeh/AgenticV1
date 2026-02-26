from fastapi import APIRouter

from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.query import router as query_router
from app.api.v1.endpoints.delegate import router as delegate_router
from app.api.v1.endpoints.validate import router as validate_router
from app.api.v1.endpoints.confidence import router as confidence_router
from app.api.v1.endpoints.explain_decision import router as explain_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router, tags=["health"])
api_v1_router.include_router(query_router, tags=["query"])
api_v1_router.include_router(delegate_router, tags=["delegate"])
api_v1_router.include_router(validate_router, tags=["validate"])
api_v1_router.include_router(confidence_router, tags=["confidence"])
api_v1_router.include_router(explain_router, tags=["explain"])