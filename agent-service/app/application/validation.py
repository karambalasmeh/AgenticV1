from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from app.application.language import detect_language
from app.domain.contracts import KnowledgeChunk
from app.domain.models import Citation, OutputLanguage, ValidationIssue


@dataclass(frozen=True)
class ValidationConfig:
    require_source_fields: bool = True
    contradiction_terms: tuple[tuple[str, str], ...] = (
        ("allow", "forbid"),
        ("increase", "decrease"),
        ("safe", "dangerous"),
        ("مسموح", "ممنوع"),
        ("زيادة", "انخفاض"),
    )


class ResponseValidator:
    def __init__(self, config: ValidationConfig | None = None) -> None:
        self.config = config or ValidationConfig()

    def validate(
        self,
        answer: str,
        expected_language: OutputLanguage,
        citations: Sequence[Citation],
        include_evidence: bool,
        evidence_chunks: Sequence[KnowledgeChunk],
    ) -> list[ValidationIssue]:
        issues: list[ValidationIssue] = []
        normalized = (answer or "").strip()

        if not normalized:
            issues.append(self._issue("empty_answer", "high", "Answer draft is empty."))
            return issues

        if detect_language(normalized) != expected_language:
            issues.append(
                self._issue(
                    "language_mismatch",
                    "high",
                    f"Answer language does not match expected `{expected_language}`.",
                )
            )

        if include_evidence:
            if not citations:
                issues.append(self._issue("missing_citations", "high", "Evidence output requested but citations are empty."))
            for citation in citations:
                if self.config.require_source_fields and (not citation.source_id or not citation.chunk_id):
                    issues.append(self._issue("invalid_citation", "high", "Citation requires source_id and chunk_id."))

        if self._has_term_conflict(normalized):
            issues.append(self._issue("conflicting_evidence", "medium", "Answer contains contradictory claims."))

        if self._evidence_contradicts_answer(normalized, evidence_chunks):
            issues.append(
                self._issue(
                    "answer_evidence_conflict",
                    "medium",
                    "Answer appears to contradict retrieved evidence.",
                )
            )

        return self._dedupe(issues)

    def recommend_actions(self, issues: Sequence[ValidationIssue]) -> list[str]:
        mapping = {
            "empty_answer": "Regenerate a complete answer.",
            "language_mismatch": "Rewrite answer in detected user language only.",
            "missing_citations": "Attach at least one valid citation.",
            "invalid_citation": "Provide citations with source_id and chunk_id.",
            "conflicting_evidence": "Resolve contradictory statements before response.",
            "answer_evidence_conflict": "Align claims with retrieved evidence.",
        }
        recommended: list[str] = []
        for issue in issues:
            action = mapping.get(issue.type)
            if action and action not in recommended:
                recommended.append(action)
        return recommended

    def _has_term_conflict(self, answer: str) -> bool:
        lowered = answer.lower()
        for positive, negative in self.config.contradiction_terms:
            if positive in lowered and negative in lowered:
                return True
        return False

    def _evidence_contradicts_answer(self, answer: str, evidence_chunks: Sequence[KnowledgeChunk]) -> bool:
        lowered_answer = answer.lower()
        allow_markers = ("allow", "allowed", "permitted", "مسموح")
        deny_markers = ("forbid", "forbidden", "ban", "ممنوع")
        evidence_text = " ".join(chunk.text.lower() for chunk in evidence_chunks)
        answer_allows = any(token in lowered_answer for token in allow_markers)
        answer_denies = any(token in lowered_answer for token in deny_markers)
        evidence_allows = any(token in evidence_text for token in allow_markers)
        evidence_denies = any(token in evidence_text for token in deny_markers)
        return (answer_allows and evidence_denies) or (answer_denies and evidence_allows)

    @staticmethod
    def _issue(issue_type: str, severity: str, details: str) -> ValidationIssue:
        return ValidationIssue(type=issue_type, severity=severity, details=details)

    @staticmethod
    def _dedupe(issues: Sequence[ValidationIssue]) -> list[ValidationIssue]:
        seen: set[tuple[str, str]] = set()
        unique: list[ValidationIssue] = []
        for issue in issues:
            key = (issue.type, issue.details)
            if key in seen:
                continue
            seen.add(key)
            unique.append(issue)
        return unique
