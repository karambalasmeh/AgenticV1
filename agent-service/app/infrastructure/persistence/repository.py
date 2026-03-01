from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.infrastructure.persistence.database import session_scope
from app.infrastructure.persistence.models import (
    ArtifactORM,
    AuditLogORM,
    ConversationMessageORM,
    MemoryJobORM,
    TicketORM,
    ViolationORM,
)


@dataclass
class PersistencePayload:
    request_id: str
    user_id: str
    conversation_id: str
    route: str
    latency_ms: int
    result: str
    policy_flags: dict[str, Any] = field(default_factory=dict)
    question: str = ""
    answer: str = ""
    language: str = "en"
    decision_trace: list[dict[str, Any]] = field(default_factory=list)
    confidence: dict[str, Any] = field(default_factory=dict)
    citations: list[dict[str, Any]] = field(default_factory=list)
    evidence_refs: list[dict[str, Any]] = field(default_factory=list)
    validation_issues: list[dict[str, Any]] = field(default_factory=list)
    explanation: dict[str, Any] = field(default_factory=dict)
    ticket: dict[str, Any] | None = None
    fallback_used: bool = False


class PersistenceRepository:
    def increment_violation(self, user_id: str, reason: str) -> int:
        with session_scope() as session:
            record = session.get(ViolationORM, user_id)
            now = datetime.now(timezone.utc)
            if record is None:
                record = ViolationORM(user_id=user_id, count=1, reason=reason, last_violation_at=now)
                session.add(record)
                return 1
            record.count += 1
            record.reason = reason
            record.last_violation_at = now
            return record.count

    def get_violation_count(self, user_id: str) -> int:
        with session_scope() as session:
            record = session.get(ViolationORM, user_id)
            return int(record.count) if record else 0

    def persist_query(self, payload: PersistencePayload) -> None:
        with session_scope() as session:
            session.merge(
                AuditLogORM(
                    request_id=payload.request_id,
                    user_id=payload.user_id,
                    route=payload.route,
                    latency_ms=payload.latency_ms,
                    result=payload.result,
                    policy_flags=payload.policy_flags,
                    fallback_used=payload.fallback_used,
                )
            )
            session.add(
                ConversationMessageORM(
                    conversation_id=payload.conversation_id,
                    user_id=payload.user_id,
                    request_id=payload.request_id,
                    question=payload.question,
                    answer=payload.answer,
                    language=payload.language,
                )
            )
            session.add(
                ArtifactORM(
                    request_id=payload.request_id,
                    decision_trace=payload.decision_trace,
                    confidence=payload.confidence,
                    citations=payload.citations,
                    evidence_refs=payload.evidence_refs,
                    validation_issues=payload.validation_issues,
                    explanation=payload.explanation,
                )
            )
            if payload.ticket:
                session.add(
                    TicketORM(
                        request_id=payload.request_id,
                        ticket_id=str(payload.ticket.get("ticket_id") or ""),
                        status=str(payload.ticket.get("status") or "open"),
                        ministry=str(payload.ticket.get("ministry") or "unknown"),
                        payload_snapshot=payload.ticket,
                    )
                )
            session.add(
                MemoryJobORM(
                    request_id=payload.request_id,
                    user_id=payload.user_id,
                    conversation_id=payload.conversation_id,
                    summary=_build_summary(payload.question, payload.answer),
                    preferences=_extract_preferences(payload.question),
                )
            )


def _build_summary(question: str, answer: str) -> str:
    q = (question or "").strip()
    a = (answer or "").strip()
    if not q and not a:
        return "Empty exchange."
    return f"Q: {q[:280]} | A: {a[:280]}"


def _extract_preferences(question: str) -> dict[str, Any]:
    lowered = (question or "").lower()
    preferences: dict[str, Any] = {}
    if "brief" in lowered or "short" in lowered or "مختصر" in lowered:
        preferences["response_style"] = "brief"
    if "detailed" in lowered or "تفصيلي" in lowered:
        preferences["response_style"] = "detailed"
    if "arabic" in lowered or "عربي" in lowered:
        preferences["language_preference"] = "ar"
    if "english" in lowered:
        preferences["language_preference"] = "en"
    return preferences
