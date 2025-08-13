# Sacred Texts LLM Configuration
# Simple, human-readable settings

# Vector Database (Local ChromaDB)
EMBEDDING_MODEL = "nomic-embed-text"
VECTOR_STORE_DIR = "vector_store/chroma"
COLLECTION_NAME = "sacred_texts"

# LLM Provider Choice - Change this to switch providers!
LLM_PROVIDER = "openrouter"  # Options: "ollama" or "openrouter"

# Local Ollama Settings (Phase 1)
OLLAMA_CHAT_MODEL = "qwen3:30b-a3b"

# OpenRouter Settings (Phase 2) 
OPENROUTER_CHAT_MODEL = "anthropic/claude-sonnet-4" 
# Set your API key: export OPENROUTER_API_KEY="your-key-here"

