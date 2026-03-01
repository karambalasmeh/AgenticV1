"""Deterministic self-verification heuristics for draft validation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence
import re

from app.schemas.artifacts import Citation, ValidationIssue


@dataclass(frozen=True)
class SelfVerificationConfig:
    """Tunable knobs that keep the heuristics predictable."""

    long_answer_word_threshold: int = 120
    min_citations_for_long_answer: int = 2
    placeholder_markers: tuple[str, ...] = ("[citation needed]", "[source pending]", "TODO", "TBD")
    required_sections: tuple[str, ...] = ("summary", "analysis", "recommendation")


class SelfVerifier:
    """Runs lightweight checks over the draft plus provided citations."""

    def __init__(self, config: SelfVerificationConfig | None = None) -> None:
        self.config = config or SelfVerificationConfig()

    def run(self, answer_draft: str, citations: Sequence[Citation]) -> List[ValidationIssue]:
        text = (answer_draft or "").strip()
        citation_list = list(citations)
        issues: List[ValidationIssue] = []

        if self._has_missing_citations(text, citation_list):
            issues.append(
                ValidationIssue(
                    type="missing_citations",
                    severity="high",
                    details="Claims or statistics are present but no usable citations were supplied.",
                )
            )

        if self._has_insufficient_evidence(text, citation_list):
            issues.append(
                ValidationIssue(
                    type="insufficient_evidence",
                    severity="medium",
                    details="Answer length suggests at least two sources, but fewer were provided.",
                )
            )

        if self._has_incomplete_structure(text):
            issues.append(
                ValidationIssue(
                    type="incomplete_structure",
                    severity="medium",
                    details="Draft is missing the expected Summary/Analysis/Recommendation scaffolding.",
                )
            )

        return issues

    # Helper detection routines -------------------------------------------------

    def _has_missing_citations(self, text: str, citations: Sequence[Citation]) -> bool:
        if not text:
            return False

        normalized = text.lower()
        has_claim_language = bool(
            re.search(r"\b(study|report|data|analysis|survey|figure|percent|evidence|indicates)\b", normalized)
        )
        placeholders_present = any(marker.lower() in normalized for marker in self.config.placeholder_markers)
        long_answer_needs_citation = len(normalized.split()) >= 60

        needs_support = has_claim_language or placeholders_present or long_answer_needs_citation
        return needs_support and len(list(citations)) == 0

    def _has_insufficient_evidence(self, text: str, citations: Sequence[Citation]) -> bool:
        if not text:
            return False

        word_count = len(text.split())
        if word_count < self.config.long_answer_word_threshold:
            return False

        return len(list(citations)) < self.config.min_citations_for_long_answer

    def _has_incomplete_structure(self, text: str) -> bool:
        if not text:
            return True

        section_headers = self._extract_section_headers(text)
        if len(section_headers) < 2:
            return True

        required = set(self.config.required_sections)
        seen = {header.lower() for header in section_headers}
        missing_required = not required.intersection(seen)
        contains_placeholder = any(marker in text for marker in ("TBD", "??", "..."))

        return missing_required or contains_placeholder

    @staticmethod
    def _extract_section_headers(text: str) -> List[str]:
        headers: List[str] = []
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue

            if ":" in stripped:
                possible_header = stripped.split(":", 1)[0].strip()
                if 1 <= len(possible_header.split()) <= 3:
                    headers.append(possible_header)
                    continue

            if re.match(r"^(?:\d+\.|\d+\)|[-*•])", stripped):
                headers.append(stripped)

        return headers
