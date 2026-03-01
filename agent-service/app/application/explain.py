from __future__ import annotations

from app.domain.models import ExplainDecisionRequest, ExplainDecisionResponse


class DecisionExplainer:
    def explain(self, req: ExplainDecisionRequest) -> ExplainDecisionResponse:
        if not req.decision_trace:
            return ExplainDecisionResponse(
                summary="No decision trace was provided.",
                explanation=[],
                audit_tags=["trace_missing"],
            )

        explanation = []
        tags = set()
        for step in req.decision_trace:
            explanation.append(
                {
                    "step": step.step,
                    "component": step.component,
                    "why": step.reason,
                }
            )
            tags.add(step.component.lower())

        summary = f"Processed {len(req.decision_trace)} decision steps for request {req.request_id}."
        if req.confidence:
            summary += f" Confidence level: {req.confidence.level} ({req.confidence.score:.2f})."
        return ExplainDecisionResponse(summary=summary, explanation=explanation, audit_tags=sorted(tags))
