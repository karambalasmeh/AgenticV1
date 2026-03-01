<<<<<<< HEAD
from __future__ import annotations

from typing import List
from app.schemas.artifacts import Validation, Citation
from app.agents.assurance.basic_validator import basic_validate
from app.core.config import settings

class Validator:
    def __init__(self):
        self.require_citations = getattr(settings, "REQUIRE_CITATIONS", False)

    def run(self, answer_draft: str, citations: List[Citation]) -> Validation:
        passed, issues = basic_validate(answer_draft, citations, self.require_citations)
        return Validation(passed=passed, issues=issues)
=======
"""Validation orchestrator covering all assurance heuristics."""
from __future__ import annotations

from typing import Iterable, List, Sequence

from app.schemas.artifacts import Citation, Validation, ValidationIssue
from .self_verifier import SelfVerifier
from .conflict_detector import ConflictDetector
from .citation_enforcer import CitationEnforcer


SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


class Validator:
    """Runs the full suite of deterministic quality checks."""

    def __init__(
        self,
        self_verifier: SelfVerifier | None = None,
        conflict_detector: ConflictDetector | None = None,
        citation_enforcer: CitationEnforcer | None = None,
    ) -> None:
        self.self_verifier = self_verifier or SelfVerifier()
        self.conflict_detector = conflict_detector or ConflictDetector()
        self.citation_enforcer = citation_enforcer or CitationEnforcer()

    def run(self, answer_draft: str, citations: Sequence[Citation]) -> Validation:
        checks: Sequence[Iterable[ValidationIssue]] = (
            self.self_verifier.run(answer_draft, citations),
            self.conflict_detector.detect(answer_draft, citations),
            self.citation_enforcer.enforce(answer_draft, citations),
        )

        issues = self._dedupe_issues([issue for bucket in checks for issue in bucket])
        issues.sort(key=lambda issue: (SEVERITY_ORDER.get(issue.severity, 3), issue.type))

        return Validation(passed=len(issues) == 0, issues=issues)

    def recommend_actions(self, issues: Sequence[ValidationIssue]) -> List[str]:
        """Map detected issues to actionable nudges for upstream agents."""
        if not issues:
            return []

        action_map = {
            "missing_citations": "Attach at least one trusted source that backs key claims.",
            "insufficient_evidence": "Add a second independent source for lengthy answers.",
            "incomplete_structure": "Reformat into Summary/Analysis/Recommendation sections.",
            "conflicting_evidence": "Resolve contradictory statements or clarify timeframe.",
            "conflicting_sources": "Drop weaker excerpts or explain why sources disagree.",
            "unsupported_claims": "Cite the numeric or impactful claims.",
            "invalid_citations": "Provide both source_id and chunk_id with adequate relevance.",
            "duplicate_citations": "Deduplicate repeated citations pointing to same chunk.",
        }

        recommendations: List[str] = []
        for issue in issues:
            if issue.type in action_map and action_map[issue.type] not in recommendations:
                recommendations.append(action_map[issue.type])
        return recommendations

    @staticmethod
    def _dedupe_issues(issues: Sequence[ValidationIssue]) -> List[ValidationIssue]:
        seen: set[tuple[str, str]] = set()
        unique: List[ValidationIssue] = []
        for issue in issues:
            key = (issue.type, issue.details)
            if key in seen:
                continue
            seen.add(key)
            unique.append(issue)
        return unique
>>>>>>> main
