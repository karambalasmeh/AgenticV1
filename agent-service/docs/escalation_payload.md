# Escalation Payload

Workflow ticket creation includes:

- `title`, `description`
- `ministry` classification:
  - `ministry_id`
  - `ministry_name`
  - confidence
  - rationale
- `payload`:
  - `request_id`
  - `question`
  - `confidence_reasons`
  - `validation_issues`
  - `evidence_pack` (chunks with source/chunk ids)
  - `decision_trace`
  - `user_context`

Escalation triggers:

- low confidence
- high-risk validation issues
- missing required evidence
- repeated policy-violation behavior
- policy uncertainty flags
