from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()


@router.get("/health")
def health():
    # English comments only
    return {
        "status": "ok",
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "env": settings.ENV,
    }