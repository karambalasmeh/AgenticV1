# LLM Strategy (Low Cost)

Deterministic-first policy:

- routing, validation, confidence, escalation are deterministic.
- LLM is used only for:
  1. specialist answer generation
  2. bounded repair rewrite (max 2)
  3. optional fallback ministry classification

Language enforcement:

- Question language is detected (`ar`/`en`) unless explicitly provided.
- Prompts include strict language instruction.
- Validator flags language mismatch.

Providers:

- `mock` (default): deterministic offline output.
- `vertex`: Gemini via Vertex AI.
