# Sacred Texts LLM - Deployment Guide

## Overview

This folder contains everything needed to deploy your Sacred Texts LLM application using a hybrid architecture:

- **Local ChromaDB**: Keeps your sacred texts data private and fast
- **Cloud OpenRouter**: Uses best-in-class LLMs (Claude, GPT-4) for superior responses
- **ngrok Integration**: Public HTTPS access for sharing and testing

## Prerequisites

> **⚠️ IMPORTANT**: You must complete data ingestion BEFORE deployment!

### Required Steps Before Deployment:
1. **Get sacred texts**: `python data/download_sacred_texts.py` OR contact authors for pre-built vector database
2. **Install Ollama**: `brew install ollama` (macOS) or visit [ollama.ai](https://ollama.ai)
3. **Create vector database** (if not using pre-built): `python data/ingest.py --sources sacred_texts_archive/extracted --mode fast`
4. **Verify vector store**: Should have 200K+ documents in `vector_store/chroma/`

### Additional Requirements:
- **Python 3.10+** with pip
- **~10GB free space** (texts + vector database)
- **OpenRouter API key** ([get one free](https://openrouter.ai/keys))
- **ngrok account** ([sign up free](https://ngrok.com/))

## Quick Start

```bash
# 1. Setup deployment environment
./deploy/setup.sh

# 2. Deploy with public access
./deploy/deploy.sh
```

## File Structure

```
deploy/
├── README.md                 # This file
├── deploy.sh                 # Main deployment script
├── setup.sh                 # Environment setup script
├── web_app.py               # FastAPI web wrapper
├── test_web.py              # Web interface testing
├── env.example              # Environment configuration template
└── PHASE2_GUIDE.md          # Detailed deployment guide
```

## Architecture

### Hybrid Deployment
- **LLM**: Cloud OpenRouter (Claude 3.5 Sonnet, GPT-4)
- **Database**: Local ChromaDB (sacred texts stay private)
- **Fallback**: Local Ollama (if OpenRouter fails)
- **Cost**: ~$0.01-0.50 per query
- **Quality**: Excellent
- **Use case**: Production-ready with reliability

## Commands

### Setup Commands
```bash
# Setup deployment environment
./deploy/setup.sh

# Check setup status
./deploy/setup.sh check
```

### Deployment Commands
```bash
# Start deployment
./deploy/deploy.sh

# Stop services
./deploy/deploy.sh stop

# Restart with changes
./deploy/deploy.sh restart

# Check status
./deploy/deploy.sh status

# View logs
./deploy/deploy.sh logs

# Cleanup
./deploy/deploy.sh cleanup
```

### Testing Commands
```bash
# Test web interface
python deploy/test_web.py

# Test CLI (unchanged)
python chat.py
python agent_chat.py
```

## Configuration

### Environment Files
- **`env.example`**: Hybrid deployment configuration template

### Key Settings
```bash
# LLM Provider
LLM_PROVIDER=ollama        # Local processing
LLM_PROVIDER=openrouter    # Cloud processing

# Models
OLLAMA_CHAT_MODEL=qwen3:30b-a3b
OPENROUTER_CHAT_MODEL=anthropic/claude-3.5-sonnet

# API Keys (for cloud processing)
OPENROUTER_API_KEY=your-key-here

# Deployment
WEB_PORT=8001
NGROK_REGION=us
```

## Switching Between Providers

### Local to Cloud
```bash
# Edit .env: LLM_PROVIDER=openrouter
# Add: OPENROUTER_API_KEY=your-key-here
./deploy/deploy.sh restart
```

### Cloud to Local
```bash
# Edit .env: LLM_PROVIDER=ollama
./deploy/deploy.sh restart
```

## Access Points

### Local Access
- **Web Interface**: http://localhost:8001
- **API**: http://localhost:8001/query
- **Health Check**: http://localhost:8001/health

### Public Access
- **ngrok URL**: Shown when you run `./deploy/deploy.sh`
- **Example**: https://abc123.ngrok-free.app

## API Usage

### Simple Chat
```bash
curl -X POST http://localhost:8001/query \
  -H "Content-Type: application/json" \
  -d '{"text": "What is compassion?", "mode": "chat"}'
```

### Deep Research Agent
```bash
curl -X POST http://localhost:8001/query \
  -H "Content-Type: application/json" \
  -d '{"text": "What is karma?", "mode": "agent"}'
```

## Monitoring

### Health Checks
```bash
# Check if running
./deploy/deploy.sh status

# Test functionality
python deploy/test_web.py

# View logs
./deploy/deploy.sh logs
```

### Cost Monitoring (OpenRouter)
- **OpenRouter Dashboard**: https://openrouter.ai/keys
- **Usage Tracking**: Real-time cost monitoring
- **Billing Alerts**: Set up payment limits

## Troubleshooting

### Common Issues

#### Setup Issues
```bash
# Reset everything
./deploy/deploy.sh cleanup
./deploy/setup_phase1.sh  # or setup_phase2.sh
./deploy/deploy.sh
```

#### Service Issues
```bash
# Check status
./deploy/deploy.sh status

# Restart services
./deploy/deploy.sh restart

# View logs
./deploy/deploy.sh logs
```

#### API Issues (OpenRouter)
```bash
# Check API key
curl -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  https://openrouter.ai/api/v1/models

# Switch to fallback
# Edit .env: LLM_PROVIDER=ollama
./deploy/deploy.sh restart
```

## Development Workflow

### Making Changes
1. **Edit code** in your CLI apps (`chat.py`, `agent_chat.py`)
2. **Test locally** with CLI interfaces
3. **Deploy instantly** with `./deploy/deploy.sh restart`
4. **Share URL** with beta users immediately

### Continuous Deployment
```bash
# After any code changes
./deploy/deploy.sh restart

# The web interface automatically reflects your changes
```

## Security

### Current Setup (Beta Testing)
- **No authentication** - suitable for trusted users
- **Local data** - ChromaDB stays on your machine
- **HTTPS exposure** - ngrok provides secure tunneling
- **No user data** - no persistent user information

### For Production
- **Add rate limiting** - prevent abuse
- **Implement authentication** - user management
- **Use static ngrok URL** - paid plan for stability
- **Consider cloud deployment** - Phase 3

## Support

### Getting Help
1. **Check logs**: `./deploy/deploy.sh logs`
2. **Run tests**: `python deploy/test_web.py`
3. **Check status**: `./deploy/deploy.sh status`
4. **Restart services**: `./deploy/deploy.sh restart`

### Documentation
- **Deployment Guide**: `PHASE2_GUIDE.md`
- **Main Guide**: `DEPLOYMENT_GUIDE.md` (in root)

### Useful Commands
```bash
# Full system check
./deploy/setup_phase1.sh check  # or setup_phase2.sh check
./deploy/deploy.sh status
python deploy/test_web.py

# Quick reset
./deploy/deploy.sh cleanup
./deploy/setup_phase1.sh  # or setup_phase2.sh
./deploy/deploy.sh
```

## Next Steps

### Phase 3: Full Cloud Deployment
- **Platform**: Supabase + Vercel/Replit
- **Features**: User accounts, persistent data, analytics
- **Deployment**: Professional cloud hosting
- **Scaling**: Handle hundreds of users

### Current Priorities
1. **Local Setup**: Get local deployment working with Ollama
2. **Cloud Upgrade**: Test with OpenRouter for better quality
3. **User Feedback**: Gather feedback from beta users
4. **Iterate**: Improve based on user needs

The deployment system is designed to be simple, reliable, and flexible. Start with local deployment for cost-free testing, then upgrade to cloud processing when you need better quality responses.
