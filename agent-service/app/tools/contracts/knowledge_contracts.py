from typing import List, Optional, Any
from pydantic import BaseModel


class KnowledgeDocument(BaseModel):
    # English comments only
    id: str
    content: str
    metadata: dict[str, Any] = {}


class RetrieveRequest(BaseModel):
    # English comments only
    query: str
    limit: int = 5


class RetrieveResponse(BaseModel):
    # English comments only
    documents: List[KnowledgeDocument]


class SourceMetadata(BaseModel):
    # English comments only
    source_id: str
    name: str
    url: Optional[str] = None


class SourcesResponse(BaseModel):
    # English comments only
    sources: List[SourceMetadata]


class VersionInfo(BaseModel):
    # English comments only
    version_id: str
    timestamp: str
    author: Optional[str] = None


class VersionsResponse(BaseModel):
    # English comments only
    versions: List[VersionInfo]
