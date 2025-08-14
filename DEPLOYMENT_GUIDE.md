# Sacred Texts LLM - Continuous Deployment Guide

## Overview

This guide explains how to deploy your Sacred Texts LLM application for continuous development and user testing. The system preserves your rich CLI experience while making it web-accessible.

## Architecture

### Dual-Mode Interface
- **💬 Simple Chat**: Direct Q&A with 5-passage retrieval
- **🤖 Deep Research Agent**: Multi-iteration research with parallel queries, reflection, and synthesis

### Web Wrapper Design
- **Preserves CLI Experience**: All rich console output is captured and streamed to web
- **Real-time Progress**: WebSocket streaming shows agent thinking process
- **Separate Endpoints**: `/chat` and `/agent` modes available via API
- **Simple Web UI**: Built-in interface for easy testing

## Quick Start

### 1. Prerequisites
```bash
# Install ngrok (if not already installed)
brew install ngrok/ngrok/ngrok

# Get ngrok auth token from: https://dashboard.ngrok.com/get-started/your-authtoken
ngrok authtoken YOUR_TOKEN
```

### 2. Deploy
```bash
# Start deployment (installs dependencies, starts web server, exposes via ngrok)
./deploy.sh

# Or manually:
pip install -r requirements.txt
python web_app.py  # Starts on http://localhost:8001
ngrok http 8001    # Exposes to public URL
```

### 3. Access
- **Local**: http://localhost:8001
- **Public**: URL shown by ngrok (e.g., https://abc123.ngrok-free.app)
- **API**: POST to `/query` with `{"text": "question", "mode": "chat"}` or `"agent"`

## Development Workflow

### Local Development (Unchanged)
```bash
# Continue using your existing CLI interfaces
python chat.py          # Simple chat mode
python agent_chat.py    # Deep research agent mode
```

### Web Deployment (New)
```bash
# Deploy changes instantly
./deploy.sh restart     # Restart with latest code changes

# Or manual restart
./deploy.sh stop
./deploy.sh start
```

### Continuous Updates
1. **Make code changes** to your CLI apps
2. **Test locally** with `python chat.py` or `python agent_chat.py`
3. **Deploy instantly** with `./deploy.sh restart`
4. **Share URL** with beta users immediately

## API Reference

### Query Endpoint
```http
POST /query
Content-Type: application/json

{
  "text": "What is the meaning of compassion?",
  "mode": "chat"  // or "agent"
}
```

### Response Format
```json
{
  "response": "Based on sacred texts...",
  "mode": "chat",
  "sources": ["buddhism/dhammapada", "christianity/sermon-on-mount"],
  "metadata": {
    "query_type": "simple_chat"
  }
}
```

### WebSocket Progress Updates
Connect to `/ws` for real-time progress:
```javascript
const ws = new WebSocket('ws://localhost:8001/ws');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'progress') {
    console.log(`${data.step}: ${data.details}`);
  }
};
```

## Deployment Commands

### Basic Operations
```bash
./deploy.sh start      # Start web server + ngrok
./deploy.sh stop       # Stop all services
./deploy.sh restart    # Restart with latest code
./deploy.sh status     # Check if services are running
./deploy.sh logs       # View recent logs
./deploy.sh cleanup    # Stop and clean up files
```

### Environment Variables
```bash
export WEB_PORT=8001           # Web server port
export WEB_HOST=0.0.0.0        # Web server host
export NGROK_REGION=us         # ngrok region
```

## Monitoring & Debugging

### Health Checks
```bash
# Check if services are running
./deploy.sh status

# View logs
./deploy.sh logs

# Test API directly
curl -X POST http://localhost:8001/query \
  -H "Content-Type: application/json" \
  -d '{"text": "test", "mode": "chat"}'
```

### Common Issues

#### Web Server Won't Start
```bash
# Check if port is in use
lsof -i :8001

# Kill existing process
./deploy.sh stop
./deploy.sh start
```

#### ngrok Connection Issues
```bash
# Check ngrok authentication
ls ~/.ngrok2/ngrok.yml

# Re-authenticate if needed
ngrok authtoken YOUR_TOKEN
```

#### Vector Store Issues
```bash
# Check if vector store exists
ls -la vector_store/

# Re-run ingestion if needed
python data/ingest.py
```

## Security Considerations

### For Beta Testing (Current Setup)
- **No authentication** - suitable for trusted beta users
- **Rate limiting** - consider adding for production
- **CORS enabled** - allows web interface access

### For Production
```python
# Add to web_app.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/query")
@limiter.limit("10/minute")  # Rate limit
async def query(request: QueryRequest):
    # ... existing code
```

## Performance Optimization

### Current Setup
- **Local Ollama**: No API latency, no rate limits
- **Local ChromaDB**: Fast vector search
- **Parallel processing**: Agent handles concurrent queries efficiently

### Scaling Considerations
- **Memory usage**: 30M words + embeddings + LLM model (~8-16GB RAM)
- **Response time**: Chat mode ~2-5s, Agent mode ~30-60s
- **Concurrent users**: Test with 5-10 simultaneous users

### Monitoring
```bash
# Monitor resource usage
htop
# or
top -p $(cat .web_server.pid)

# Check ngrok dashboard
open http://localhost:4040
```

## Integration Examples

### Python Client
```python
import requests

def query_sacred_texts(question: str, mode: str = "chat"):
    response = requests.post(
        "http://localhost:8001/query",
        json={"text": question, "mode": mode}
    )
    return response.json()

# Usage
result = query_sacred_texts("What is karma?", mode="agent")
print(result["response"])
```

### JavaScript Client
```javascript
async function querySacredTexts(question, mode = 'chat') {
    const response = await fetch('/query', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({text: question, mode: mode})
    });
    return await response.json();
}

// Usage
const result = await querySacredTexts('What is karma?', 'agent');
console.log(result.response);
```

## Migration Path

### Phase 1: Current (Local + ngrok)
- ✅ Local ChromaDB + Ollama models
- ✅ ngrok exposure for beta testing
- ✅ Dual-mode interface

### Phase 2: Hybrid (Local DB + Cloud LLM)
- 🔄 Local ChromaDB + OpenRouter API
- 🔄 Better chat models while keeping data local
- 🔄 Improved response quality

### Phase 3: Full Cloud (Future)
- 📋 Supabase + Vercel/Replit
- 📋 Professional sharing and scaling
- 📋 User accounts and persistence

## Troubleshooting

### Development Issues
```bash
# Reset everything
./deploy.sh cleanup
pip install -r requirements.txt --force-reinstall
./deploy.sh start

# Check Python environment
python -c "import fastapi, uvicorn, websockets; print('Dependencies OK')"
```

### Performance Issues
```bash
# Monitor memory usage
ps aux | grep python
ps aux | grep ngrok

# Check disk space (for vector store)
df -h vector_store/
```

### Network Issues
```bash
# Test local connectivity
curl http://localhost:8001/health

# Test ngrok tunnel
curl $(cat .ngrok_url)/health
```

## Support

For issues or questions:
1. Check logs: `./deploy.sh logs`
2. Check status: `./deploy.sh status`
3. Restart services: `./deploy.sh restart`
4. Full reset: `./deploy.sh cleanup && ./deploy.sh start`

The deployment system is designed to be robust and self-healing, but manual intervention may be needed for complex issues.
