import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.api.route import ingestion, retrieval

# Create FastAPI app
app = FastAPI(
    title="Document Processing and Knowledge Graph API",
    description="API for document ingestion and knowledge retrieval using LLMs and knowledge graphs",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins since frontend is served from same app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(ingestion.router)
app.include_router(retrieval.router)

# Mount static files for frontend
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

@app.get("/")
async def root():
    """Serve the main HTML page."""
    return FileResponse("frontend/index.html")

if __name__ == "__main__":
    print("Starting server...")
    print("Server running at http://localhost:8080")
    print("API docs available at http://localhost:8080/docs")
    print("Press Ctrl+C to stop the server")
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
