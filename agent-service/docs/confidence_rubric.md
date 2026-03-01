# Confidence Rubric

Deterministic scorer (`app/application/confidence.py`) computes score `0..1`:

- Base score: `0.85`
- Penalties:
  - high/medium/low validation issues
  - low citation coverage for long answers
  - repair attempts
  - missing expected evidence

Confidence levels:

- `high`: `>= 0.75`
- `medium`: `>= 0.45` and `< 0.75`
- `low`: `< 0.45`

Output includes:

- `score`
- `level`
- `reasons` (human-readable)
- `signals` (machine-consumable)
