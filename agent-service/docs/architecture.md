# Architecture Overview

## API Layer

- `app/api/v1/endpoints/*`
- Thin request/response handling only
- Delegates business logic to container services

## Application Layer

- `app/application/orchestration_service.py`
- Deterministic-first orchestration workflow
- Router, validator, confidence, escalation, classifier, explainer services

## Domain Layer

- `app/domain/models.py`
- `app/domain/contracts.py`
- Shared request/response types and integration contracts

## Infrastructure Layer

- `app/infrastructure/llm.py`: LLM provider implementations
- `app/infrastructure/clients.py`: resilient HTTP clients + mocks/fallbacks
- `app/infrastructure/persistence/*`: SQLAlchemy models/repository/init
- `app/infrastructure/bootstrap.py`: dependency wiring
