# Validation Policy

Deterministic checks:

- non-empty answer
- language compliance with detected/user language
- citation structure checks when evidence output is required
- contradiction detection in answer text
- answer-vs-evidence contradiction detection

Repair loop:

- Triggered on any validation issue
- Max attempts: 2
- LLM is asked to rewrite with explicit issue list
- If still failing, confidence drops and escalation can trigger
