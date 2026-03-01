from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Any

import httpx

from app.domain.contracts import (
    AuditLogRequest,
    GuardrailCheckRequest,
    GuardrailCheckResponse,
    KnowledgeChunk,
    RetrieveResponse,
    SourcesResponse,
    SourceRecord,
    TicketCreateRequest,
    TicketCreateResponse,
    TicketStatusResponse,
    VersionRecord,
    VersionsResponse,
)

logger = logging.getLogger(__name__)


class _HTTPBaseClient:
    def __init__(self, base_url: str, timeout_s: float, retries: int) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s
        self.retries = retries

    async def _request(self, method: str, path: str, json_body: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        for attempt in range(self.retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout_s) as client:
                    response = await client.request(method=method, url=url, json=json_body)
                response.raise_for_status()
                if not response.text:
                    return {}
                return response.json()
            except Exception:
                if attempt >= self.retries:
                    raise
                await asyncio.sleep(0.2 * (attempt + 1))
        return {}


class KnowledgeHTTPClient(_HTTPBaseClient):
    async def retrieve(self, query: str, top_k: int) -> RetrieveResponse:
        payload = {"query": query, "top_k": top_k}
        data = await self._request("POST", "/retrieve", payload)
        chunks = []
        for raw in data.get("chunks", []) or data.get("documents", []):
            chunks.append(
                KnowledgeChunk(
                    source_id=str(raw.get("source_id") or raw.get("id") or ""),
                    chunk_id=str(raw.get("chunk_id") or raw.get("id") or ""),
                    text=str(raw.get("text") or raw.get("content") or ""),
                    relevance_score=float(raw.get("relevance_score", raw.get("score", 0.0))),
                    metadata=raw.get("metadata") or {},
                )
            )
        return RetrieveResponse(chunks=chunks, metadata=data.get("metadata") or {})

    async def get_sources(self) -> SourcesResponse:
        data = await self._request("GET", "/sources")
        sources = [
            SourceRecord(
                source_id=str(item.get("source_id") or item.get("id") or ""),
                name=str(item.get("name") or ""),
                metadata=item.get("metadata") or {},
            )
            for item in data.get("sources", [])
        ]
        return SourcesResponse(sources=sources)

    async def get_versions(self) -> VersionsResponse:
        data = await self._request("GET", "/versions")
        versions = [
            VersionRecord(
                version_id=str(item.get("version_id") or item.get("id") or ""),
                timestamp=str(item.get("timestamp") or ""),
                metadata=item.get("metadata") or {},
            )
            for item in data.get("versions", [])
        ]
        return VersionsResponse(versions=versions)


class GovernanceHTTPClient(_HTTPBaseClient):
    async def guardrail_check(self, request: GuardrailCheckRequest) -> GuardrailCheckResponse:
        data = await self._request("POST", "/guardrail_check", request.model_dump())
        return GuardrailCheckResponse(
            allowed=bool(data.get("allowed", data.get("passed", True))),
            blocked=bool(data.get("blocked", not data.get("passed", True))),
            violations=[str(item) for item in data.get("violations", [])],
            risk_score=float(data.get("risk_score", 0.0)),
            details=data.get("details") or {},
        )

    async def audit(self, request: AuditLogRequest) -> None:
        await self._request("POST", "/audit", request.model_dump())


class WorkflowHTTPClient(_HTTPBaseClient):
    async def create_ticket(self, request: TicketCreateRequest) -> TicketCreateResponse:
        data = await self._request("POST", "/tickets", request.model_dump())
        return TicketCreateResponse(
            ticket_id=str(data.get("ticket_id") or data.get("id") or ""),
            status=str(data.get("status") or "open"),
            metadata=data.get("metadata") or {},
        )

    async def get_ticket_status(self, ticket_id: str) -> TicketStatusResponse:
        data = await self._request("GET", f"/tickets/{ticket_id}")
        return TicketStatusResponse(
            ticket_id=ticket_id,
            status=str(data.get("status") or "unknown"),
            metadata=data.get("metadata") or {},
        )


class MockKnowledgeClient:
    async def retrieve(self, query: str, top_k: int) -> RetrieveResponse:
        chunks = [
            KnowledgeChunk(
                source_id="policy-001",
                chunk_id="chunk-a",
                text=f"Policy excerpt relevant to: {query}",
                relevance_score=0.92,
                metadata={"title": "National Policy Update"},
            ),
            KnowledgeChunk(
                source_id="policy-002",
                chunk_id="chunk-b",
                text=f"Secondary evidence about: {query}",
                relevance_score=0.77,
                metadata={"title": "Ministry Circular"},
            ),
        ]
        return RetrieveResponse(chunks=chunks[:top_k], metadata={"source_filters_supported": False})

    async def get_sources(self) -> SourcesResponse:
        return SourcesResponse(
            sources=[SourceRecord(source_id="policy-001", name="Mock Policy Registry", metadata={})]
        )

    async def get_versions(self) -> VersionsResponse:
        return VersionsResponse(versions=[VersionRecord(version_id="v1", timestamp="2026-01-01T00:00:00Z")])


class MockGovernanceClient:
    async def guardrail_check(self, request: GuardrailCheckRequest) -> GuardrailCheckResponse:
        lowered = request.content.lower()
        blocked_terms = ("weapon", "explosive", "sex", "porn", "سلاح", "متفجر", "إباحي")
        hits = [term for term in blocked_terms if term in lowered]
        if hits:
            return GuardrailCheckResponse(
                allowed=False,
                blocked=True,
                violations=[f"blocked_term:{term}" for term in hits],
                risk_score=0.95,
            )
        return GuardrailCheckResponse(allowed=True, blocked=False, violations=[], risk_score=0.02)

    async def audit(self, request: AuditLogRequest) -> None:
        return None


class MockWorkflowClient:
    async def create_ticket(self, request: TicketCreateRequest) -> TicketCreateResponse:
        return TicketCreateResponse(ticket_id="MOCK-TICKET-001", status="open", metadata={"mock": True})

    async def get_ticket_status(self, ticket_id: str) -> TicketStatusResponse:
        return TicketStatusResponse(ticket_id=ticket_id, status="open", metadata={"mock": True})


@dataclass
class IntegrationResult:
    data: Any
    used_fallback: bool = False
    fallback_reason: str | None = None


class IntegrationClients:
    def __init__(
        self,
        *,
        use_mocks: bool,
        knowledge_base_url: str,
        governance_base_url: str,
        workflow_base_url: str,
        timeout_s: float,
        retries: int,
    ) -> None:
        self.use_mocks = use_mocks
        self.mock_knowledge = MockKnowledgeClient()
        self.mock_governance = MockGovernanceClient()
        self.mock_workflow = MockWorkflowClient()
        self.real_knowledge = KnowledgeHTTPClient(knowledge_base_url, timeout_s=timeout_s, retries=retries)
        self.real_governance = GovernanceHTTPClient(governance_base_url, timeout_s=timeout_s, retries=retries)
        self.real_workflow = WorkflowHTTPClient(workflow_base_url, timeout_s=timeout_s, retries=retries)

    async def retrieve(self, query: str, top_k: int) -> IntegrationResult:
        if self.use_mocks:
            return IntegrationResult(data=await self.mock_knowledge.retrieve(query, top_k), used_fallback=True)
        try:
            return IntegrationResult(data=await self.real_knowledge.retrieve(query, top_k))
        except Exception as exc:
            logger.warning("Knowledge service fallback activated: %s", exc)
            return IntegrationResult(
                data=await self.mock_knowledge.retrieve(query, top_k),
                used_fallback=True,
                fallback_reason=str(exc),
            )

    async def guardrail_check(self, request: GuardrailCheckRequest) -> IntegrationResult:
        if self.use_mocks:
            return IntegrationResult(data=await self.mock_governance.guardrail_check(request), used_fallback=True)
        try:
            return IntegrationResult(data=await self.real_governance.guardrail_check(request))
        except Exception as exc:
            logger.warning("Governance service fallback activated: %s", exc)
            return IntegrationResult(
                data=await self.mock_governance.guardrail_check(request),
                used_fallback=True,
                fallback_reason=str(exc),
            )

    async def create_ticket(self, request: TicketCreateRequest) -> IntegrationResult:
        if self.use_mocks:
            return IntegrationResult(data=await self.mock_workflow.create_ticket(request), used_fallback=True)
        try:
            return IntegrationResult(data=await self.real_workflow.create_ticket(request))
        except Exception as exc:
            logger.warning("Workflow service fallback activated: %s", exc)
            return IntegrationResult(
                data=await self.mock_workflow.create_ticket(request),
                used_fallback=True,
                fallback_reason=str(exc),
            )

    async def send_audit(self, request: AuditLogRequest) -> IntegrationResult:
        if self.use_mocks:
            await self.mock_governance.audit(request)
            return IntegrationResult(data={"success": True}, used_fallback=True)
        try:
            await self.real_governance.audit(request)
            return IntegrationResult(data={"success": True})
        except Exception as exc:
            logger.warning("Governance audit fallback activated: %s", exc)
            await self.mock_governance.audit(request)
            return IntegrationResult(data={"success": True}, used_fallback=True, fallback_reason=str(exc))
