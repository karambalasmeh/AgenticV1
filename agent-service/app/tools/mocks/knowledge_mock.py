from typing import List, Optional
from datetime import datetime, timezone

from app.tools.contracts.knowledge_contracts import (
    RetrieveRequest,
    RetrieveResponse,
    KnowledgeDocument,
    SourcesResponse,
    SourceMetadata,
    VersionsResponse,
    VersionInfo,
)


class MockKnowledgeClient:
    # English comments only
    def __init__(self, scenario: str = "SUCCESS_EVIDENCE"):
        self.scenario = scenario

    async def retrieve(self, request: RetrieveRequest) -> RetrieveResponse:
        if self.scenario == "MISSING_DOCS":
            return RetrieveResponse(documents=[])
        
        if self.scenario == "CONFLICTING_EVIDENCE":
            return RetrieveResponse(
                documents=[
                    KnowledgeDocument(id="doc1", content="Topic A is allowed.", metadata={"source": "policy_v1"}),
                    KnowledgeDocument(id="doc2", content="Topic A is strictly forbidden.", metadata={"source": "policy_v2"}),
                ]
            )
        
        # Default: SUCCESS_EVIDENCE
        return RetrieveResponse(
            documents=[
                KnowledgeDocument(
                    id="doc_success",
                    content=f"Found evidence for: {request.query}. Policy matches criteria.",
                    metadata={"relevance": 0.95}
                )
            ]
        )

    async def get_sources(self) -> SourcesResponse:
        return SourcesResponse(
            sources=[
                SourceMetadata(source_id="src1", name="Official Policy Portal", url="https://policy.gov.kw"),
            ]
        )

    async def get_versions(self) -> VersionsResponse:
        return VersionsResponse(
            versions=[
                VersionInfo(version_id="v1.2.0", timestamp=datetime.now(timezone.utc).isoformat(), author="Admin"),
            ]
        )
