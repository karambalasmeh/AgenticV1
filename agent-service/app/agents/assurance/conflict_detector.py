"""Simple, deterministic conflict detection heuristics."""
from __future__ import annotations

from collections import defaultdict
from typing import List, Sequence, Set
import re

from app.schemas.artifacts import Citation, ValidationIssue


class ConflictDetector:
    """Flags obvious contradictions within the same answer."""

    CONTRADICTION_TERM_PAIRS: Sequence[tuple[str, str]] = (
        ("increase", "decrease"),
        ("improves", "worsens"),
        ("supports", "refutes"),
        ("confirmed", "denied"),
        ("safe", "dangerous"),
    )

    def detect(self, answer_draft: str, citations: Sequence[Citation]) -> List[ValidationIssue]:
        text = (answer_draft or "").lower()
        issues: List[ValidationIssue] = []

        if self._has_conflicting_language(text):
            issues.append(
                ValidationIssue(
                    type="conflicting_evidence",
                    severity="medium",
                    details="Draft asserts mutually exclusive outcomes (e.g., increase vs decrease).",
                )
            )

        conflicting_sources = self._locate_conflicting_sources(citations)
        if conflicting_sources:
            joined = ", ".join(sorted(conflicting_sources))
            issues.append(
                ValidationIssue(
                    type="conflicting_sources",
                    severity="medium",
                    details=f"Multiple excerpts from {joined} conflict with each other.",
                )
            )

        return issues

    def _has_conflicting_language(self, text: str) -> bool:
        if not text:
            return False

        for pos_term, neg_term in self.CONTRADICTION_TERM_PAIRS:
            if re.search(rf"\b{re.escape(pos_term)}\b", text) and re.search(
                rf"\b{re.escape(neg_term)}\b", text
            ):
                # Require the contradictory terms to appear within a short span.
                if self._terms_close(text, pos_term, neg_term):
                    return True
        return False

    @staticmethod
    def _terms_close(text: str, term_a: str, term_b: str, window: int = 240) -> bool:
        idx_a = text.find(term_a)
        idx_b = text.find(term_b)
        if idx_a == -1 or idx_b == -1:
            return False
        return abs(idx_a - idx_b) <= window

    def _locate_conflicting_sources(self, citations: Sequence[Citation]) -> Set[str]:
        conflicts: Set[str] = set()
        grouped = defaultdict(list)
        for cite in citations:
            grouped[cite.source_id].append(cite)

        for source_id, items in grouped.items():
            if len(items) < 2:
                continue

            relevance_scores = [cite.relevance_score for cite in items]
            if max(relevance_scores) - min(relevance_scores) >= 0.5:
                conflicts.add(source_id)
                continue

            titles = [((cite.title or "") + " " + (cite.publisher or "")).lower() for cite in items]
            support_terms = ("support", "confirm", "favorable")
            refute_terms = ("refute", "challenge", "criticism")
            has_supporting = any(any(term in title for term in support_terms) for title in titles)
            has_refuting = any(any(term in title for term in refute_terms) for title in titles)
            if has_supporting and has_refuting:
                conflicts.add(source_id)

        return conflicts
