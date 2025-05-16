import asyncio
import argparse
from typing import List
from src.data_retrive.agent import DataRetrievalAgent

async def main():
    parser = argparse.ArgumentParser(description="Search information in the knowledge graph")
    parser.add_argument("--query", required=True, help="Search query")
    parser.add_argument("--doc-types", nargs="+", help="Document types to search within")
    parser.add_argument("--no-relationships", action="store_true", 
                      help="Disable relationship analysis")
    parser.add_argument("--model", default="gpt-4", help="LLM model to use")
    args = parser.parse_args()
    
    agent = DataRetrievalAgent(model_name=args.model)
    
    try:
        result = await agent.search_knowledge(
            query=args.query,
            doc_types=args.doc_types,
            include_relationships=not args.no_relationships
        )
        
        if result["status"] == "success":
            print("\n=== Search Results ===")
            print(f"Query: {result['query']}")
            if result.get("doc_types"):
                print(f"Document Types: {', '.join(result['doc_types'])}")
            print("\nSummary:")
            print(result["summary"])
        else:
            print(f"\nError performing search: {result['error']}")
    
    finally:
        await agent.close()

if __name__ == "__main__":
    asyncio.run(main()) 