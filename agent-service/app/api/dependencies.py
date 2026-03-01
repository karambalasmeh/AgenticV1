from __future__ import annotations

from fastapi import Request

from app.infrastructure.bootstrap import ServiceContainer


def get_container(request: Request) -> ServiceContainer:
    return request.app.state.container
