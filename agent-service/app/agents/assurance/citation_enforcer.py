"""Citation policy enforcement heuristics."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence, Tuple
import math
import re
from collections import Counter

from app.schemas.artifacts import Citation, ValidationIssue


@dataclass(frozen=True)
class CitationPolicy:
    """Simple deterministic citation policy."""

    sentences_per_citation: int = 2
    min_relevance_score: float = 0.05
    allow_duplicate_entries: int = 1
    require_chunk_id: bool = True
    numeric_keywords: Tuple[str, ...] = ("percent", "increase", "decrease", "billion", "million")


class CitationEnforcer:
    """Checks whether claims are grounded per the policy."""

    def __init__(self, policy: CitationPolicy | None = None) -> None:
        self.policy = policy or CitationPolicy()

    def enforce(self, answer_draft: str, citations: Sequence[Citation]) -> List[ValidationIssue]:
        text = (answer_draft or "").strip()
        issues: List[ValidationIssue] = []

        invalid_count = self._count_invalid_citations(citations)
        if invalid_count:
            issues.append(
                ValidationIssue(
                    type="invalid_citations",
                    severity="low",
                    details=f"{invalid_count} citation(s) missing identifiers or below relevance threshold.",
                )
            )

        duplicate_count = self._count_duplicates(citations)
        if duplicate_count:
            issues.append(
                ValidationIssue(
                    type="duplicate_citations",
                    severity="low",
                    details=f"{duplicate_count} duplicate citation reference(s) detected.",
                )
            )

        coverage_issue = self._check_claim_coverage(text, len(citations))
        if coverage_issue:
            issues.append(coverage_issue)

        return issues

    def _count_invalid_citations(self, citations: Sequence[Citation]) -> int:
        invalid = 0
        for cite in citations:
            if not cite.source_id:
                invalid += 1
                continue

            if self.policy.require_chunk_id and not cite.chunk_id:
                invalid += 1
                continue

            if cite.relevance_score is not None and cite.relevance_score < self.policy.min_relevance_score:
                invalid += 1
        return invalid

    def _count_duplicates(self, citations: Sequence[Citation]) -> int:
        if not citations:
            return 0

        counter = Counter((cite.source_id, cite.chunk_id) for cite in citations)
        duplicates = 0
        for key, count in counter.items():
            if not key[0]:
                continue
            if count > self.policy.allow_duplicate_entries:
                duplicates += count - self.policy.allow_duplicate_entries
        return duplicates

    def _check_claim_coverage(self, text: str, citation_count: int) -> ValidationIssue | None:
        if not text:
            return None

        sentences = [segment.strip() for segment in re.split(r"[.!?]", text) if segment.strip()]
        if not sentences:
            return None

        claim_sentences = [s for s in sentences if self._sentence_needs_citation(s)]
        if not claim_sentences:
            return None

        required = max(1, math.ceil(len(claim_sentences) / self.policy.sentences_per_citation))
        if citation_count >= required:
            return None

        missing = required - citation_count
        return ValidationIssue(
            type="unsupported_claims",
            severity="medium",
            details=f"{missing} claim-centric sentence(s) are missing supporting citations.",
        )

    def _sentence_needs_citation(self, sentence: str) -> bool:
        normalized = sentence.lower()
        if any(keyword in normalized for keyword in self.policy.numeric_keywords):
            return True
        return bool(re.search(r"\d", sentence))
