# API Contracts

Base path: `/api/v1`

## `POST /query`

Request:

```json
{
  "user_id": "u_123",
  "conversation_id": "c_456",
  "question": "What is the transport policy update?",
  "output_controls": {
    "include_evidence": false,
    "include_decision_trace": false,
    "include_confidence": false
  }
}
```

Default response (when `output_controls` omitted):

```json
{
  "request_id": "uuid",
  "answer": "..."
}
```

Controlled response (backward-compatible fields available):

- `status`
- `language`
- `citations`
- `confidence`
- `validation`
- `validation_issues`
- `decision_trace`
- `trace`
- `escalation`
- `ministry`

## `POST /delegate`

Accepts delegation plan and returns acceptance status + plan artifacts.

## `POST /confidence`

Accepts `answer_draft`, citations, and validation signals, returns `score` + `level` + reasons.

## `POST /validate`

Validates answer draft deterministically and returns issues plus recommended actions.

## `POST /explain_decision`

Converts trace/confidence into audit-readable explanation blocks.

## `GET /health`

Service status plus `mock_mode` flag.
