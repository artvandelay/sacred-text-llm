# Sacred Texts LLM v3.0 Architecture

This document describes the clean, modern architecture implemented in v3.0.

## 🎯 Design Principles

1. **Modes as Experiments**: Isolated experimental features that don't touch core
2. **Single Source of Truth**: One config file, one entry point, one registry
3. **Generator Pattern**: Streaming updates + final response for all modes
4. **Environment-Driven**: All behavior configurable via `.env` variables
5. **Zero Dependencies**: Modes are completely self-contained

## 🏗️ Current Architecture

```
sacred-text-LLM/
├── agent_chat.py              # Main entry point (Universal CLI)
├── app/
│   ├── config.py              # Single config source (environment-driven)
│   ├── core/                  # Shared infrastructure
│   │   ├── providers.py       # LLM abstraction (Ollama/OpenRouter)
│   │   ├── vector_store.py    # Database abstraction (ChromaDB)
│   │   └── state.py           # Shared data structures
│   └── modes/                 # Experimental features
│       ├── base.py            # Abstract base class
│       ├── registry.py        # Single source of truth for modes
│       ├── deep_research.py   # Research agent mode
│       └── contemplative.py   # Reflection mode
├── scripts/                   # Utilities
│   ├── chat.py               # Simple chat interface
│   ├── query.py              # One-shot queries
│   └── new_mode.py           # Mode generator template
└── deploy/
    ├── web_app.py            # Web interface
    └── deploy.sh             # Deployment automation
```

## 🎛️ Modes System

### Current Modes

**Deep Research Mode** (`deep_research`)
- Iterative AI agent with planning, parallel search, and synthesis
- Configurable depth (1-8 iterations) and breadth (1-20 queries)
- Confidence-based early stopping

**Contemplative Mode** (`contemplative`)
- Single passage + thoughtful reflection question
- Focused on personal spiritual practice
- Minimal, fast responses

### Mode Contract

Every mode follows this simple pattern:

```python
from app.modes.base import BaseMode
from app import config as agent_config

class YourMode(BaseMode):
    def __init__(self, llm_provider, vector_store):
        super().__init__(llm_provider, vector_store)
        # Access settings via agent_config.SETTING_NAME
        
    def run(self, query: str, chat_history=None) -> Generator[Dict[str, Any], None, str]:
        # Yield progress updates
        yield {"type": "planning", "content": "Thinking..."}
        yield {"type": "searching", "content": "Finding passages..."}
        
        # Your mode logic here
        response = self.process_query(query)
        
        # Return final response
        return response
```

### Adding New Modes

1. **Generate template**: `python scripts/new_mode.py your_mode`
2. **Implement logic**: Edit `app/modes/your_mode.py`
3. **Register mode**: Add to `app/modes/registry.py`
4. **Test**: `python agent_chat.py --mode your_mode --query "test"`
5. **Deploy**: `./deploy/deploy.sh restart`

## ⚙️ Configuration System

### Single Source: `app/config.py`

All settings are environment-driven:

```python
# AI Provider Settings
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "qwen3:30b-a3b")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# Research Behavior
MAX_ITERATIONS_PER_QUERY = get_env_int("MAX_ITERATIONS_PER_QUERY", 4)
CONFIDENCE_THRESHOLD = get_env_float("CONFIDENCE_THRESHOLD", 0.75)
MAX_PARALLEL_QUERIES = get_env_int("MAX_PARALLEL_QUERIES", 10)

# Database Settings
VECTOR_STORE_DIR = os.getenv("VECTOR_STORE_DIR", "vector_store/chroma")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")

# Privacy
os.environ["ANONYMIZED_TELEMETRY"] = "False"  # Disable ChromaDB telemetry
```

### User Configuration

Users configure via `.env` file:

```bash
# Quick tweaks
LLM_PROVIDER=openrouter                    # Switch to cloud AI
MAX_ITERATIONS_PER_QUERY=2                # Faster responses
MAX_PARALLEL_QUERIES=15                   # Deeper research
SHOW_DETAILED_PROGRESS=false              # Less verbose
```

## 🏃‍♂️ Usage Patterns

### Command Line Interface

