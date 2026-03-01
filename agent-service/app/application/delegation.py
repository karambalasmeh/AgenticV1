from __future__ import annotations

from app.application.router import Router
from app.domain.models import DecisionTraceStep, DelegatePlanStep, DelegateRequest, DelegateResponse, QueryRequest


class DelegationService:
    def __init__(self, router: Router | None = None) -> None:
        self.router = router or Router()

    def build_plan_for_query(self, req: QueryRequest) -> list[DelegatePlanStep]:
        decision = self.router.route(req)
        plan: list[DelegatePlanStep] = []
        for specialist in decision.specialists:
            plan.append(
                DelegatePlanStep(
                    agent=specialist,
                    action="generate",
                    inputs={"intent": decision.intent, "topic": decision.topic},
                )
            )
        if len(plan) > 1:
            plan.append(DelegatePlanStep(agent="merge_specialist", action="merge", inputs={}))
        return plan

    def execute(self, req: DelegateRequest) -> DelegateResponse:
        steps = req.plan or []
        trace = [
            DecisionTraceStep(
                step="delegate",
                component="DelegationService",
                reason=f"Accepted {len(steps)} step(s) for execution planning.",
            )
        ]
        return DelegateResponse(
            task_id=req.task_id,
            status="accepted",
            artifacts={"plan_steps": [step.model_dump() for step in steps]},
            decision_trace=trace,
        )
