# Sacred Texts LLM Agent Configuration
# Environment-based configuration with sensible defaults

import os
from typing import Optional
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

def get_env_bool(key: str, default: bool = False) -> bool:
    """Get boolean from environment variable"""
    value = os.getenv(key, str(default)).lower()
    return value in ('true', '1', 'yes', 'on')

def get_env_int(key: str, default: int) -> int:
    """Get integer from environment variable"""
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default

def get_env_float(key: str, default: float) -> float:
    """Get float from environment variable"""
    try:
        return float(os.getenv(key, str(default)))
    except ValueError:
        return default

# =============================================================================
# LLM PROVIDERS
# =============================================================================

# Provider choice: "ollama" or "openrouter"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")

# Ollama Settings (Local)
OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "qwen3:30b-a3b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# OpenRouter Settings (Cloud)
# Get API key from: https://openrouter.ai/keys
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_CHAT_MODEL = os.getenv("OPENROUTER_CHAT_MODEL", "anthropic/claude-3.5-sonnet")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

# =============================================================================
# VECTOR DATABASE
# =============================================================================

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
VECTOR_STORE_DIR = os.getenv("VECTOR_STORE_DIR", "vector_store/chroma")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "sacred_texts")

# =============================================================================
# AGENT BEHAVIOR
# =============================================================================

# Core agent loop settings
MAX_ITERATIONS_PER_QUERY = get_env_int("MAX_ITERATIONS_PER_QUERY", 4)
CONFIDENCE_THRESHOLD = get_env_float("CONFIDENCE_THRESHOLD", 0.75)
MIN_EVIDENCE_CHUNKS = get_env_int("MIN_EVIDENCE_CHUNKS", 3)

# Research expansion settings (new)
MAX_RESEARCH_ITERATIONS = get_env_int("MAX_RESEARCH_ITERATIONS", 8)
MAX_QUERIES_PER_ITERATION = get_env_int("MAX_QUERIES_PER_ITERATION", 5)
RESEARCH_DEPTH_MODE = os.getenv("RESEARCH_DEPTH_MODE", "deep")  # "quick", "standard", "deep", "exhaustive"

# Parallel query settings
MAX_PARALLEL_QUERIES = get_env_int("MAX_PARALLEL_QUERIES", 3)
ENABLE_QUERY_REFORMULATION = get_env_bool("ENABLE_QUERY_REFORMULATION", True)

# Search settings
DEFAULT_SEARCH_K = get_env_int("DEFAULT_SEARCH_K", 5)
MAX_TOTAL_EVIDENCE_CHUNKS = get_env_int("MAX_TOTAL_EVIDENCE_CHUNKS", 15)

# =============================================================================
# UI & PROGRESS
# =============================================================================

# Show agent thinking process while working
SHOW_AGENT_PROGRESS = get_env_bool("SHOW_AGENT_PROGRESS", True)
SHOW_SEARCH_QUERIES = get_env_bool("SHOW_SEARCH_QUERIES", True)
SHOW_CONFIDENCE_SCORES = get_env_bool("SHOW_CONFIDENCE_SCORES", True)

# Progress display settings
PROGRESS_UPDATE_INTERVAL = get_env_float("PROGRESS_UPDATE_INTERVAL", 0.5)
COLLAPSE_COMPLETED_STEPS = get_env_bool("COLLAPSE_COMPLETED_STEPS", True)

# =============================================================================
# OPENROUTER USAGE INSTRUCTIONS
# =============================================================================

if LLM_PROVIDER == "openrouter" and not OPENROUTER_API_KEY:
    print("""
    🔑 OpenRouter API Key Required!
    
    1. Visit: https://openrouter.ai/keys
    2. Sign up/login to get your API key
    3. Set environment variable: export OPENROUTER_API_KEY="your-key-here"
    
    Or create a .env file with:
    OPENROUTER_API_KEY=your-key-here
    """)