```bash
# Main interface (multi-mode)
python agent_chat.py                      # Interactive with mode switching
python agent_chat.py --list-modes         # See available modes
python agent_chat.py --mode contemplative --query "What is wisdom?"

# Utility interfaces
python scripts/chat.py                    # Simple Q&A
python scripts/query.py "What is peace?"  # Single query
```

### Web Interface

```bash
./deploy/deploy.sh                        # Deploy with ngrok
# Visit http://localhost:8001 or ngrok URL
```

### Programmatic Usage

```python
from app.core.providers import create_provider
from app.core.vector_store import get_vector_store
from app.modes.registry import get_mode
from app import config

# Initialize
llm = create_provider(config.LLM_PROVIDER)
store = get_vector_store()
mode = get_mode("deep_research", llm, store)

# Run with streaming
for update in mode.run("What is enlightenment?"):
    print(f"Update: {update}")
# Generator returns final response via StopIteration.value
```

## 🧩 Core Components

### LLM Providers (`app/core/providers.py`)

Unified interface for AI models:
- **Local**: Ollama (free, private)
- **Cloud**: OpenRouter API (better quality)
- **Switching**: Change `LLM_PROVIDER` environment variable

### Vector Store (`app/core/vector_store.py`)

Database abstraction:
- **Current**: ChromaDB with local persistence
- **Abstract**: Protocol allows future database switching
- **Features**: Semantic search, 210K+ text chunks

### State Management (`app/core/state.py`)

Minimal shared data structures:
- `SearchResult`: Container for vector search results
- `parse_json_response`: LLM response parsing utility

## 🔄 Generator Pattern

All modes use Python generators for streaming:

```python
def run(self, query: str) -> Generator[Dict[str, Any], None, str]:
    yield {"type": "planning", "content": "Analyzing query..."}
    yield {"type": "searching", "content": "Finding passages..."}
    yield {"type": "synthesizing", "content": "Generating response..."}
    return "Final response"
```

**Benefits:**
- Real-time progress updates
- Cancellable operations
- Memory efficient
- Uniform interface across CLI and web

## 🚀 Deployment

### Local Development
```bash
python agent_chat.py              # Test CLI
python deploy/web_app.py          # Test web (localhost:8001)
```

### Production Deployment
```bash
./deploy/deploy.sh                # Full deployment with ngrok
./deploy/deploy.sh restart        # Update with code changes
./deploy/deploy.sh status         # Check service status
```

## 🧪 Testing

```bash
# Run test suite
pytest                           # All tests

# Test specific modes
python agent_chat.py --mode deep_research --query "test"
python agent_chat.py --mode contemplative --query "test"

# Test new mode template
python scripts/new_mode.py test_mode
python agent_chat.py --mode test_mode --query "test"
```

## 🎯 Key Improvements in v3.0

### From v2.x → v3.0

1. **Configuration Unification**
   - Before: 3 config files with duplication
   - After: Single `app/config.py` with environment variables

2. **Architecture Cleanup**
   - Before: Complex `app/agent/` and `app/chat/` directories
   - After: Clean `app/core/` infrastructure + `app/modes/` features

3. **Entry Points**
   - Before: Multiple scattered entry points
   - After: `agent_chat.py` as main, utilities in `scripts/`

4. **Privacy**
   - Before: ChromaDB sending telemetry
   - After: Complete local operation, zero external calls

5. **Extensibility**
   - Before: Hard to add new features
   - After: Create new mode in minutes

## 💡 Design Philosophy

### Why This Architecture?

1. **Experimentation**: Easy to try new AI approaches without breaking core
2. **Maintenance**: Clear separation of concerns, minimal dependencies
3. **Privacy**: Local data, configurable AI providers
4. **Performance**: Efficient streaming, parallel processing
5. **User Experience**: Consistent interface across CLI and web

### Future Expansion

The v3.0 architecture supports:
- **New modes**: Koan generator, debate facilitator, ritual guide
- **New databases**: Supabase, Pinecone, local alternatives
- **New AI providers**: Anthropic direct, local LLMs, custom APIs
- **New interfaces**: Discord bot, API server, mobile app

---

*This architecture provides a solid foundation for spiritual AI experimentation while maintaining simplicity and performance.*
