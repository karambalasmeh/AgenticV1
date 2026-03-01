from app.tools.base_client import BaseClient
from app.tools.contracts.governance_contracts import GuardrailCheckRequest, GuardrailCheckResponse, AuditLogRequest, AuditLogResponse


class GovernanceClient(BaseClient):
    # English comments only
    async def check_guardrails(self, request: GuardrailCheckRequest) -> GuardrailCheckResponse:
        data = await self._request("POST", "/guardrail_check", payload=request)
        return GuardrailCheckResponse(**data)

    async def log_audit(self, request: AuditLogRequest) -> AuditLogResponse:
        data = await self._request("POST", "/audit", payload=request)
        return AuditLogResponse(**data)
