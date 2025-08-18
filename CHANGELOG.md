# Changelog

## [v3.0.0] - Clean Architecture & Modes System - 2025-01-XX

### 🏗️ Major Architecture Overhaul

#### **Modes System**
- **Experimental Modes**: Isolated experimental features (deep_research, contemplative)
- **Easy Extensibility**: Simple template for creating new modes
- **Mode Registry**: Single source of truth for all available modes
- **Generator Pattern**: Streaming updates and final responses

#### **Configuration Unification**
- **Single Config**: Consolidated all settings into `app/config.py`
- **Environment-Driven**: All behavior configurable via environment variables
- **Privacy-First**: Disabled ChromaDB telemetry for fully local operation
- **No Config Duplication**: Eliminated redundant config files

#### **Codebase Cleanup**
- **Legacy Removal**: Deleted `app/agent/`, `app/chat/`, redundant files
- **Clean Structure**: `app/core/` for infrastructure, `app/modes/` for features
- **Entry Point Clarity**: `agent_chat.py` as main, scripts moved to `scripts/`
- **Testing Improvements**: Parallel pytest execution with progress bars

### 📁 Breaking Changes
- Moved `chat.py` → `scripts/chat.py`
- Moved `query.py` → `scripts/query.py`
- Removed `app/agent/config.py` and `app/chat/config.py`
- Unified all configuration in `app/config.py`

### ✨ Features
- Multi-mode interface with deep research and contemplative modes
- Configuration tuning options for AI behavior
- Clean architecture for rapid experimentation
- Zero telemetry for complete privacy

## [v2.2.0] - Complete Deployment System - 2024-12-28

### 🚀 Major Deployment Features

#### **Hybrid Architecture**
- **Cloud LLM Integration**: OpenRouter support for Claude 3.5 Sonnet, GPT-4, and other premium models
- **Local Data Privacy**: ChromaDB vector database keeps sacred texts data completely local
- **Intelligent Fallback**: Automatic fallback to local Ollama if OpenRouter fails
- **Cost Monitoring**: Built-in OpenRouter usage tracking and cost management

#### **Web Deployment System**
- **Public Web Access**: ngrok integration for instant HTTPS public URLs
- **Real-time Streaming**: WebSocket streaming of agent progress and console output
- **Dual Mode Interface**: Complete web interface for both Chat and Deep Research Agent
- **API Endpoints**: RESTful API (`/query`, `/health`, `/info`) for integration

#### **Comprehensive Setup Automation**
- **One-Command Setup**: `./deploy/setup.sh` handles all configuration
- **Environment Management**: Smart `.env` file creation and validation
- **Dependency Checking**: Automatic verification of Python, Ollama, ngrok, and API keys  
- **Database Validation**: Vector store verification with document counting

#### **Production-Ready Deployment**
- **Service Management**: Start, stop, restart, status, logs commands
- **Error Handling**: Graceful failure recovery and detailed error reporting
- **Cross-Platform Support**: macOS, Linux compatibility with proper dependency detection
- **Documentation**: Complete setup guides for new users from scratch

### 📁 New File Structure
```
deploy/
├── setup.sh              # Complete environment setup
├── deploy.sh             # Service management
├── web_app.py            # FastAPI web wrapper
├── test_web.py           # Automated testing suite
├── env.example           # Configuration template
└── README.md             # Deployment documentation
```

### 🔧 Technical Improvements
- **Rich Console Capture**: Preserves CLI formatting in web interface
- **Progress UI Streaming**: Real-time agent thinking process via WebSocket
- **Path Management**: Proper Python path handling for deploy folder structure
- **Environment Isolation**: Clean separation of development and deployment configs

### 📚 Documentation Overhaul
- **Complete User Guide**: Step-by-step setup for new users (clone → deploy)
- **Prerequisites Documentation**: Clear requirements (vector database, API keys, etc.)
- **Architecture Explanation**: Hybrid local/cloud approach benefits
- **Troubleshooting Guides**: Common issues and solutions

### 🧪 Quality Assurance
- **Automated Test Suite**: 5-test web interface validation
- **Deployment Verification**: End-to-end testing from setup to public access
- **Error Handling**: Comprehensive error catching and user-friendly messages
- **Cross-Platform Testing**: macOS compatibility verified

### 🎯 User Experience
- **Zero-Config Web UI**: No frontend development needed
- **Instant Sharing**: Public ngrok URLs for beta testing and demos
- **Cost Transparency**: Clear OpenRouter usage and cost information
- **Easy Provider Switching**: Toggle between local and cloud LLMs

## [v2.1.0] - Adaptive Intelligence Architecture - 2024-12-28

### 🧠 Revolutionary Intelligence

#### **Adaptive Research Strategy**
- **Question Type Detection**: Agent intelligently classifies questions as simple_factual, follow_up_clarification, moderate_research, or deep_research
- **Dynamic Query Generation**: 1-3 queries for simple questions, 5-20 queries for complex research (no more forced limits)
- **Conditional Processing**: Skips unnecessary synthesis steps for simple factual questions
- **Strategy-Based Termination**: Simple questions terminate after 1 iteration with direct answers

#### **Performance Improvements**  
- **Faster Simple Answers**: "how many pandavas" → 3 queries, 31s duration (vs 20 queries, 90s+ previously)
- **Context Preservation**: Follow-up questions maintain conversation context ("who is their mother" understands Pandava context)
- **Intelligent Adaptation**: Complex philosophical questions still get full 20-query treatment when needed

