# Sacred Texts LLM
> *AI-powered gateway to 33+ million words of spiritual wisdom from 40+ traditions*

Chat with sacred texts using advanced AI - query the Bhagavad Gita, Bible, Quran, Buddhist sutras, Tao Te Ching, and hundreds more spiritual texts with semantic search and intelligent responses.

*Texts courtesy of [sacred-texts.com](https://sacred-texts.com/) - "the largest freely available archive of online books about religion, mythology, folklore and the esoteric on the Internet"*

## 🚀 Quick Start

### Get Running in 15 Minutes

```bash
# 1. Clone and install
git clone https://github.com/artvandelay/sacred-text-llm
cd sacred-text-LLM
pip install -r requirements.txt

# 2. Get the data (choose one):
python data/download_sacred_texts.py    # Download from sacred-texts.com (4GB, 15min)
# OR contact authors for pre-built vector database

# 3. Set up environment (IMPORTANT!)
cp .env.example .env                     # Copy environment template
# Edit .env file with your settings:
# - OPENROUTER_API_KEY=your-key-here (for better AI models)
# - LLM_PROVIDER=openrouter (or ollama for local-only)

# 4. Install AI models
brew install ollama                      # macOS
ollama serve &
ollama pull nomic-embed-text
ollama pull qwen3:30b-a3b               # or your preferred model

# 5. Create vector database (if downloaded texts)
# This processes 33M+ words into ChromaDB with semantic embeddings
# Converts texts into 210K+ searchable chunks for AI retrieval
# Takes 1-2 hours but enables intelligent semantic search
python data/ingest.py --sources sacred_texts_archive/extracted

# 6. Start chatting!
python agent_chat.py                    # Multi-mode interface
```

### Deploy Web Interface
```bash
./deploy/deploy.sh
# Visit http://localhost:8001 or your ngrok URL
```

**⏱️ Setup time**: 15 minutes download + 1-2 hours processing | **💾 Space needed**: ~10GB

### Common Configuration Options

After setup, you can tune the AI behavior by editing your `.env` file:

```bash
# AI Provider & Models
LLM_PROVIDER=openrouter                    # ollama (local) or openrouter (cloud)
OLLAMA_CHAT_MODEL=qwen3:30b-a3b           # Local model choice
OPENROUTER_CHAT_MODEL=anthropic/claude-3.5-sonnet  # Cloud model choice

# Deep Research Behavior  
MAX_ITERATIONS_PER_QUERY=4                # How many research cycles (1-8)
CONFIDENCE_THRESHOLD=0.75                 # When to stop researching (0.1-1.0)
MAX_PARALLEL_QUERIES=10                   # Search breadth per iteration (1-20)

# Search Settings
DEFAULT_SEARCH_K=5                        # Results per search (1-20)
MAX_TOTAL_EVIDENCE_CHUNKS=15              # Total passages to analyze (5-50)

# UI Options
SHOW_AGENT_PROGRESS=true                  # Show thinking process
SHOW_DETAILED_PROGRESS=true               # Verbose progress updates
SHOW_CONFIDENCE_SCORES=true               # Display confidence levels
```

**Quick tweaks:**
- **Faster responses**: Lower `MAX_ITERATIONS_PER_QUERY` to 2
- **Deeper research**: Increase `MAX_PARALLEL_QUERIES` to 15-20  
- **Better quality**: Switch to `LLM_PROVIDER=openrouter` with API key
- **Local only**: Keep `LLM_PROVIDER=ollama` (no API key needed)

## 🎛️ Modes & Usage

The v3.0 architecture introduces **modes** - isolated experimental features you can switch between or extend with your own ideas.

### Current Modes

**🔍 Deep Research Mode** (`deep_research`)
- Iterative AI agent that plans, searches, and synthesizes comprehensive responses
- Performs 1-4 research cycles with parallel queries for thorough investigation
- Best for: Complex questions, cross-tradition comparisons, scholarly research

```bash
python agent_chat.py --mode deep_research --query "How do different traditions view suffering?"
```

**🧘 Contemplative Mode** (`contemplative`) 
- Returns a single relevant passage with a thoughtful reflection question
- Focused on personal spiritual practice and meditation
- Best for: Daily reflection, spiritual guidance, mindfulness practice

```bash
python agent_chat.py --mode contemplative --query "What is inner peace?"
```

### Other Interface Options

```bash
python scripts/chat.py                  # Simple chat interface
python scripts/query.py "What is compassion?"  # Single questions
```

### Create Your Own Mode

Want to experiment with a new approach? The architecture makes it easy:

```bash
# 1. Generate a new mode template
python scripts/new_mode.py your_mode_name

# 2. Edit the generated file with your logic
# app/modes/your_mode.py is created with the basic structure

# 3. Register it in the system
# Add to app/modes/registry.py

# 4. Test your mode
python agent_chat.py --mode your_mode --query "test question"

# 5. Deploy instantly
./deploy/deploy.sh restart
```

**Mode Ideas:** Koan generator, verse finder, tradition comparison, debate facilitator, meditation guide, ritual explanation, historical context, or anything you can imagine!

## 📚 What's Included

### **Scale & Coverage**
- **📚 33,298,287 words** (33.3 million) across 362 sacred texts
- **📄 2,200,367 lines** of spiritual wisdom (~73,345 pages at 30 lines/page)
- **🌍 40+ spiritual traditions** spanning all major world religions
- **🔍 210K+ semantic chunks** optimized for AI retrieval

### **📖 Famous Texts**

**📿 Hindu Classics:** Bhagavad Gita, Upanishads, Mahabharata, Vedic literature  
**🕉️ Buddhist Wisdom:** Jataka Tales, Dhammapada, Tibetan and Zen texts  
**☪️ Islamic Heritage:** Quran, Sufi poetry, classical Islamic philosophy  
**✝️ Christian Tradition:** Church Fathers (Augustine, Aquinas), mystical texts  
**🕊️ Other Traditions:** Tao Te Ching, Jewish mystical texts, Indigenous wisdom, Hermetic texts

## ✨ Features

- **🧠 Semantic Search**: Find wisdom by meaning, not just keywords
- **🎛️ Experimental Modes**: Deep research agent + contemplative reflection modes
- **🤖 Modular AI**: Switch between local models (Ollama) and cloud APIs (GPT-4, Claude)
- **🔒 Privacy-First**: Keep sacred texts local, choose your AI provider, zero telemetry
- **📱 Multiple Interfaces**: Chat UI, command line, or integrate via API
- **⚡ Fast & Accurate**: Optimized chunking and retrieval for spiritual content
- **🏗️ Clean Architecture**: Easy to add new experimental modes and features

**🆕 v3.0.0**: Clean modes architecture, unified configuration, privacy-first design, experimental modes system

## 📖 Advanced Setup

### Prerequisites
- **Python 3.10+** with pip
- **~10GB free space** (texts + vector database)
- **2-3 hours** for initial setup (mostly processing time)

### Detailed Installation

#### Step 1: Environment Setup
```bash
git clone <your-repo-url>
cd sacred-text-LLM
pip install -r requirements.txt
```

#### Step 2: Install Ollama (Local AI)
```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve &

# Install embedding model
ollama pull nomic-embed-text

# Install chat model
ollama pull qwen3:30b-a3b
```

#### Step 3: Data Collection & Processing
```bash
# Option A: Download sacred texts (~4GB, 15 minutes)
python data/download_sacred_texts.py

# Option B: Contact authors for pre-built vector database

# If using Option A, create vector database (~2GB, 1-2 hours)  
python data/ingest.py --sources sacred_texts_archive/extracted --mode fast

# Verify completion
python data/check_progress.py
```

#### Step 4: Optional - Cloud AI Setup
For better chat quality, set up OpenRouter API:

```bash
export OPENROUTER_API_KEY="your-key-here"
export LLM_PROVIDER="openrouter"  # Switches from local to cloud
```

#### Step 5: Deploy & Test
```bash
# Deploy web interface
./deploy/deploy.sh

# Test CLI interfaces
python agent_chat.py --list-modes
python agent_chat.py --mode contemplative --query "What is wisdom?"
```

### Configuration Options

Edit environment variables or `.env` file:

```bash
# AI Provider Settings
LLM_PROVIDER=ollama                    # or "openrouter"
OLLAMA_CHAT_MODEL=qwen3:30b-a3b       # Local model
OPENROUTER_CHAT_MODEL=anthropic/claude-3.5-sonnet  # Cloud model

# Database Settings
VECTOR_STORE_DIR=vector_store/chroma   # Database location
COLLECTION_NAME=sacred_texts           # Collection name

# Agent Behavior
MAX_ITERATIONS_PER_QUERY=4            # Research depth
CONFIDENCE_THRESHOLD=0.75              # Quality threshold
MAX_PARALLEL_QUERIES=10                # Search breadth
```

### Troubleshooting

**Vector store empty?**
```bash
python data/check_progress.py
# Should show ~200K documents. If 0, re-run ingestion.
```

**Ollama connection issues?**
```bash
ollama list                           # Check installed models
ollama serve &                        # Restart service
curl http://localhost:11434/api/tags  # Test API
```

**Deployment issues?**
```bash
./deploy/setup.sh check              # Validate environment
python deploy/test_web.py            # Test web interface
```

## 📋 Project Info

### Technical Details
- **Archive Size**: 249 MB total (183 MB extracted texts)
- **RAG Storage**: ~2.6 GB (with embeddings/indexes when complete)
- **File Count**: 362 texts (.txt format)
- **Download Time**: 10-15 minutes
- **Structure**: Maintains sacred-texts.com hierarchy by tradition

### Data Sources
- **Primary**: [sacred-texts.com/download.htm](https://sacred-texts.com/download.htm)
- **Alternative**: Contact authors for pre-built vector database

### Development Phases
**Phase 1: Data Collection** ✅ COMPLETE
- ✅ Text processing and chunking (adaptive semantic/verse/paragraph)
- ✅ Embedding generation and vector database setup
- ✅ Basic search interface development

**Phase 2: AI Interface** ✅ COMPLETE
- ✅ Multi-mode interface (agent_chat.py) with deep research and contemplative modes
- ✅ Simple chat interface (scripts/chat.py) 
- ✅ Command-line query tool (scripts/query.py)
- ✅ Rich formatting and source attribution
- ✅ Multi-tradition knowledge synthesis

**Phase 3: Architecture** ✅ COMPLETE (v3.0.0)
- ✅ Clean modes system for experimental features
- ✅ Unified configuration and privacy-first design
- ✅ Streamlined codebase and deployment system

### Contributing

The v3.0 architecture makes it easy to contribute new modes or features:

1. **Create a mode**: Use `python scripts/new_mode.py your_idea`
2. **Test locally**: `python agent_chat.py --mode your_idea`
3. **Deploy instantly**: `./deploy/deploy.sh restart`

See `docs/creating-new-modes.md` for detailed guidance.

---

*Sacred Texts LLM v3.0.0 - Built for spiritual wisdom seekers, researchers, and AI experimenters*