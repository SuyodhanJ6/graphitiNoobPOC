from typing import Dict, Any, Optional, List, AsyncGenerator
import asyncio
from contextlib import asynccontextmanager

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.callbacks import AsyncCallbackHandler
from langchain_core.outputs import LLMResult

from langgraph.prebuilt import create_react_agent

from src.config.settings import (
    OPENAI_API_KEY,
    DEFAULT_MODEL,
    CONVERSATION_MEMORY_SIZE
)
from src.utils.mcp_client import setup_mcp_client, cleanup_mcp_client
from src.prompts.retrieval_prompts import RetrievalPrompts
from src.utils.session_manager import get_session_manager
from src.models.search import StreamingSearchResponse

class StreamingHandler(AsyncCallbackHandler):
    """Custom callback handler for streaming responses."""
    
    def __init__(self):
        super().__init__()
        self.queue = asyncio.Queue()
        self.is_finished = False
        self._done = asyncio.Event()
    
    async def on_llm_new_token(self, token: str, **kwargs) -> None:
        """Handle new tokens as they are generated."""
        await self.queue.put(token)
    
    async def on_llm_end(self, response: LLMResult, **kwargs) -> None:
        """Handle the end of LLM response generation."""
        self.is_finished = True
        self._done.set()
    
    async def on_llm_error(self, error: Exception, **kwargs) -> None:
        """Handle LLM errors."""
        self.is_finished = True
        self._done.set()
        await self.queue.put(f"Error: {str(error)}")
    
    async def aiter(self):
        """Async iterator for streaming tokens."""
        try:
            while not self.is_finished or not self.queue.empty():
                try:
                    token = await self.queue.get()
                    yield token
                except asyncio.QueueEmpty:
                    if self._done.is_set():
                        break
                    await asyncio.sleep(0.1)
                    continue
        except asyncio.CancelledError:
            self.is_finished = True
            self._done.set()
            raise
        finally:
            self._done.set()

