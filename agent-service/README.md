# agent-service (Team 2)

Government-grade orchestration microservice for the Jordan National Policy Intelligence Platform.

## What this service does

- Exposes `POST /api/v1/query` for chat-first policy answers.
- Orchestrates deterministic-first routing, specialist generation, validation/repair, confidence scoring, and escalation.
- Integrates with knowledge/governance/workflow services through resilient clients with automatic mock fallback.
- Persists audit logs, conversation history, artifacts, violations, tickets, and memory jobs asynchronously (non-blocking for `/query`).

## Clean architecture

- `app/api`: FastAPI routers only.
- `app/application`: orchestration, routing, validation, confidence, escalation, explanation.
- `app/domain`: request/response schemas and integration contracts.
- `app/infrastructure`: LLM providers, HTTP clients + mocks, persistence (SQLAlchemy), bootstrap/container.

## API surface

- `POST /api/v1/query`
- `POST /api/v1/delegate`
- `POST /api/v1/confidence`
- `POST /api/v1/validate`
- `POST /api/v1/explain_decision`
- `GET /health` (and `GET /api/v1/health`)

## Query behavior and `output_controls`

Default (chat-first): if `output_controls` is omitted, response is:

```json
{ "request_id": "...", "answer": "..." }
```

Backward-compatible controls:

- `include_evidence=false` => `citations` is always `[]`.
- `include_decision_trace=false` => `decision_trace` and `trace` are always `[]`.
- `include_confidence=false` => `confidence` is omitted.
- All internal artifacts are still computed and persisted.

## Local run (mock mode)

```bash
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8002 --reload
```

Swagger: `http://127.0.0.1:8002/docs`

## Local run (real integrations)

Set:

- `USE_MOCK_SERVICES=false`
- `LLM_PROVIDER=vertex` (or keep `mock`)
- service URLs to live endpoints
- `DATABASE_URL` to Postgres (for example `127.0.0.1:5433`)

## Env vars (`.env.example`)

| Variable | Purpose | Default |
|---|---|---|
| `USE_MOCK_SERVICES` | Enable mock fallback clients | `true` |
| `LLM_PROVIDER` | `mock` or `vertex` provider | `mock` |
| `DATABASE_URL` | SQLite/Postgres connection | `sqlite:///./agent_service.db` |
| `KNOWLEDGE_SERVICE_URL` | Team-1 endpoint | `http://knowledge-service:8000` |
| `WORKFLOW_SERVICE_URL` | Team-4 endpoint | `http://workflow-service:8000` |
| `GOVERNANCE_SERVICE_URL` | Team-3 endpoint | `http://governance-service:8000` |
| `CLIENT_TIMEOUT_S` | downstream timeout | `4` |
| `CLIENT_RETRIES` | downstream retries | `1` |

Postgres port-conflict example: `postgresql+psycopg://user:pass@127.0.0.1:5433/agent_service`

## Testing and checks

```bash
pytest -q
python -m compileall app
```

## Lint / format (CI-like command set)

```bash
ruff check .
ruff format .
pytest -q
```

## Escalation ticket payload

When escalated, workflow payload includes:

- ministry classification (`ministry_id`, `ministry_name`, confidence, rationale)
- confidence reasons
- validation issues
- evidence pack
- decision trace
- request/user context

## Notes

- Knowledge retrieval currently uses chunks without source filtering (as required).
- Conflict detection is deterministic and cheap.
- Memory/history writes are background tasks and never block `/query`.
- See `docs/ASSUMPTIONS.md` for explicit assumptions and future TODO hooks.
