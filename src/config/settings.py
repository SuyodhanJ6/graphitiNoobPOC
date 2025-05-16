import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Memory Configuration
CONVERSATION_MEMORY_SIZE = int(os.getenv("CONVERSATION_MEMORY_SIZE", "10"))

# Server Configuration
GRAPHITI_SERVER = {
    "url": os.getenv("GRAPHITI_SERVER_URL", "http://localhost:8000/sse"),
    "transport": "sse"
}

MARKITDOWN_SERVER = {
    "url": os.getenv("MARKITDOWN_SERVER_URL", "http://127.0.0.1:3001/sse"),
    "transport": "sse"
} 