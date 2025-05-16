from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List, Optional
import tempfile
import os
import shutil
from pydantic import BaseModel

from src.data_Ingestion.agent import DataIngestionAgent

router = APIRouter(prefix="/ingest", tags=["ingestion"])

class ProcessResponse(BaseModel):
    status: str
    summary: str
    file_processed: str

@router.post("/document", response_model=ProcessResponse)
async def ingest_document(
    file: UploadFile = File(...),
    model: Optional[str] = None
) -> ProcessResponse:
    """
    Ingest a single document into the knowledge graph.
    
    Args:
        file: The document file to process
        model: Optional LLM model to use
    """
    # Create temporary file to store upload
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        try:
            # Save uploaded file
            shutil.copyfileobj(file.file, temp_file)
            temp_path = temp_file.name
            
            # Process document
            agent = DataIngestionAgent(model_name=model) if model else DataIngestionAgent()
            result = await agent.process_document(temp_path)
            
            if result["status"] == "error":
                raise HTTPException(status_code=500, detail=result["error"])
                
            return ProcessResponse(
                status=result["status"],
                summary=result["summary"],
                file_processed=file.filename
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
            
        finally:
            await file.close()
            # Cleanup temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            await agent.close()

@router.post("/batch", response_model=List[ProcessResponse])
async def ingest_batch(
    files: List[UploadFile] = File(...),
    model: Optional[str] = None
) -> List[ProcessResponse]:
    """
    Batch ingest multiple documents into the knowledge graph.
    
    Args:
        files: List of document files to process
        model: Optional LLM model to use
    """
    agent = DataIngestionAgent(model_name=model) if model else DataIngestionAgent()
    responses = []
    
    try:
        for file in files:
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                try:
                    # Save uploaded file
                    shutil.copyfileobj(file.file, temp_file)
                    temp_path = temp_file.name
                    
                    # Process document
                    result = await agent.process_document(temp_path)
                    
                    responses.append(
                        ProcessResponse(
                            status=result["status"],
                            summary=result["summary"],
                            file_processed=file.filename
                        )
                    )
                    
                finally:
                    await file.close()
                    # Cleanup temp file
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                        
    finally:
        await agent.close()
        
    return responses 