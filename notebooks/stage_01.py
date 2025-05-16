import os
import asyncio
import argparse
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
import mimetypes
import pathlib

# Load environment variables
load_dotenv()

# LangChain MCP adapter imports
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

# LangChain imports
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage

class DocumentProcessor:
    """Agent for processing documents and storing knowledge using Graphiti"""
    
    def __init__(self, model_name: str = "gpt-4"):
        self.model_name = model_name
        self.llm = None
        self.agent = None
        self.mcp_client = None
        self.system_prompt = """
        You are an AI assistant with access to both document processing and knowledge graph capabilities.
        
        Available Tools:
        1. Document Processing (MarkItDown):
           - Process various document formats (PDF, PPT, Word, Excel, etc.)
           - Extract text from images using OCR
           - Transcribe audio files
           - Parse structured formats (CSV, JSON, XML)
           - Process web content and YouTube URLs
        
        2. Knowledge Graph (Graphiti):
           - add_episode: Store processed information
           - search_nodes: Find relevant information
           - search_facts: Find relationships
           - get_episodes: Retrieve conversation history
        
        Your responsibilities:
        1. Process uploaded documents effectively
        2. Extract meaningful information
        3. Store processed content in the knowledge graph
        4. Maintain relationships between documents and information
        5. Provide structured access to stored knowledge
        """
    
    async def setup(self):
        """Set up the agent with both MarkItDown and Graphiti tools."""
        self.llm = ChatOpenAI(model=self.model_name, api_key=os.getenv("OPENAI_API_KEY"))
        
        try:
            # Connect to both MCP servers
            self.mcp_client = MultiServerMCPClient(
                {
                    "graphiti": {
                        "url": "http://localhost:8000/sse",
                        "transport": "sse",
                    },
                    "markitdown": {
                        "url": "http://127.0.0.1:3001/sse",
                        "transport": "sse",
                    }
                }
            )
            
            await self.mcp_client.__aenter__()
            mcp_tools = self.mcp_client.get_tools()
            print(f"Loaded {len(mcp_tools)} tools from MCP servers")
            
            self.agent = create_react_agent(
                self.llm,
                mcp_tools,
                prompt=self.system_prompt
            )
            
        except Exception as e:
            print(f"Error connecting to MCP servers: {str(e)}")
            raise

    async def process_document(self, file_path: str) -> Dict[str, Any]:
        """Process a document and store its information.
        
        Args:
            file_path: Path to the document to process
            
        Returns:
            Processing and storage results
        """
        if not self.agent:
            await self.setup()
        
        try:
            # Get file type
            mime_type, _ = mimetypes.guess_type(file_path)
            file_ext = pathlib.Path(file_path).suffix.lower()
            
            process_prompt = f"""
            Please process this document and store its information:
            
            File: {file_path}
            Type: {mime_type or file_ext}
            
            1. Use appropriate MarkItDown tools to process the document
            2. Extract key information and insights
            3. Store the processed information in the knowledge graph using add_episode
            4. Create appropriate relationships using search_facts if relevant
            
            Please provide a summary of what was processed and stored.
            """
            
            result = await self.agent.ainvoke({
                "messages": [
                    HumanMessage(content=process_prompt)
                ]
            })
            
            return result
            
        except Exception as e:
            return {
                "error": f"Error processing document: {str(e)}"
            }

    async def search_documents(self, query: str, doc_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """Search for information across processed documents.
        
        Args:
            query: Search query
            doc_types: Optional list of document types to search within
            
        Returns:
            Search results
        """
        if not self.agent:
            await self.setup()
        
        try:
            type_filter = f" within {', '.join(doc_types)}" if doc_types else ""
            search_prompt = f"""
            Please search for information{type_filter} about:
            
            {query}
            
            1. Use search_nodes to find relevant documents and information
            2. Use search_facts to find relationships between documents
            3. Compile the results in a clear, structured format
            """
            
            result = await self.agent.ainvoke({
                "messages": [
                    HumanMessage(content=search_prompt)
                ]
            })
            
            return result
            
        except Exception as e:
            return {
                "error": f"Error searching documents: {str(e)}"
            }

    async def close(self):
        """Clean up resources."""
        if self.mcp_client:
            await self.mcp_client.__aexit__(None, None, None)


async def main():
    """Run the document processor."""
    parser = argparse.ArgumentParser(description="Document Processor with Knowledge Graph")
    parser.add_argument("--action", choices=["process", "search"], required=True,
                      help="Action to perform (process or search)")
    parser.add_argument("--file", help="Path to file to process")
    parser.add_argument("--query", help="Search query")
    parser.add_argument("--doc-types", nargs="+", help="Document types to search within")
    parser.add_argument("--model", default="gpt-4", help="LLM model to use")
    args = parser.parse_args()
    
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not found in environment variables")
        print("Please set it in your .env file")
        return
    
    processor = DocumentProcessor(model_name=args.model)
    
    try:
        if args.action == "process":
            if not args.file:
                print("ERROR: --file is required for process action")
                return
            result = await processor.process_document(args.file)
        else:  # search
            if not args.query:
                print("ERROR: --query is required for search action")
                return
            result = await processor.search_documents(args.query, args.doc_types)
        
        if "error" in result:
            print(f"Error: {result['error']}")
            return
        
        # Display the result
        ai_messages = [msg for msg in result["messages"] if isinstance(msg, AIMessage)]
        if ai_messages:
            print("\n===== PROCESSING RESULT =====")
            print(ai_messages[-1].content)
        else:
            print("No result was generated")
    
    finally:
        await processor.close()


if __name__ == "__main__":
    asyncio.run(main())