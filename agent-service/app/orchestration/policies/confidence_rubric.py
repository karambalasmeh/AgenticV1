from __future__ import annotations

from typing import Any, Dict, List
from app.schemas.artifacts import Confidence, ValidationIssue
from app.orchestration.policies.basic_confidence import score_confidence

class ConfidenceRubric:
    def score(
        self,
        answer_draft: str,
        citations: List[Any],
        validation_issues: List[ValidationIssue],
        signals: Dict[str, Any] = None,
    ) -> Confidence:
        # We need to map the arguments to score_confidence
        # score_confidence(valid, issues, is_complex, citations_count)
        
        # Note: 'valid' is usually calculated externally, but here we can infer it
        valid = not any(i.severity == "high" for i in validation_issues)
        is_complex = signals.get("is_complex", False) if signals else False
        
        score, level, rationale, out_signals = score_confidence(
            valid=valid,
            issues=validation_issues,
            is_complex=is_complex,
            citations_count=len(citations),
        )
        
        # Merge input signals if provided
        if signals:
            out_signals.update(signals)
            
        return Confidence(
            score=score,
            level=level,
            rationale=rationale,
            signals=out_signals
        )