class DataRetrievalAgent:
    """Agent responsible for searching and retrieving information from the knowledge graph."""
    
    def __init__(self, model_name: str = DEFAULT_MODEL, session_id: Optional[str] = None):
        self.model_name = model_name
        self.llm = None
        self.agent = None
        self.mcp_client = None
        self.prompts = RetrievalPrompts()
        self.session_id = session_id
        self._session_manager = get_session_manager()
    
    async def setup(self):
        """Initialize the agent and its dependencies."""
        if self.agent is not None:
            return
            
        self.llm = ChatOpenAI(
            model=self.model_name,
            api_key=OPENAI_API_KEY,
            streaming=False
        )
        
        self.mcp_client = await setup_mcp_client()
        mcp_tools = self.mcp_client.get_tools()
        
        self.agent = create_react_agent(
            self.llm,
            mcp_tools,
            prompt=self.prompts.get_focused_search_prompt("")
        )

    @property
    def memory(self):
        """Get the memory manager for the current session."""
        if not self.session_id:
            raise ValueError("Session ID is required for memory operations")
        return self._session_manager.get_memory(self.session_id)
    
    @asynccontextmanager
    async def _setup_streaming(self):
        """Setup streaming with proper resource cleanup."""
        callback_handler = StreamingHandler()
        self.llm = ChatOpenAI(
            model=self.model_name,
            api_key=OPENAI_API_KEY,
            streaming=True,
            callbacks=[callback_handler]
        )
        
        try:
            self.mcp_client = await setup_mcp_client()
            mcp_tools = self.mcp_client.get_tools()
            
            self.agent = create_react_agent(
                self.llm,
                mcp_tools,
                prompt=self.prompts.get_focused_search_prompt("")
            )
            
            yield callback_handler
            
        finally:
            if self.mcp_client:
                await cleanup_mcp_client(self.mcp_client)
            callback_handler.is_finished = True

    async def stream_search_knowledge(
        self, 
        query: str, 
        doc_types: Optional[List[str]] = None,
        include_relationships: bool = False,
        search_type: str = "focused",
        session_id: Optional[str] = None
    ) -> AsyncGenerator[StreamingSearchResponse, None]:
        """Stream search results from the knowledge graph."""
        effective_session_id = session_id or self.session_id
        if not effective_session_id:
            raise ValueError("Session ID is required for search operations")
        
        try:
            session_memory = self._session_manager.get_memory(effective_session_id)
            chat_history = session_memory.get_formatted_history()
            history_context = f"\nPrevious conversation context:\n{chat_history}\n" if chat_history else ""
            
            if search_type == "detailed":
                prompt = self.prompts.get_detailed_search_prompt(
                    query, doc_types, include_relationships
                )
            elif search_type == "timeline":
                prompt = self.prompts.get_timeline_search_prompt(
                    query, doc_types
                )
            else:
                prompt = self.prompts.get_focused_search_prompt(
                    query, doc_types, include_relationships
                )
            
            prompt_with_history = f"{history_context}\n{prompt}"
            
            async with self._setup_streaming() as callback_handler:
                task = asyncio.create_task(
                    self.agent.ainvoke({
                        "messages": [HumanMessage(content=prompt_with_history)]
                    })
                )
                
                collected_tokens = []
                try:
                    async for token in callback_handler.aiter():
                        collected_tokens.append(token)
                        yield StreamingSearchResponse(
                            chunk=token,
                            type="token"
                        )
                    
                    result = await task
                    response = "".join(collected_tokens)
                    
                    if "\nSource:" in response:
                        answer, citations = response.split("\nSource:", 1)
                        citation_parts = citations.strip("[]").split("|")
                        yield StreamingSearchResponse(
                            chunk="",
                            type="citation",
                            metadata={
                                "document": citation_parts[0].strip(),
                                "date": citation_parts[1].strip() if len(citation_parts) > 1 else None,
                                "section": citation_parts[2].strip() if len(citation_parts) > 2 else None
                            }
                        )
                    
                    session_memory.add_interaction(query, response)
                    
                    yield StreamingSearchResponse(
                        chunk="",
                        type="end",
                        metadata={
                            "status": "success",
                            "query": query,
                            "doc_types": doc_types,
                            "search_type": search_type,
                            "session_id": effective_session_id
                        }
                    )
                    
                except Exception as e:
                    yield StreamingSearchResponse(
                        chunk=str(e),
                        type="error",
                        metadata={
                            "status": "error",
                            "query": query,
                            "session_id": effective_session_id
                        }
                    )
                finally:
                    if not task.done():
                        task.cancel()
                        try:
                            await task
                        except asyncio.CancelledError:
                            pass
                
        except Exception as e:
            yield StreamingSearchResponse(
                chunk=str(e),
                type="error",
                metadata={
                    "status": "error",
                    "query": query,
                    "session_id": effective_session_id
                }
            )

    async def search_knowledge(
        self, 
        query: str, 
        doc_types: Optional[List[str]] = None,
        include_relationships: bool = False,
        search_type: str = "focused",  # Can be "focused", "detailed", or "timeline"
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Search for information in the knowledge graph.
        
        Args:
            query: Search query
            doc_types: Optional list of document types to filter by
            include_relationships: Whether to search for relationships between documents
            search_type: Type of search to perform (focused, detailed, or timeline)
            session_id: Optional session ID to use for this search (overrides instance session_id)
            
        Returns:
            Dict containing search results and status
        """
        # Initialize agent if not already done
        if not self.agent:
            await self.setup()
        
        # Use provided session_id or instance session_id
        effective_session_id = session_id or self.session_id
        if not effective_session_id:
            raise ValueError("Session ID is required for search operations")
        
        try:
            # Get memory for the session
            session_memory = self._session_manager.get_memory(effective_session_id)
            
            # Include chat history in the prompt if available
            chat_history = session_memory.get_formatted_history()
            history_context = f"\nPrevious conversation context:\n{chat_history}\n" if chat_history else ""
            
            # Select appropriate prompt based on search type
            if search_type == "detailed":
                prompt = self.prompts.get_detailed_search_prompt(
                    query, doc_types, include_relationships
                )
            elif search_type == "timeline":
                prompt = self.prompts.get_timeline_search_prompt(
                    query, doc_types
                )
            else:  # Default to focused search
                prompt = self.prompts.get_focused_search_prompt(
                    query, doc_types, include_relationships
                )
            
            # Add chat history to the prompt
            prompt_with_history = f"{history_context}\n{prompt}"
            
            result = await self.agent.ainvoke({
                "messages": [HumanMessage(content=prompt_with_history)]
            })
            
            # Extract the last AI message as the response
            ai_messages = [msg for msg in result["messages"] if isinstance(msg, AIMessage)]
            response = ai_messages[-1].content if ai_messages else "No results found"
            
            # Store the interaction in session memory
            session_memory.add_interaction(query, response)
            
            return {
                "status": "success",
                "summary": response,
                "query": query,
                "doc_types": doc_types,
                "search_type": search_type,
                "session_id": effective_session_id
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "query": query,
                "session_id": effective_session_id
            }
    
    def get_conversation_history(self, session_id: Optional[str] = None) -> str:
        """Get the formatted conversation history for a session.
        
        Args:
            session_id: Optional session ID (overrides instance session_id)
            
        Returns:
            Formatted string of recent conversations
        """
        effective_session_id = session_id or self.session_id
        if not effective_session_id:
            raise ValueError("Session ID is required to get conversation history")
        return self._session_manager.get_memory(effective_session_id).get_formatted_history()
    
    def clear_conversation_history(self, session_id: Optional[str] = None) -> None:
        """Clear the conversation history for a session.
        
        Args:
            session_id: Optional session ID (overrides instance session_id)
        """
        effective_session_id = session_id or self.session_id
        if not effective_session_id:
            raise ValueError("Session ID is required to clear conversation history")
        self._session_manager.clear_session(effective_session_id)
    
    async def close(self):
        """Clean up resources."""
        if self.mcp_client:
            await cleanup_mcp_client(self.mcp_client)
