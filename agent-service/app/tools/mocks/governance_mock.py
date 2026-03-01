from app.tools.contracts.governance_contracts import (
    GuardrailCheckRequest,
    GuardrailCheckResponse,
    AuditLogRequest,
    AuditLogResponse,
)


class MockGovernanceClient:
    # English comments only
    def __init__(self, scenario: str = "SUCCESS_EVIDENCE"):
        self.scenario = scenario

    async def check_guardrails(self, request: GuardrailCheckRequest) -> GuardrailCheckResponse:
        if self.scenario == "GUARDRAIL_BLOCK":
            return GuardrailCheckResponse(
                passed=False,
                violations=["PII detected in request", "Sensitive data leak"],
                risk_score=0.9
            )
        
        return GuardrailCheckResponse(passed=True, violations=[], risk_score=0.05)

    async def log_audit(self, request: AuditLogRequest) -> AuditLogResponse:
        return AuditLogResponse(success=True, log_id="AUDIT-LOG-999")
