# Sacred Texts LLM - Deployment Guide

## Overview

This folder contains everything needed to deploy your Sacred Texts LLM application using a hybrid architecture:

- **Local ChromaDB**: Keeps your sacred texts data private and fast
- **Cloud OpenRouter**: Uses best-in-class LLMs (Claude, GPT-4) for superior responses
- **ngrok Integration**: Public HTTPS access for sharing and testing

## Quick Start

```bash
# Setup deployment environment
./deploy/setup.sh

# Deploy with public access
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
# Phase 1 setup
./deploy/setup_phase1.sh

# Phase 2 setup
./deploy/setup_phase2.sh

# Check setup
./deploy/setup_phase1.sh check
./deploy/setup_phase2.sh check
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
- **`env.example`**: Phase 1 configuration (Ollama)
- **`env.phase2.example`**: Phase 2 configuration (OpenRouter)

### Key Settings
```bash
# LLM Provider
LLM_PROVIDER=ollama        # Phase 1
LLM_PROVIDER=openrouter    # Phase 2

# Models
OLLAMA_CHAT_MODEL=qwen3:30b-a3b
OPENROUTER_CHAT_MODEL=anthropic/claude-3.5-sonnet

# API Keys (Phase 2)
OPENROUTER_API_KEY=your-key-here

# Deployment
WEB_PORT=8001
NGROK_REGION=us
```

## Switching Between Phases

### Phase 1 → Phase 2
```bash
./deploy/setup_phase2.sh
./deploy/deploy.sh restart
```

### Phase 2 → Phase 1
```bash
# Edit .env file
LLM_PROVIDER=ollama
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

### Cost Monitoring (Phase 2)
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

#### API Issues (Phase 2)
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
- **Phase 1 Guide**: `PHASE1_GUIDE.md`
- **Phase 2 Guide**: `PHASE2_GUIDE.md`
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
1. **Phase 1**: Get local deployment working
2. **Phase 2**: Test with OpenRouter for better quality
3. **User Feedback**: Gather feedback from beta users
4. **Iterate**: Improve based on user needs

The deployment system is designed to be simple, reliable, and flexible. Start with Phase 1 for cost-free testing, then upgrade to Phase 2 when you need better quality responses.
