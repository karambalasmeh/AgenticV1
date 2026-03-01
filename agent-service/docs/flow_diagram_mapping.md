# Runtime Flow Mapping

`OrchestrationService.execute_query` implements:

1. request id/correlation setup
2. deterministic local guardrail
3. governance guardrail check (fail-open with audit trace + fallback logging)
4. language detection (Arabic/English)
5. routing (intent/topic/complexity/specialists)
6. optional retrieval from knowledge-service `/retrieve` (no source filter enforcement)
7. specialist execution (parallel for complex routes)
8. merge draft
9. deterministic validation
10. bounded repair loop (max 2)
11. confidence scoring
12. escalation and workflow ticket creation
13. immediate response return
14. async persistence and memory job write
