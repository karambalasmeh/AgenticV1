# Decision Trace Spec

Trace item schema:

```json
{
  "step": "routing",
  "component": "Router",
  "reason": "intent=policy, topic=transport, complexity=low",
  "metadata": {}
}
```

Typical query steps:

1. `request_received`
2. `local_guardrail`
3. `governance_check`
4. `routing`
5. `retrieval`
6. `validation`
7. `confidence`
8. `ticket` (if escalated)

Trace is persisted regardless of UI output mode. It is returned only when `include_decision_trace=true`.
