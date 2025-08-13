# Sacred Texts LLM Configuration
# Simple, human-readable settings

import os
from pathlib import Path

# Load .env file from root directory
try:
    from dotenv import load_dotenv
    # Get the root directory (2 levels up from this file)
    root_dir = Path(__file__).parent.parent.parent
    env_path = root_dir / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✓ Loaded environment variables from {env_path}")
    else:
        print(f"ℹ️  No .env file found at {env_path}")
except ImportError:
    print("ℹ️  python-dotenv not installed. Install with: pip install python-dotenv")
except Exception as e:
    print(f"⚠️  Error loading .env file: {e}")

# Vector Database (Local ChromaDB)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
VECTOR_STORE_DIR = os.getenv("VECTOR_STORE_DIR", "vector_store/chroma")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "sacred_texts")

# LLM Provider Choice - Change this to switch providers!
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openrouter")  # Options: "ollama" or "openrouter"

# Local Ollama Settings (Phase 1)
OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "qwen3:30b-a3b")

# OpenRouter Settings (Phase 2) 
OPENROUTER_CHAT_MODEL = os.getenv("OPENROUTER_CHAT_MODEL", "anthropic/claude-sonnet-4") 
# Set your API key: export OPENROUTER_API_KEY="your-key-here"

