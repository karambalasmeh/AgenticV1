from __future__ import annotations

from app.domain.models import Citation


def has_minimum_citation_fields(citation: Citation) -> bool:
    return bool(citation.source_id and citation.chunk_id)
