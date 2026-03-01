# Assumptions

1. Knowledge-service currently supports `/retrieve` with chunks and optional metadata, but source filtering is not enforced yet.
2. Governance `guardrail_check` schema may vary; agent-service normalizes either `allowed/blocked` or legacy `passed`.
3. Workflow lifecycle beyond ticket creation is owned by Team-4; agent-service stores created ticket snapshot and optional status.
4. Persistence uses SQLAlchemy `create_all` for now (no Alembic migration chain yet). This is intentionally minimal for fast integration.
5. Default deployment mode is mock-safe (`USE_MOCK_SERVICES=true`) to avoid blocking on external teams.
6. Answer-only default mode applies when `output_controls` is omitted. Explicit controls preserve backward-compatible response fields.

## TODO Hooks

- Replace SQLAlchemy `create_all` with Alembic migration workflow.
- Add richer conflict detection using evidence versions metadata when Team-1 finalizes version contract.
- Add asynchronous queue worker for memory summarization and audit fan-out.
- Add workflow status polling endpoint integration once Team-4 contract is finalized.
