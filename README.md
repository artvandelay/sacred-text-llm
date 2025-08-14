# Sacred Texts LLM Interface
> *An AI-powered gateway to 33+ million words of spiritual wisdom*

**🎯 Goal**: Query and converse with sacred texts from world religions and spiritual traditions using advanced RAG (Retrieval-Augmented Generation).

## 📊 **Complete Collection Report**

### **Scale & Coverage**
- **📚 33,298,287 words** (33.3 million) across 362 sacred texts
- **📄 2,200,367 lines** of spiritual wisdom (~73,345 pages at 30 lines/page)
- **📖 Equivalent to 295 full books** - a massive digital spiritual library
- **🌍 40+ spiritual traditions** spanning all major world religions
- **🔍 210K+ semantic chunks** optimized for AI retrieval

### **📖 Famous Texts Included**
This collection contains humanity's most treasured spiritual works:

**📿 Hindu Classics:**
- Srimad-Bhagavad-Gita (Swami Swarupananda translation)
- The Upanishads, Parts 1 & 2 (Max Muller translation)
- Complete Mahabharata texts
- Vedic literature and Puranas

**🕉️ Buddhist Wisdom:**
- The Jataka Tales (complete 6-volume set)
- Dhammapada and core Buddhist sutras
- Tibetan and Zen texts

**☪️ Islamic Heritage:**
- The Qur'an (Rodwell edition, 1876)
- Sufi poetry and mystical texts
- Classical Islamic philosophy

**✝️ Christian Tradition:**
- Church Fathers (Augustine, Aquinas)
- Mystical and contemplative texts
- Early Christian writings

**🕊️ Other Traditions:**
- Tao Te Ching and Taoist classics
- Jewish mystical texts and philosophy
- Indigenous wisdom traditions
- Hermetic and esoteric texts

## ✨ **What Makes This Special**
- **🧠 Semantic Search**: Find wisdom by meaning, not just keywords
- **🤖 Modular AI**: Switch between local models (Ollama) and cloud APIs (GPT-4, Claude)
- **🔒 Privacy-First**: Keep sacred texts local, choose your AI provider
- **📱 Multiple Interfaces**: Chat UI, command line, or integrate via API
- **⚡ Fast & Accurate**: Optimized chunking and retrieval for spiritual content

**Status**: Phase 1 complete ✅ | Phase 2 deployed ✅ | Web deployment ready ✅ | Vector store complete ✅

## Quick Start

### 1. Download Texts (if not done)
```bash
python data/download_sacred_texts.py
```

### 2. Deploy the Application

#### **🚀 Quick Deploy (Recommended)**
```bash
# Setup deployment environment
./deploy/setup.sh

# Deploy with public access
./deploy/deploy.sh
```

#### **💬 Command Line Interface**
```bash
# Simple chat interface
python chat.py

# Advanced agentic research interface  
python agent_chat.py

# Single query
python query.py "What is the meaning of compassion?"
```

### 3. Web Interface
After deployment, access your Sacred Texts LLM via:
- **Local**: http://localhost:8001
- **Public**: Your unique ngrok URL (shown during deployment)

## Hybrid Architecture

The system uses a **hybrid approach** combining the best of local and cloud:

### **Primary: OpenRouter Cloud LLMs**
```bash
# Configured in .env file
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your-key-here
OPENROUTER_CHAT_MODEL=anthropic/claude-3.5-sonnet
```

**Benefits:**
- 🚀 **Superior Quality**: GPT-4, Claude 3.5 Sonnet responses
- 💰 **Cost Effective**: ~$0.01-0.10 per question
- 🔄 **Latest Models**: Always access to newest LLMs

### **Fallback: Local Ollama**
```bash
# Automatic fallback if OpenRouter fails
OLLAMA_CHAT_MODEL=qwen3:30b-a3b
ENABLE_OLLAMA_FALLBACK=true
```

**Benefits:**
- ✅ **Reliability**: Never fails completely
- ✅ **Privacy**: Local processing when needed
- ✅ **No Dependency**: Works offline

### **Data Privacy**
- 📚 **Sacred texts**: Always stored locally (ChromaDB)
- 🔒 **Queries only**: Only your questions go to OpenRouter
- 🏠 **Full control**: Switch to local-only anytime

## 🤖 **Agentic Chat Interface**

The advanced `agent_chat.py` provides an iterative AI agent that thinks, plans, and searches multiple times before responding:

