from fastapi import APIRouter, HTTPException, Query, Header
from fastapi.responses import StreamingResponse
from typing import List, Optional, Literal, Dict, AsyncGenerator
from uuid import uuid4
from pydantic import BaseModel
import json

from src.data_retrive.agent import DataRetrievalAgent
from src.models.search import SearchResponse, Citation, StreamingSearchResponse

router = APIRouter(prefix="/retrieve", tags=["retrieval"])

# Keep a single instance of the agent for the entire service
_agent: Optional[DataRetrievalAgent] = None

async def get_agent(model: Optional[str] = None) -> DataRetrievalAgent:
    """Get or create the DataRetrievalAgent instance."""
    global _agent
    if _agent is None:
        _agent = DataRetrievalAgent(model_name=model) if model else DataRetrievalAgent()
    return _agent

def get_or_create_session_id(x_session_id: Optional[str] = Header(None)) -> str:
    """Get existing session ID from header or create new one."""
    return x_session_id or str(uuid4())

async def stream_search_generator(
    agent: DataRetrievalAgent,
    query: str,
    doc_types: Optional[List[str]] = None,
    include_relationships: bool = False,
    search_type: str = "focused",
    session_id: str = None
) -> AsyncGenerator[str, None]:
    """Generate streaming search results.
    
    Args:
        agent: DataRetrievalAgent instance
        query: Search query
        doc_types: Optional list of document types to filter
        include_relationships: Whether to include relationships
        search_type: Type of search to perform
        session_id: Session ID for conversation context
    """
    async for chunk in agent.stream_search_knowledge(
        query=query,
        doc_types=doc_types,
        include_relationships=include_relationships,
        search_type=search_type,
        session_id=session_id
    ):
        # Convert the chunk to JSON and yield
        yield json.dumps(chunk.dict()) + "\n"

@router.get("/search/stream")
async def stream_search(
    query: str,
    doc_types: Optional[List[str]] = Query(None),
    include_relationships: bool = False,
    search_type: Literal["focused", "detailed", "timeline"] = "focused",
    model: Optional[str] = None,
    x_session_id: Optional[str] = Header(None)
) -> StreamingResponse:
    """
    Stream search results from the knowledge graph.
    
    Args:
        query: Search query string
        doc_types: Optional list of document types to filter by
        include_relationships: Whether to include document relationships
        search_type: Type of search to perform (focused, detailed, or timeline)
        model: Optional LLM model to use
        x_session_id: Optional session ID header
        
    Returns:
        Streaming response with JSON lines format
    """
    try:
        agent = await get_agent(model)
        session_id = get_or_create_session_id(x_session_id)
        
        return StreamingResponse(
            stream_search_generator(
                agent=agent,
                query=query,
                doc_types=doc_types,
                include_relationships=include_relationships,
                search_type=search_type,
                session_id=session_id
            ),
            media_type="application/x-ndjson"  # Newline-delimited JSON
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search", response_model=SearchResponse)
async def search_knowledge(
    query: str,
    doc_types: Optional[List[str]] = Query(None),
    include_relationships: bool = False,
    search_type: Literal["focused", "detailed", "timeline"] = "focused",
    model: Optional[str] = None,
    x_session_id: Optional[str] = Header(None)
) -> SearchResponse:
    """
    Search for information in the knowledge graph.
    
    Args:
        query: Search query string
        doc_types: Optional list of document types to filter by
        include_relationships: Whether to include document relationships
        search_type: Type of search to perform (focused, detailed, or timeline)
        model: Optional LLM model to use
        x_session_id: Optional session ID header
    """
    try:
        agent = await get_agent(model)
        session_id = get_or_create_session_id(x_session_id)
        
        result = await agent.search_knowledge(
            query=query,
            doc_types=doc_types,
            include_relationships=include_relationships,
            search_type=search_type,
            session_id=session_id
        )
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Parse the response to extract answer and citations
        response = result["summary"].split("\nSource:", 1)
        answer = response[0].replace("Answer:", "").strip()
        
        # If no answer found, provide a clear message
        if not answer or answer == "No results found":
            return SearchResponse(
                status="success",
                answer="No information found for this query.",
                citations=[],
                query=query,
                doc_types=doc_types,
                search_type=search_type
            )
        
        # Extract citations
        citations = []
        if len(response) > 1:
            citation_text = response[1].strip()
            # Parse citation in format [Document Name | Date | Section]
            citation_parts = citation_text.strip("[]").split("|")
            citations.append(Citation(
                document=citation_parts[0].strip(),
                date=citation_parts[1].strip() if len(citation_parts) > 1 else None,
                section=citation_parts[2].strip() if len(citation_parts) > 2 else None
            ))
        
        return SearchResponse(
            status=result["status"],
            answer=answer,
            citations=citations,
            query=query,
            doc_types=doc_types,
            search_type=search_type
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversation/history")
async def get_conversation_history(
    x_session_id: Optional[str] = Header(None)
) -> dict:
    """Get the recent conversation history for a session."""
    try:
        agent = await get_agent()
        session_id = get_or_create_session_id(x_session_id)
        history = agent.get_conversation_history(session_id=session_id)
        return {
            "status": "success",
            "history": history,
            "session_id": session_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/conversation/clear")
async def clear_conversation_history(
    x_session_id: Optional[str] = Header(None)
) -> dict:
    """Clear the conversation history for a session."""
    try:
        agent = await get_agent()
        session_id = get_or_create_session_id(x_session_id)
        agent.clear_conversation_history(session_id=session_id)
        return {
            "status": "success",
            "message": "Conversation history cleared",
            "session_id": session_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search/batch", response_model=List[SearchResponse])
async def batch_search(
    queries: List[str] = Query(...),
    doc_types: Optional[List[str]] = Query(None),
    include_relationships: bool = False,
    search_type: Literal["focused", "detailed", "timeline"] = "focused",
    model: Optional[str] = None,
    x_session_id: Optional[str] = Header(None)
) -> List[SearchResponse]:
    """
    Perform multiple searches in the knowledge graph.
    
    Args:
        queries: List of search queries
        doc_types: Optional list of document types to filter by
        include_relationships: Whether to include document relationships
        search_type: Type of search to perform (focused, detailed, or timeline)
        model: Optional LLM model to use
        x_session_id: Optional session ID header
    """
    agent = await get_agent(model)
    session_id = get_or_create_session_id(x_session_id)
    responses = []
    
    try:
        for query in queries:
            result = await agent.search_knowledge(
                query=query,
                doc_types=doc_types,
                include_relationships=include_relationships,
                search_type=search_type,
                session_id=session_id
            )
            
            # Parse the response to extract answer and citations
            response = result["summary"].split("\nSource:", 1)
            answer = response[0].replace("Answer:", "").strip()
            
            # Extract citations
            citations = []
            if len(response) > 1:
                citation_text = response[1].strip()
                # Parse citation in format [Document Name | Date | Section]
                citation_parts = citation_text.strip("[]").split("|")
                citations.append(Citation(
                    document=citation_parts[0].strip(),
                    date=citation_parts[1].strip() if len(citation_parts) > 1 else None,
                    section=citation_parts[2].strip() if len(citation_parts) > 2 else None
                ))
            
            responses.append(
                SearchResponse(
                    status=result["status"],
                    answer=answer,
                    citations=citations,
                    query=result["query"],
                    doc_types=result.get("doc_types"),
                    search_type=result.get("search_type", "focused")
                )
            )
            
    finally:
        return responses 