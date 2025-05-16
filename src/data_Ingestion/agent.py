import mimetypes
import pathlib
from typing import Dict, Any, Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent

from src.config.settings import OPENAI_API_KEY, DEFAULT_MODEL
from src.utils.mcp_client import setup_mcp_client, cleanup_mcp_client
from src.prompts.ingestion_prompts import IngestionPrompts

class DataIngestionAgent:
    """Agent responsible for processing and ingesting documents into the knowledge graph."""
    
    def __init__(self, model_name: str = DEFAULT_MODEL):
        self.model_name = model_name
        self.llm = None
        self.agent = None
        self.mcp_client = None
        self.prompts = IngestionPrompts()
    
    async def setup(self):
        """Initialize the agent with required tools and configurations."""
        self.llm = ChatOpenAI(model=self.model_name, api_key=OPENAI_API_KEY)
        
        try:
            self.mcp_client = await setup_mcp_client()
            mcp_tools = self.mcp_client.get_tools()
            
            # Use base document processing prompt by default
            self.agent = create_react_agent(
                self.llm,
                mcp_tools,
                prompt=self.prompts.get_document_processing_prompt("")  # Empty path, will be set per request
            )
            
        except Exception as e:
            if self.mcp_client:
                await cleanup_mcp_client(self.mcp_client)
            raise RuntimeError(f"Failed to setup ingestion agent: {str(e)}")

    async def process_document(self, file_path: str) -> Dict[str, Any]:
        """Process a document and store its information in the knowledge graph.
        
        Args:
            file_path: Path to the document to process
            
        Returns:
            Dict containing processing results and status
        """
        if not self.agent:
            await self.setup()
        
        try:
            mime_type, _ = mimetypes.guess_type(file_path)
            file_ext = pathlib.Path(file_path).suffix.lower()
            
            # Get appropriate processing prompt based on file type
            process_prompt = self.prompts.get_document_processing_prompt(
                file_path=file_path,
                mime_type=mime_type
            )
            
            result = await self.agent.ainvoke({
                "messages": [HumanMessage(content=process_prompt)]
            })
            
            # Extract the last AI message as the summary
            ai_messages = [msg for msg in result["messages"] if isinstance(msg, AIMessage)]
            summary = ai_messages[-1].content if ai_messages else "No summary available"
            
            # If document was processed successfully, extract metadata and establish relationships
            if "error" not in result:
                # Extract metadata
                metadata_prompt = self.prompts.get_metadata_extraction_prompt()
                metadata_result = await self.agent.ainvoke({
                    "messages": [HumanMessage(content=metadata_prompt)]
                })
                
                # Establish relationships with other documents
                relationship_prompt = self.prompts.get_relationship_prompt(file_path)
                await self.agent.ainvoke({
                    "messages": [HumanMessage(content=relationship_prompt)]
                })
            
            return {
                "status": "success",
                "summary": summary,
                "file_processed": file_path
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "file_processed": file_path
            }
    
    async def close(self):
        """Clean up resources."""
        if self.mcp_client:
            await cleanup_mcp_client(self.mcp_client)
