from __future__ import annotations

import re

from app.domain.models import OutputLanguage

ARABIC_RE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]")


def detect_language(text: str) -> OutputLanguage:
    if text and ARABIC_RE.search(text):
        return "ar"
    return "en"


def language_instruction(language: OutputLanguage) -> str:
    if language == "ar":
        return "Respond only in Arabic."
    return "Respond only in English."
