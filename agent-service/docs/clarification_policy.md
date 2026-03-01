# Clarification Policy

Current `/query` behavior is answer-first with deterministic routing.

Clarification can be introduced as a future extension when strict required fields are enabled by policy (for example mandatory comparison date ranges).

Current low-cost stance:

- Do not block benign questions for missing optional fields.
- Escalate only when confidence and validation signals justify workflow ticket creation.
- Keep clarification logic as a TODO hook in application routing/service layer.
