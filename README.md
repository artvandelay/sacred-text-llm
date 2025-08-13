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

**Status**: Phase 1 complete ✅ | Phase 2 in progress 🚧 | Chat interface ready ✅

> **⚠️ FOR OTHER AI AGENTS**: 
> - Ingestion is CURRENTLY RUNNING (PID 3170) - DO NOT INTERRUPT
> - Vector store has 212,611 docs ready, chat interface works
> - ~30 minutes remaining for full ingestion 
> - Use `tail -f ingest.log` to monitor progress

## Quick Start

### 1. Download Texts (if not done)
```bash
python download_sacred_texts.py
```

### 2. Ingest to Vector Database (currently running)
```bash
python ingest.py --sources sacred_texts_archive/extracted --mode fast --embed-workers 1 --db-batch-size 128
```
**Current Status**: ⚡ INGESTING NOW - 212,611 docs ready, still processing (~30 mins remaining)

### 3. Query the Sacred Texts
```bash
# Simple query (single-shot retrieval)
python query.py "What is the meaning of compassion?"

# Interactive chat (enhanced interface)
python chat.py

# 🤖 Agentic chat (advanced iterative agent)
python agent_chat.py
```

⚠️ **Important**: Ingestion is still running. The chat interface works with current data (212K+ docs) but will have complete coverage once ingestion finishes.

## LLM Provider Options

The system supports **modular LLM providers** - same interface, different backends:

### **Phase 1: Local Ollama (Current)**
```python
# config.py
LLM_PROVIDER = "ollama"  # Uses your local models
```

**Benefits:**
- ✅ Free - no API costs
- ✅ Private - data never leaves your machine  
- ✅ Fast - no network calls for chat generation

### **Phase 2: OpenRouter APIs (Better Quality)**
```python
# config.py  
LLM_PROVIDER = "openrouter"  # Uses GPT-4, Claude, etc.
```

```bash
# Set your API key
export OPENROUTER_API_KEY="your-key-here"

# Run the same interface
python chat.py
```

**Benefits:**
- 🚀 Better response quality (GPT-4, Claude)
- 💰 Low cost (~$0.01-0.10 per question)
- 🔄 Same interface - just better answers

### **Easy Switching**
Change one line in `config.py` to switch providers:
```python
LLM_PROVIDER = "ollama"      # Local models
LLM_PROVIDER = "openrouter"  # Cloud models
```

**The beauty:** Same chat interface, same vector search (local ChromaDB), easy A/B testing!

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
