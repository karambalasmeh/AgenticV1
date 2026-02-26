from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.tracing import RequestContextMiddleware
from app.core.errors import install_exception_handlers


def create_app() -> FastAPI:
    # Configure logging first
    setup_logging(settings.LOG_LEVEL)

    app = FastAPI(
        title=settings.SERVICE_NAME,
        version=settings.SERVICE_VERSION,
        docs_url="/docs" if settings.ENV != "prod" else None,
        redoc_url="/redoc" if settings.ENV != "prod" else None,
        openapi_url="/openapi.json" if settings.ENV != "prod" else None,
    )

    # Middlewares
    app.add_middleware(RequestContextMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # tighten in prod
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(api_v1_router, prefix="/api/v1")

    # Error handlers
    install_exception_handlers(app)

    return app


app = create_app()