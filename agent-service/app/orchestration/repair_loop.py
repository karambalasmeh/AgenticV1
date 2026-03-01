from __future__ import annotations

from typing import Callable, Tuple, List

from app.schemas.artifacts import ValidationIssue, Citation
from app.orchestration.decision_trace import trace
from app.agents.base import AgentContext, Artifacts


RunSpecialistsFn = Callable[[AgentContext, Artifacts], Artifacts]
ValidateFn = Callable[[str, List[Citation]], Tuple[bool, List[ValidationIssue]]]


def run_with_repair(
    ctx: AgentContext,
    artifacts: Artifacts,
    run_specialists: RunSpecialistsFn,
    validate: ValidateFn,
    max_attempts: int = 2,
) -> tuple[Artifacts, bool, list[ValidationIssue], int]:
    # English comments only
    last_issues: list[ValidationIssue] = []

    # attempt = number of validation attempts (NOT +1)
    for attempt in range(1, max_attempts + 1):
        answer_draft = str(artifacts.get("answer_draft", ""))
        citations = artifacts.get("citations", []) or []

        ok, issues = validate(answer_draft, citations)
        last_issues = issues

        if ok:
            ctx.trace.append(trace("repair_loop", "RepairLoop", f"Validation passed on attempt {attempt}."))
            return artifacts, True, issues, attempt

        ctx.trace.append(trace("repair_loop", "RepairLoop", f"Validation failed on attempt {attempt}."))

        # If this was the last attempt, stop
        if attempt == max_attempts:
            break

        # Repair strategy (LLM-based rewrite instruction)
        fix_prompt = (
            "Fix the draft to address the issues:\n"
            + "\n".join([f"- {i.type}: {i.details}" for i in issues])
            + "\n\nReturn an improved structured answer."
        )

        artifacts["repair_instructions"] = fix_prompt

        # Re-run specialists to produce a new answer draft
        ctx.trace.append(trace("repair_loop", "RepairLoop", "Attempting repair by re-running specialists."))
        artifacts = run_specialists(ctx, artifacts)

    ctx.trace.append(trace("repair_loop", "RepairLoop", f"Repair attempts exhausted ({max_attempts})."))
    return artifacts, False, last_issues, max_attempts