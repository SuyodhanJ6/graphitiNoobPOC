import asyncio
import argparse
from src.data_Ingestion.agent import DataIngestionAgent

async def main():
    parser = argparse.ArgumentParser(description="Ingest documents into the knowledge graph")
    parser.add_argument("--file", required=True, help="Path to file to process")
    parser.add_argument("--model", default="gpt-4", help="LLM model to use")
    args = parser.parse_args()
    
    agent = DataIngestionAgent(model_name=args.model)
    
    try:
        result = await agent.process_document(args.file)
        
        if result["status"] == "success":
            print("\n=== Document Processing Summary ===")
            print(f"File: {result['file_processed']}")
            print("\nSummary:")
            print(result["summary"])
        else:
            print(f"\nError processing document: {result['error']}")
    
    finally:
        await agent.close()

if __name__ == "__main__":
    asyncio.run(main()) 