from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.errors import install_exception_handlers
from app.core.logging import setup_logging
from app.core.tracing import RequestContextMiddleware
from app.infrastructure.bootstrap import build_container
from app.infrastructure.persistence import init_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(settings.LOG_LEVEL)
    init_database()
    app.state.container = build_container()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.SERVICE_NAME,
        version=settings.SERVICE_VERSION,
        docs_url="/docs" if settings.ENV != "prod" else None,
        redoc_url="/redoc" if settings.ENV != "prod" else None,
        openapi_url="/openapi.json" if settings.ENV != "prod" else None,
        lifespan=lifespan,
    )
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_v1_router, prefix=settings.API_PREFIX)

    @app.get("/health")
    async def root_health():
        return {
            "status": "ok",
            "service": settings.SERVICE_NAME,
            "version": settings.SERVICE_VERSION,
            "env": settings.ENV,
            "mock_mode": settings.USE_MOCK_SERVICES,
        }

    install_exception_handlers(app)
    return app


app = create_app()
