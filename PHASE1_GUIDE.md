# Phase 1: Local Ollama + ngrok Deployment

## Overview

Phase 1 deploys your Sacred Texts LLM using local Ollama models with ngrok exposure for beta testing. This setup provides:

- **Local LLM**: No API costs, no rate limits, full control
- **Fast responses**: No network latency
- **Privacy**: All data stays on your machine
- **Easy switching**: Can switch to OpenRouter later

## Quick Start

### 1. Initial Setup
```bash
# Run the Phase 1 setup script
./setup_phase1.sh

# This will:
# - Install dependencies
# - Set up Ollama with qwen3:30b-a3b model
# - Configure ngrok
# - Test the setup
```

### 2. Deploy
```bash
# Start the deployment
./deploy.sh

# This will:
# - Start the web server
# - Expose via ngrok
# - Show you the public URL
```

### 3. Access
- **Local**: http://localhost:8001
- **Public**: URL shown by ngrok (e.g., https://abc123.ngrok-free.app)

## Prerequisites

### Required Software
- **Python 3.10+**: Already installed
- **Ollama**: Install from https://ollama.ai/download
- **ngrok**: Will be installed automatically by setup script

### Required Data
- **Vector store**: Run `python data/ingest.py` first to create embeddings
- **Ollama model**: qwen3:30b-a3b (will be downloaded automatically)

### Required Configuration
- **ngrok auth token**: Get from https://dashboard.ngrok.com/get-started/your-authtoken

## Configuration

### Environment Variables (.env)
```bash
# Phase 1: Local Ollama
LLM_PROVIDER=ollama
OLLAMA_CHAT_MODEL=qwen3:30b-a3b
OLLAMA_BASE_URL=http://localhost:11434

# Vector database
EMBEDDING_MODEL=nomic-embed-text
VECTOR_STORE_DIR=vector_store/chroma
COLLECTION_NAME=sacred_texts

# Deployment
WEB_PORT=8001
WEB_HOST=0.0.0.0
NGROK_REGION=us
```

### Switching to OpenRouter (Phase 2)
To switch to cloud LLM later:
```bash
# Edit .env file
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your-api-key-here
OPENROUTER_CHAT_MODEL=anthropic/claude-3.5-sonnet

# Restart deployment
./deploy.sh restart
```

## Usage

### Web Interface
1. Visit the ngrok URL
2. Choose mode: **Simple Chat** or **Deep Research Agent**
3. Ask questions about sacred texts
4. Watch real-time progress for agent mode

### API Usage
```bash
# Simple chat
curl -X POST http://localhost:8001/query \
  -H "Content-Type: application/json" \
  -d '{"text": "What is compassion?", "mode": "chat"}'

# Deep research agent
curl -X POST http://localhost:8001/query \
  -H "Content-Type: application/json" \
  -d '{"text": "What is karma?", "mode": "agent"}'
```

### CLI Usage (Unchanged)
```bash
# Continue using your existing CLI interfaces
python chat.py          # Simple chat
python agent_chat.py    # Deep research agent
```

## Performance

### Expected Response Times
- **Simple Chat**: 2-5 seconds
- **Deep Research Agent**: 30-60 seconds
- **Memory Usage**: 8-16GB RAM (depending on model size)

### Concurrent Users
- **Recommended**: 5-10 simultaneous users
- **Maximum**: 20 users (may slow down with complex queries)

## Monitoring

### Health Checks
```bash
# Check if services are running
./deploy.sh status

# View logs
./deploy.sh logs

# Test functionality
python test_web.py
```

### Resource Monitoring
```bash
# Monitor memory usage
htop

# Check Ollama status
curl http://localhost:11434/api/tags

# Check web server
curl http://localhost:8001/health
```

## Troubleshooting

### Common Issues

#### Ollama Not Running
```bash
# Start Ollama
ollama serve

# Check if running
curl http://localhost:11434/api/tags
```

#### Model Not Found
```bash
# Install the model
ollama pull qwen3:30b-a3b

# List installed models
ollama list
```

#### ngrok Not Working
```bash
# Check authentication
ls ~/.ngrok2/ngrok.yml

# Re-authenticate
ngrok authtoken YOUR_TOKEN
```

#### Vector Store Missing
```bash
# Run ingestion
python data/ingest.py

# Check if created
ls -la vector_store/
```

### Performance Issues

#### Slow Responses
- Check if Ollama is using GPU: `nvidia-smi` (if available)
- Reduce model size or use smaller model
- Check memory usage: `htop`

#### High Memory Usage
- Close other applications
- Consider using smaller Ollama model
- Monitor with: `ps aux | grep ollama`

## Development Workflow

### Making Changes
1. **Edit code** in your CLI apps (`chat.py`, `agent_chat.py`)
2. **Test locally** with CLI interfaces
3. **Deploy instantly** with `./deploy.sh restart`
4. **Share URL** with beta users immediately

### Adding Features
- **CLI changes**: Automatically reflected in web interface
- **Configuration changes**: Edit `.env` and restart
- **New models**: Update `OLLAMA_CHAT_MODEL` in `.env`

## Security

### Current Setup (Beta Testing)
- **No authentication** - suitable for trusted users
- **Local data** - all processing on your machine
- **ngrok exposure** - temporary public access

### For Production
- Add rate limiting
- Implement user authentication
- Use static ngrok URL (paid plan)
- Consider cloud deployment

## Next Steps

### Phase 2: Hybrid Setup
- Keep local ChromaDB
- Switch to OpenRouter for better chat models
- Improved response quality
- Some API costs

### Phase 3: Full Cloud
- Migrate to Supabase + Vercel
- Professional sharing
- User accounts and persistence
- Full cloud deployment

## Support

### Getting Help
1. Check logs: `./deploy.sh logs`
2. Run tests: `python test_web.py`
3. Check status: `./deploy.sh status`
4. Restart services: `./deploy.sh restart`

### Useful Commands
```bash
# Full reset
./deploy.sh cleanup
./setup_phase1.sh
./deploy.sh

# Check everything
./setup_phase1.sh check
./deploy.sh status
python test_web.py
```

Phase 1 is designed to be simple, reliable, and cost-effective for beta testing while maintaining your existing development workflow.