#### **User Experience**
- **Natural Conversation Flow**: Follow-up clarifications work properly with maintained context
- **Appropriate Response Depth**: Simple questions get direct answers, complex ones get scholarly analysis
- **Efficient Resource Usage**: No more over-engineering simple requests

### 🔧 Technical Architecture
- **Upper Limits Philosophy**: Set maximum capabilities (20 queries) but let intelligence decide what's needed
- **Flexible Pipeline**: Each step (query generation, synthesis, reflection) adapts to question complexity
- **Smart Defaults**: Conservative fallbacks ensure system reliability while maximizing intelligence

---

## [v2.0.0] - Enhanced Deep Research Agent - 2024-12-28

### 🚀 Major Features

#### **Deep Research Architecture**
- **Query Decomposition**: Agent now breaks complex questions into 3-5 focused sub-queries
- **Iterative Expansion**: Learns concepts from each research cycle to generate better queries
- **Insight Synthesis**: Processes batches of passages (15-25 per cycle) into coherent insights
- **Smart Termination**: Agent decides when sufficient depth is achieved rather than hitting arbitrary limits
- **Increased Scale**: Up to 8 research iterations with 5 queries each (vs previous 4 iterations, 3 queries)

#### **Enhanced Progress Visibility**
- **Query Decomposition Display**: Real-time view of how questions are broken down
- **Insight Synthesis Progress**: Shows sources being processed and insight previews
- **Detailed Step Tracking**: Comprehensive view of agent's thinking process
- **Configurable Detail Level**: `SHOW_DETAILED_PROGRESS` option for granular control

#### **Response Quality Improvements**
- **Removed Token Limit**: Increased from 1000 to 8000 tokens for comprehensive responses
- **Structured Format**: New scholarly response template with sections:
  - I. Foundational Understanding
  - II. Diverse Perspectives  
  - III. Technical Analysis
  - IV. Practical Synthesis
  - V. Scholarly Assessment
- **Better Prompts**: Enhanced prompts for deeper analysis and more precise quotations

### 🔧 Technical Improvements

#### **Configuration Enhancements**
- Added `MAX_RESEARCH_ITERATIONS` (default: 8)
- Added `MAX_QUERIES_PER_ITERATION` (default: 5) 
- Added `RESEARCH_DEPTH_MODE` for future expansion
- Added `SHOW_DETAILED_PROGRESS` for UI control

#### **Chat History Integration**
- Fixed chat history context in follow-up questions
- Agent now maintains conversation context across queries
- Recent chat history (last 4 exchanges) included in response generation

#### **Error Handling**
- Improved EOF handling for piped input
- Better graceful degradation when progress UI fails
- Enhanced fallback mechanisms for LLM failures

### 🐛 Bug Fixes

#### **Critical Fixes**
- **Response Truncation**: Fixed 1000-token limit that was cutting off responses mid-sentence
- **Model Recognition**: Fixed `.env` file parsing (`OPENROUTER_CHAT_MODE` → `OPENROUTER_CHAT_MODEL`)
- **Progress Display**: Fixed empty progress updates during insight generation
- **EOF Handling**: Fixed crashes when using piped input

#### **Minor Fixes**
- Cleaned up progress UI display formatting
- Improved error messages and fallback behavior
- Fixed import organization and linting issues

### 📊 Performance Improvements

- **Faster Research**: Agent often completes in fewer iterations due to better query quality
- **Higher Confidence**: Typical confidence scores increased from ~50% to 80-95%
- **Efficient Termination**: Smart stopping reduces unnecessary computation
- **Better Synthesis**: Insight-based approach vs raw text concatenation

### 🔄 Breaking Changes

- **Configuration**: Some environment variable names changed (see migration guide)
- **Response Format**: New structured scholarly format (much more detailed)
- **Progress Display**: Enhanced UI may look different in some terminals

### 📚 Documentation

- Updated `README.md` with new features and examples
- Enhanced `AGENT_GUIDE.md` with configuration options
- Added comprehensive `CHANGELOG.md`
- Updated status from "ingestion running" to "complete"

### 🔧 Migration Guide

#### **Environment Variables**
```bash
# Old
MAX_ITERATIONS_PER_QUERY=4
MAX_PARALLEL_QUERIES=3

# New (add these)
MAX_RESEARCH_ITERATIONS=8
MAX_QUERIES_PER_ITERATION=5
SHOW_DETAILED_PROGRESS=true
```

#### **Model Configuration**
```bash
# Fix in .env file if you have this typo:
OPENROUTER_CHAT_MODE → OPENROUTER_CHAT_MODEL
```

### 📈 Metrics

- **Response Quality**: 8000+ token comprehensive responses vs previous ~1000 tokens
- **Research Depth**: Up to 40 queries (8 iterations × 5 queries) vs previous 12 queries  
- **Confidence**: Average confidence improved from 50% to 85%+
- **Speed**: Often faster due to smart termination despite more capabilities
- **Database**: Complete 363,461 documents indexed

---

## [v1.0.0] - Initial Release

### Features
- Basic RAG implementation with ChromaDB
- Simple agent with Plan-Search-Reflect loop
- Multi-provider LLM support (Ollama, OpenRouter)
- 363K+ documents from sacred texts
- Basic chat interface

### Technical
- ChromaDB vector storage
- Ollama embedding generation
- Rich terminal UI
- Command-line interfaces (query.py, chat.py, agent_chat.py)