### **Agent Capabilities:**
- **🧠 Strategic Planning**: Analyzes your question and plans search strategy
- **🔍 Parallel Search**: Runs multiple refined searches simultaneously  
- **🤔 Evidence Evaluation**: Reflects on sufficiency before responding
- **⚡ Iterative Refinement**: Continues searching until confident or max iterations
- **📊 Progress Tracking**: Shows thinking process in real-time (like Cursor/Perplexity)

### **Agent Configuration:**
```bash
# Use environment variables or defaults in agent_config.py
export MAX_ITERATIONS_PER_QUERY=4        # Max search iterations
export CONFIDENCE_THRESHOLD=0.75         # Stop when this confident
export MAX_PARALLEL_QUERIES=3            # Simultaneous searches
export SHOW_AGENT_PROGRESS=true          # Show thinking process
```

### **Best For:**
- **Complex spiritual questions** requiring multiple perspectives
- **Cross-tradition comparisons** (Buddhism vs Christianity vs Islam)
- **Deep philosophical inquiries** needing comprehensive evidence
- **Research-quality responses** with multiple sources

### **Example Agent Behavior:**
```
🤖 Thinking about: "How do different traditions view suffering?"

🧠 Planning: Strategy planned → Focus: Cross-tradition perspectives on suffering
🔍 Searching: Running 3 parallel queries...
    • Buddhist teachings on suffering and dukkha
    • Christian perspectives on suffering and redemption  
    • Islamic views on suffering and divine wisdom
🤔 Reflecting: Confidence: 85% → Quality: excellent
✍️ Generating: Synthesizing final response
✅ Complete in 2 iterations
```

---

## Notes for Agent

### Project Phases
**Phase 1: Data Collection** ✅ COMPLETE
- Created downloader for sacred-texts.com archive
- 353 texts covering all major spiritual traditions
- ~4-5GB total data with organized structure
- Tested and verified download scripts

**Phase 2: RAG Implementation** 🚧 IN PROGRESS
- ✅ Text processing and chunking (adaptive semantic/verse/paragraph)
- ⚡ Embedding generation (1/705 files, ~3 hours remaining)
- ✅ Vector database setup (ChromaDB)
- ✅ Basic search interface development

**Phase 3: Chat Interface** ✅ READY
- ✅ Interactive chat interface (chat.py) 
- ✅ Command-line query tool (query.py)
- ✅ Rich formatting and source attribution
- ✅ Multi-tradition knowledge synthesis

### Data Sources
- **Primary**: [sacred-texts.com/download.htm](https://sacred-texts.com/download.htm)
- **Alternative**: [Google Drive backup](https://drive.google.com/drive/u/0/folders/1VYTr5l7jARi_Kb_aB0Jjjq2RZF9kacK7)

### Technical Details
- **Archive Size**: 249 MB total (183 MB extracted texts)
- **RAG Storage**: ~2.6 GB (with embeddings/indexes when complete)
- **File Count**: 362 texts (.txt format)
- **Download Time**: 10-15 minutes
- **Structure**: Maintains sacred-texts.com hierarchy by tradition

### Collections Included
- **Buddhism**: 22 files (Jataka, Dhammapada, etc.)
- **Hinduism**: 23 files (Upanishads, Bhagavad Gita, etc.)
- **Christianity**: 25 files (Augustine, Aquinas, mystical texts)
- **Islam**: 15 files (Quran translations, Sufi poetry)
- **Judaism**: 9 files (Talmud, Kabbalah, Maimonides)
- **Taoism**: 6 files (Tao Te Ching, Art of War)
- **Celtic/Norse**: 64 files (Mabinogion, Poetic Edda)
- **Native American**: 13 files (Creation myths, tribal wisdom)
- **Esoteric**: 16 files (Hermetic texts, Gnostic gospels)
- **Other traditions**: 35+ categories

### Download Script Features
- Progress tracking with resume capability
- User-Agent handling to avoid 403 errors
- Maintains original directory structure
- Automatic extraction option
- Detailed logging and error reporting
- Creates collection metadata

### File Organization
```
sacred_texts_archive/
├── afr/          # African traditions
├── bud/          # Buddhism  
├── chr/          # Christianity
├── hin/          # Hinduism
├── isl/          # Islam
├── jud/          # Judaism
├── tao/          # Taoism
├── neu/          # European/Norse
├── nam/          # Native American
├── eso/          # Esoteric/Occult
└── extracted/    # Uncompressed texts
```

### Testing Completed
- ✅ URL accessibility verified
- ✅ Download functionality tested
- ✅ Content verification (extracted Lao Tzu text)
- ✅ Complete catalog validation (362 files = 100% coverage)
- ✅ User-Agent fix applied for 403 errors
- ✅ Directory structure maintenance confirmed
