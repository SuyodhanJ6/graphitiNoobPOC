from typing import Dict, Any
from langchain_mcp_adapters.client import MultiServerMCPClient
from src.config.settings import GRAPHITI_SERVER, MARKITDOWN_SERVER

async def setup_mcp_client() -> MultiServerMCPClient:
    """Set up and return a configured MCP client."""
    mcp_client = MultiServerMCPClient(
        {
            "graphiti": GRAPHITI_SERVER,
            "markitdown": MARKITDOWN_SERVER
        }
    )
    await mcp_client.__aenter__()
    return mcp_client

async def cleanup_mcp_client(client: MultiServerMCPClient) -> None:
    """Clean up MCP client resources."""
    if client:
        await client.__aexit__(None, None, None) 