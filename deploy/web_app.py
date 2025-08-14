#!/usr/bin/env python3
"""
Web wrapper for Sacred Texts LLM - preserves rich console experience
Enables continuous deployment while maintaining CLI development workflow
"""

import asyncio
import json
import time
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.markdown import Markdown

from app.chat.core import SacredTextsChat
from app.agent.core import SacredTextsAgent
from app.agent.ui import SimpleProgressUI


# =============================================================================
# WEB CONSOLE CAPTURE
# =============================================================================

class WebConsole:
    """Captures rich console output for web streaming"""
    
    def __init__(self):
        self.messages = []
        self.websocket: Optional[WebSocket] = None
        
    def print(self, *args, **kwargs):
        """Capture console output and send to websocket if available"""
        # Convert rich objects to plain text for web
        text_parts = []
        for arg in args:
            if hasattr(arg, '__rich__'):
                # Handle rich objects
                text_parts.append(str(arg))
            else:
                text_parts.append(str(arg))
        
        message = " ".join(text_parts)
        self.messages.append({
            "type": "console",
            "content": message,
            "timestamp": time.time()
        })
        
        # Send to websocket if connected
        if self.websocket:
            try:
                asyncio.create_task(
                    self.websocket.send_text(json.dumps({
                        "type": "console",
                        "content": message,
                        "timestamp": time.time()
                    }))
                )
            except Exception:
                pass  # WebSocket might be closed
    
    def send_progress(self, step: str, details: str = "", progress: Optional[float] = None):
        """Send progress updates to web client"""
        if self.websocket:
            try:
                asyncio.create_task(
                    self.websocket.send_text(json.dumps({
                        "type": "progress",
                        "step": step,
                        "details": details,
                        "progress": progress,
                        "timestamp": time.time()
                    }))
                )
            except Exception:
                pass


# =============================================================================
# WEB PROGRESS UI
# =============================================================================

class WebProgressUI(SimpleProgressUI):
    """Web-compatible progress UI that streams updates"""
    
    def __init__(self, web_console: WebConsole):
        self.web_console = web_console
        
    def start_session(self, question: str):
        self.web_console.send_progress("start", f"🤖 Thinking about: {question}")
        
    def update_step(self, step, details: str = "", progress: Optional[float] = None):
        self.web_console.send_progress(step.value, details, progress)
        
    def complete_step(self, step, summary: str, details: List[str] = None):
        self.web_console.send_progress("complete", summary)
        
    def show_parallel_searches(self, queries: List[str]):
        self.web_console.send_progress("searching", f"🔍 Searching {len(queries)} parallel queries...")
        
    def show_evidence_evaluation(self, confidence: float, evidence_count: int):
        self.web_console.send_progress("evaluating", f"🤔 Confidence: {confidence:.1%} with {evidence_count} pieces of evidence")
        
    def finish_session(self, final_response: str, agent_state):
        self.web_console.send_progress("complete", f"✅ Complete in {agent_state.current_iteration} iterations")


# =============================================================================
# API MODELS
# =============================================================================

class QueryRequest(BaseModel):
    text: str
    mode: str = "chat"  # "chat" or "agent"
    stream: bool = True  # Whether to stream progress updates

class QueryResponse(BaseModel):
    response: str
    mode: str
    sources: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


# =============================================================================
# FASTAPI APP
# =============================================================================

app = FastAPI(
    title="Sacred Texts LLM",
    description="Dual-mode sacred texts interface: simple chat and deep research agent",
    version="1.0.0"
)

# Enable CORS for web interface
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global web console for capturing output
web_console = WebConsole()


