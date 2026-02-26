from app.schemas.artifacts import DecisionTraceStep


def trace(step: str, component: str, reason: str) -> DecisionTraceStep:
    return DecisionTraceStep(step=step, component=component, reason=reason)