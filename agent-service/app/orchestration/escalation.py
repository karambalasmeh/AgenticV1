from __future__ import annotations

from typing import Any, Dict, Optional
from app.schemas.artifacts import Escalation, Validation, Confidence

class EscalationEngine:
    def evaluate(
        self,
        validation: Validation,
        confidence: Confidence,
        signals: Dict[str, Any] = None
    ) -> Escalation:
        # Ported logic from karam:
        # if (not valid_after_repair) or (confidence.level == "low"):
        #     triggered = True
        
        triggered = False
        reason = None
        
        if not validation.passed:
            triggered = True
            reason = "invalid_output"
        elif confidence.level == "low":
            triggered = True
            reason = "low_confidence"
            
        return Escalation(
            triggered=triggered,
            reason=reason,
            ticket=None
        )