@app.get("/", response_class=HTMLResponse)
async def root():
    """Simple web interface"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sacred Texts LLM</title>
        <style>
            body { font-family: monospace; margin: 20px; background: #1a1a1a; color: #fff; }
            .container { max-width: 800px; margin: 0 auto; }
            .mode-selector { margin-bottom: 20px; }
            .mode-btn { padding: 10px 20px; margin: 5px; border: none; border-radius: 5px; cursor: pointer; }
            .mode-btn.active { background: #4CAF50; color: white; }
            .mode-btn.inactive { background: #666; color: #ccc; }
            .provider-info { margin-bottom: 15px; padding: 10px; background: #2a2a2a; border-radius: 5px; display: flex; justify-content: space-between; align-items: center; }
            .provider-status { font-size: 14px; color: #4CAF50; }
            .refresh-btn { background: none; border: none; color: #4CAF50; cursor: pointer; font-size: 16px; }
            .input-area { margin-bottom: 20px; }
            #query { width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #444; background: #2a2a2a; color: #fff; }
            #submit { padding: 10px 20px; background: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer; }
            #output { background: #2a2a2a; padding: 15px; border-radius: 5px; min-height: 200px; white-space: pre-wrap; }
            .progress { color: #4CAF50; }
            .error { color: #f44336; }
            .response { color: #fff; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🕉️ Sacred Texts LLM</h1>
            
            <div class="provider-info">
                <span id="provider-status">Loading...</span>
                <button onclick="refreshProviderInfo()" class="refresh-btn">🔄</button>
            </div>
            
            <div class="mode-selector">
                <button class="mode-btn active" onclick="setMode('chat')">💬 Simple Chat</button>
                <button class="mode-btn inactive" onclick="setMode('agent')">🤖 Deep Research Agent</button>
            </div>
            
            <div class="input-area">
                <textarea id="query" placeholder="Ask about wisdom, spirituality, philosophy..." rows="3"></textarea>
                <br><br>
                <button id="submit" onclick="submitQuery()">Ask Question</button>
            </div>
            
            <div id="output">Ready to answer your questions...</div>
        </div>
        
        <script>
            let currentMode = 'chat';
            let ws = null;
            
            // Load provider info on page load
            window.onload = function() {
                refreshProviderInfo();
            };
            
            async function refreshProviderInfo() {
                try {
                    const response = await fetch('/info');
                    const data = await response.json();
                    const statusElement = document.getElementById('provider-status');
                    statusElement.innerHTML = `
                        <strong>Provider:</strong> ${data.current_provider.toUpperCase()} 
                        <strong>Model:</strong> ${data.chat_model}
                        <strong>Phase:</strong> ${data.phase}
                    `;
                } catch (error) {
                    document.getElementById('provider-status').innerHTML = 'Error loading provider info';
                }
            }
            
            function setMode(mode) {
                currentMode = mode;
                document.querySelectorAll('.mode-btn').forEach(btn => {
                    btn.classList.remove('active');
                    btn.classList.add('inactive');
                });
                event.target.classList.remove('inactive');
                event.target.classList.add('active');
            }
            
            function connectWebSocket() {
                ws = new WebSocket(`ws://${window.location.host}/ws`);
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    if (data.type === 'console') {
                        document.getElementById('output').innerHTML += '\\n' + data.content;
                    } else if (data.type === 'progress') {
                        document.getElementById('output').innerHTML += '\\n<span class="progress">' + data.details + '</span>';
                    }
                    document.getElementById('output').scrollTop = document.getElementById('output').scrollHeight;
                };
                ws.onclose = function() {
                    setTimeout(connectWebSocket, 1000);
                };
            }
            
            async function submitQuery() {
                const query = document.getElementById('query').value;
                if (!query.trim()) return;
                
                document.getElementById('output').innerHTML = 'Processing...\\n';
                document.getElementById('submit').disabled = true;
                
                try {
                    const response = await fetch('/query', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            text: query,
                            mode: currentMode,
                            stream: true
                        })
                    });
                    
                    const result = await response.json();
                    document.getElementById('output').innerHTML += '\\n<span class="response">' + result.response + '</span>';
                } catch (error) {
                    document.getElementById('output').innerHTML += '\\n<span class="error">Error: ' + error.message + '</span>';
                } finally {
                    document.getElementById('submit').disabled = false;
                }
            }
            
            // Connect WebSocket on page load
            connectWebSocket();
            
            // Allow Enter to submit
            document.getElementById('query').addEventListener('keydown', function(e) {
                if (e.key === 'Enter' && e.ctrlKey) {
                    submitQuery();
                }
            });
        </script>
    </body>
    </html>
    """


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Handle query requests for both chat and agent modes"""
    try:
        web_console.print(f"📝 New {request.mode} query: {request.text}")
        
        if request.mode == "chat":
            return await handle_chat_query(request)
        else:
            return await handle_agent_query(request)
            
    except Exception as e:
        web_console.print(f"❌ Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def handle_chat_query(request: QueryRequest) -> QueryResponse:
    """Handle simple chat mode query"""
    web_console.print("💬 Starting simple chat mode...")
    
    # Create chat instance with web console
    chat = SacredTextsChat()
    chat.console = web_console  # Replace console with web console
    
    if not chat.initialize():
        raise HTTPException(status_code=500, detail="Failed to initialize chat")
    
    # Get response
    response = chat.get_response(request.text)
    if not response:
        raise HTTPException(status_code=500, detail="Failed to generate response")
    
    # Get sources for metadata
    docs, metas = chat.search_texts(request.text)
    sources = []
    for meta in metas:
        if isinstance(meta, dict):
            source = meta.get("source_path", "unknown")
            source = source.replace("sacred_texts_archive/extracted/", "").replace(".txt", "")
            sources.append(source)
    
    web_console.print("✅ Chat response complete")
    
    return QueryResponse(
        response=response,
        mode="chat",
        sources=sources,
        metadata={"query_type": "simple_chat"}
    )


async def handle_agent_query(request: QueryRequest) -> QueryResponse:
    """Handle agent mode query with full research process"""
    web_console.print("🤖 Starting deep research agent mode...")
    
    # Create agent instance with web progress UI
    agent = SacredTextsAgent()
    agent.console = web_console  # Replace console with web console
    agent.progress_ui = WebProgressUI(web_console)  # Use web progress UI
    
    if not agent.initialize():
        raise HTTPException(status_code=500, detail="Failed to initialize agent")
    
    # Get agent response (this will stream progress via WebProgressUI)
    response = agent.agent_response(request.text)
    
    web_console.print("✅ Agent response complete")
    
    return QueryResponse(
        response=response,
        mode="agent",
        metadata={"query_type": "deep_research"}
    )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time progress updates"""
    await websocket.accept()
    web_console.websocket = websocket
    
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        web_console.websocket = None


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": time.time()}


@app.get("/info")
async def get_info():
    """Get system information"""
    # Get current provider info
    from app.agent import config as agent_config
    from app.chat import config as chat_config
    
    return {
        "name": "Sacred Texts LLM",
        "version": "1.0.0",
        "modes": ["chat", "agent"],
        "description": "Dual-mode sacred texts interface with simple chat and deep research capabilities",
        "current_provider": agent_config.LLM_PROVIDER,
        "chat_model": agent_config.OLLAMA_CHAT_MODEL if agent_config.LLM_PROVIDER == "ollama" else agent_config.OPENROUTER_CHAT_MODEL,
        "available_providers": ["ollama", "openrouter"],
        "phase": "Phase 2 - Local ChromaDB + Cloud OpenRouter" if agent_config.LLM_PROVIDER == "openrouter" else "Phase 1 - Local Ollama + ngrok exposure"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
