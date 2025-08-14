# Phase 2: Hybrid Deployment - Local ChromaDB + Cloud OpenRouter

## Overview

Phase 2 deploys your Sacred Texts LLM using a hybrid approach: local ChromaDB for data privacy with cloud OpenRouter LLM for superior response quality. This setup provides:

- **Better Quality**: Cloud LLM (Claude 3.5 Sonnet) for superior responses
- **Data Privacy**: Local ChromaDB keeps your sacred texts data private
- **Cost Control**: Pay-per-use API costs with monitoring
- **Reliability**: Ollama fallback if OpenRouter fails
- **Easy Switching**: Can switch back to Phase 1 anytime

## Quick Start

### 1. Get OpenRouter API Key
```bash
# Visit: https://openrouter.ai/keys
# Sign up/login to get your API key
```

### 2. Setup Phase 2
```bash
# Run the Phase 2 setup script
./deploy/setup_phase2.sh

# This will:
# - Configure for OpenRouter
# - Validate your API key
# - Set up Ollama fallback
# - Test the setup
```

### 3. Deploy
```bash
# Start the deployment
./deploy/deploy.sh

# This will:
# - Start the web server
# - Expose via ngrok
# - Show you the public URL
```

### 4. Access
- **Local**: http://localhost:8001
- **Public**: URL shown by ngrok (e.g., https://abc123.ngrok-free.app)

## Configuration

### Environment Variables (.env)
```bash
# Phase 2: Cloud OpenRouter
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your-api-key-here
OPENROUTER_CHAT_MODEL=anthropic/claude-3.5-sonnet

# Local ChromaDB (data privacy)
EMBEDDING_MODEL=nomic-embed-text
VECTOR_STORE_DIR=vector_store/chroma
COLLECTION_NAME=sacred_texts

# Ollama fallback
OLLAMA_CHAT_MODEL=qwen3:30b-a3b
ENABLE_OLLAMA_FALLBACK=true

# Deployment
WEB_PORT=8001
WEB_HOST=0.0.0.0
NGROK_REGION=us
```

### Available OpenRouter Models
```bash
# Recommended models (edit in .env):
OPENROUTER_CHAT_MODEL=anthropic/claude-3.5-sonnet    # Best balance
OPENROUTER_CHAT_MODEL=anthropic/claude-3-opus-20240229 # Best quality, higher cost
OPENROUTER_CHAT_MODEL=openai/gpt-4o-mini             # Good balance
OPENROUTER_CHAT_MODEL=meta-llama/llama-3.1-70b-instruct # Open source option
```

## Usage

### Web Interface
1. Visit the ngrok URL
2. Choose mode: **Simple Chat** or **Deep Research Agent**
3. Ask questions about sacred texts
4. Watch real-time progress for agent mode
5. Notice improved response quality from cloud LLM

### API Usage
```bash
# Simple chat (OpenRouter)
curl -X POST http://localhost:8001/query \
  -H "Content-Type: application/json" \
  -d '{"text": "What is compassion?", "mode": "chat"}'

# Deep research agent (OpenRouter)
curl -X POST http://localhost:8001/query \
  -H "Content-Type: application/json" \
  -d '{"text": "What is karma?", "mode": "agent"}'
```

### CLI Usage (Unchanged)
```bash
# Continue using your existing CLI interfaces
python chat.py          # Simple chat (now uses OpenRouter)
python agent_chat.py    # Deep research agent (now uses OpenRouter)
```

## Performance

### Expected Response Times
- **Simple Chat**: 3-8 seconds (network + processing)
- **Deep Research Agent**: 45-90 seconds (multiple API calls)
- **Memory Usage**: 4-8GB RAM (reduced from Phase 1)

### Quality Improvements
- **Better reasoning**: Cloud LLM provides more nuanced responses
- **Improved synthesis**: Better integration of multiple sources
- **Enhanced creativity**: More sophisticated analysis and insights
- **Consistent quality**: Professional-grade responses

### Cost Considerations
- **Simple Chat**: ~$0.01-0.05 per query
- **Deep Research Agent**: ~$0.10-0.50 per query
- **Monthly estimate**: $10-100 depending on usage

## Cost Monitoring

### OpenRouter Dashboard
- **Monitor usage**: https://openrouter.ai/keys
- **Track costs**: Real-time cost tracking
- **Usage analytics**: Query volume and model usage
- **Billing**: Set up payment methods and limits

### Cost Optimization
```bash
# Use cheaper models for testing
OPENROUTER_CHAT_MODEL=openai/gpt-4o-mini

# Use higher quality for production
OPENROUTER_CHAT_MODEL=anthropic/claude-3.5-sonnet

# Use best quality for complex research
OPENROUTER_CHAT_MODEL=anthropic/claude-3-opus-20240229
```

## Reliability Features

### Ollama Fallback
- **Automatic fallback**: If OpenRouter fails, switches to local Ollama
- **Seamless transition**: Users don't notice the switch
- **Reliability**: Ensures service availability
- **Cost protection**: Prevents API failures from breaking service

### Error Handling
- **API timeouts**: Automatic retry with exponential backoff
- **Rate limiting**: Respects OpenRouter rate limits
- **Network issues**: Graceful degradation to fallback
- **Model unavailability**: Automatic model switching

## Monitoring

### Health Checks
```bash
# Check if services are running
./deploy/deploy.sh status

# View logs
./deploy/deploy.sh logs

# Test functionality
python deploy/test_web.py
```

### API Monitoring
```bash
# Check OpenRouter status
curl -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  https://openrouter.ai/api/v1/models

# Monitor costs
# Visit: https://openrouter.ai/keys
```

### Performance Monitoring
```bash
# Monitor response times
# Check web interface for real-time feedback

# Monitor memory usage
htop

# Check network connectivity
ping openrouter.ai
```

## Troubleshooting

### Common Issues

#### OpenRouter API Key Issues
```bash
# Check if API key is valid
curl -H "Authorization: Bearer YOUR_KEY" \
  https://openrouter.ai/api/v1/models

# Re-setup if needed
./deploy/setup_phase2.sh
```

#### High Costs
```bash
# Switch to cheaper model
# Edit .env: OPENROUTER_CHAT_MODEL=openai/gpt-4o-mini
./deploy/deploy.sh restart

# Or switch back to Phase 1
# Edit .env: LLM_PROVIDER=ollama
./deploy/deploy.sh restart
```

#### Slow Responses
```bash
# Check network connectivity
ping openrouter.ai

# Check if fallback is working
# Look for Ollama usage in logs
./deploy/deploy.sh logs
```

#### API Rate Limits
```bash
# Check current usage
# Visit: https://openrouter.ai/keys

# Reduce concurrent users
# Or upgrade OpenRouter plan
```

### Performance Issues

#### Network Latency
- **Use closer regions**: Consider OpenRouter region settings
- **Optimize queries**: Reduce unnecessary API calls
- **Cache responses**: Consider implementing response caching

#### High Memory Usage
- **Monitor Ollama**: Check if fallback is consuming resources
- **Optimize ChromaDB**: Consider database optimization
- **Reduce concurrent users**: Limit simultaneous requests

## Development Workflow

### Making Changes
1. **Edit code** in your CLI apps (`chat.py`, `agent_chat.py`)
2. **Test locally** with CLI interfaces
3. **Deploy instantly** with `./deploy/deploy.sh restart`
4. **Share URL** with beta users immediately

### Testing Different Models
```bash
# Test different OpenRouter models
# Edit .env file and restart
OPENROUTER_CHAT_MODEL=anthropic/claude-3.5-sonnet
./deploy/deploy.sh restart

# Compare quality and costs
# Monitor OpenRouter dashboard
```

### A/B Testing
```bash
# Test Phase 1 vs Phase 2
# Switch between providers
LLM_PROVIDER=ollama      # Phase 1
LLM_PROVIDER=openrouter  # Phase 2
./deploy/deploy.sh restart
```

## Security

### Current Setup (Beta Testing)
- **API key security**: Store securely in .env file
- **Local data**: ChromaDB remains on your machine
- **Network security**: HTTPS via ngrok
- **No user data**: No persistent user data stored

### For Production
- **API key rotation**: Regular key updates
- **Rate limiting**: Implement request limits
- **User authentication**: Add user management
- **Data encryption**: Encrypt sensitive data

## Migration Path

### From Phase 1 to Phase 2
```bash
# Easy migration
./deploy/setup_phase2.sh
./deploy/deploy.sh restart
```

### From Phase 2 to Phase 1
```bash
# Switch back anytime
# Edit .env: LLM_PROVIDER=ollama
./deploy/deploy.sh restart
```

### To Phase 3 (Future)
- **Full cloud deployment**: Supabase + Vercel
- **User accounts**: Persistent user data
- **Professional sharing**: Public deployment
- **Advanced features**: User management, analytics

## Support

### Getting Help
1. Check logs: `./deploy/deploy.sh logs`
2. Run tests: `python deploy/test_web.py`
3. Check status: `./deploy/deploy.sh status`
4. Restart services: `./deploy/deploy.sh restart`

### Useful Commands
```bash
# Full reset
./deploy/deploy.sh cleanup
./deploy/setup_phase2.sh
./deploy/deploy.sh

# Check everything
./deploy/setup_phase2.sh check
./deploy/deploy.sh status
python deploy/test_web.py

# Monitor costs
# Visit: https://openrouter.ai/keys
```

### Cost Management
```bash
# Set up billing alerts
# Visit OpenRouter dashboard

# Monitor usage patterns
# Adjust model selection based on costs

# Consider hybrid approach
# Use cheaper models for simple queries
# Use premium models for complex research
```

Phase 2 provides the best of both worlds: superior response quality from cloud LLMs while maintaining data privacy with local ChromaDB. The hybrid approach ensures reliability and cost control while delivering professional-grade responses.
