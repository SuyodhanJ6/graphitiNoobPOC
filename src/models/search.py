from typing import List, Optional, Dict, Any
from pydantic import BaseModel

class Citation(BaseModel):
    """Model for document citations."""
    document: str
    date: Optional[str] = None
    section: Optional[str] = None

class SearchResponse(BaseModel):
    """Model for search response."""
    status: str
    answer: str
    citations: List[Citation]
    query: str
    doc_types: Optional[List[str]] = None
    search_type: str = "focused"

class StreamingSearchResponse(BaseModel):
    """Model for streaming search response chunks."""
    chunk: str
    type: str = "token"  # can be "token", "citation", "end"
    metadata: Optional[Dict[str, Any]] = None 