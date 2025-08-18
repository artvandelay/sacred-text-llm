"""
Deprecated: use app.config instead.
Retained temporarily to avoid breaking imports during transition.
"""

import os
from pathlib import Path

# Load .env file from root directory
try:
    from dotenv import load_dotenv
    root_dir = Path(__file__).parent.parent.parent
    env_path = root_dir / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except Exception:
    pass

# Vector Database (Local ChromaDB)
from app.config import EMBEDDING_MODEL, VECTOR_STORE_DIR, COLLECTION_NAME

# LLM Provider Choice - Change this to switch providers!
from app.config import LLM_PROVIDER

# Local Ollama Settings (Phase 1)
from app.config import OLLAMA_CHAT_MODEL

# OpenRouter Settings (Phase 2) 
from app.config import OPENROUTER_CHAT_MODEL 
# Set your API key: export OPENROUTER_API_KEY="your-key-here"

