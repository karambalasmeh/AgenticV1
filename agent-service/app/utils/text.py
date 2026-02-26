from __future__ import annotations

import re
from typing import Literal

DetectedLanguage = Literal["ar", "en"]

_AR_RE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]")


def detect_language_from_text(text: str) -> DetectedLanguage:
    if text and _AR_RE.search(text):
        return "ar"
    return "en"