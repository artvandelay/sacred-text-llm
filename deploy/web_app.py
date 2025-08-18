#!/usr/bin/env python3
"""
Minimal FastAPI web wrapper for the Sacred Texts LLM modes.

This provides a simple web interface and API for accessing all modes.
"""

import os
import sys
import asyncio
import json
import logging
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import chromadb
import uvicorn

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.providers import create_provider
from app.modes.registry import MODES, get_mode, list_modes
from app.agent import config as agent_config
from app.core.vector_store import ChromaVectorStore


class QueryRequest(BaseModel):
    text: str
    mode: str = "deep_research"
    chat_history: Optional[List[Dict]] = None


# Simple connection tracking
active_connections: List[WebSocket] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup."""
    # Initialize on startup
    logging.info("Starting Sacred Texts Web API...")
    logging.info("Available modes: %s", list(MODES.keys()))
    yield
    # Cleanup on shutdown
    logging.info("Shutting down...")


app = FastAPI(title="Sacred Texts LLM", lifespan=lifespan)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the minimal web interface."""
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(html_path):
        with open(html_path) as f:
            return f.read()
    
    # Fallback minimal HTML
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Sacred Texts LLM</title>
    <style>
        body { font-family: system-ui; max-width: 600px; margin: 50px auto; padding: 20px; }
        input, button, select { display: block; width: 100%; margin: 10px 0; padding: 10px; }
        #results { margin-top: 20px; white-space: pre-wrap; background: #f5f5f5; padding: 15px; }
    </style>
</head>
<body>
    <h1>Sacred Texts LLM</h1>
    <select id="mode">
        <option value="deep_research">Deep Research</option>
        <option value="contemplative">Contemplative</option>
    </select>
    <input type="text" id="query" placeholder="Ask a question..." />
    <button onclick="submitQuery()">Submit</button>
    <div id="results"></div>
    
    <script>
        function submitQuery() {
            const mode = document.getElementById('mode').value;
            const query = document.getElementById('query').value;
            const results = document.getElementById('results');
            
            results.textContent = 'Processing...';
            
            fetch('/query', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({text: query, mode: mode})
            })
            .then(r => r.json())
            .then(data => {
                results.textContent = data.response || 'No response';
            })
            .catch(err => {
                results.textContent = 'Error: ' + err;
            });
        }
    </script>
</body>
</html>
"""


@app.get("/info")
async def info():
    """Return information about available modes."""
    return {
        "modes": {name: {"description": info["description"]} for name, info in MODES.items()},
        "default_mode": "deep_research"
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/version")
async def version():
    # Simple version info; could be wired to git hash via env later
    return {"version": "modes-architecture-initial"}


@app.post("/query")
async def query(request: QueryRequest):
    """Non-streaming endpoint for simple API access."""
    try:
        # Initialize dependencies
        llm = create_provider(agent_config.LLM_PROVIDER)
        db = chromadb.PersistentClient(path=agent_config.VECTOR_STORE_DIR)
        collection = db.get_or_create_collection(
            name=agent_config.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
        store = ChromaVectorStore(collection)
        # Get mode and run query
        mode = get_mode(request.mode, llm, store)
        generator = mode.run(request.text, request.chat_history)
        
        # Collect all updates
        updates = []
        response = None
        
        try:
            # Manually iterate to catch the return value
            while True:
                try:
                    update = next(generator)
                    updates.append(update)
                except StopIteration as e:
                    response = e.value
                    break
        except Exception as e:
            # Handle other errors during generation
            pass
        
        return {"updates": updates, "response": response or "No response generated"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for streaming responses."""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        # Wait for query
        data = await websocket.receive_json()
        
        # Initialize dependencies
        llm = create_provider(agent_config.LLM_PROVIDER)
        db = chromadb.PersistentClient(path=agent_config.VECTOR_STORE_DIR)
        collection = db.get_or_create_collection(
            name=agent_config.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
        store = ChromaVectorStore(collection)
        # Get mode
        mode_name = data.get("mode", "deep_research")
        query_text = data.get("text", "")
        chat_history = data.get("chat_history")
        
        mode = get_mode(mode_name, llm, store)
        
        # Run query and stream results
        generator = mode.run(query_text, chat_history)
        
        try:
            async for update in async_generator_wrapper(generator):
                # Format update for display
                update_msg = format_update_for_display(update)
                if update_msg:
                    await websocket.send_json({
                        "type": "update",
                        "content": update_msg
                    })
        except StopIteration as e:
            # Send final response
            await websocket.send_json({
                "type": "response",
                "content": e.value or "No response generated"
            })
            
    except Exception as e:
        logging.exception("WebSocket error")
        await websocket.send_json({
            "type": "error",
            "content": str(e)
        })
    finally:
        active_connections.remove(websocket)


async def async_generator_wrapper(sync_gen):
    """Wrap a synchronous generator for async iteration."""
    loop = asyncio.get_event_loop()
    
    while True:
        try:
            # Run synchronous next() in executor
            value = await loop.run_in_executor(None, next, sync_gen)
            yield value
        except StopIteration as e:
            # Propagate the return value
            raise StopIteration(e.value)


def format_update_for_display(update: Dict[str, Any]) -> str:
    """Format update messages for web display."""
    update_type = update.get("type", "")
    
    if update_type == "planning":
        return f"🤔 {update.get('content', 'Planning...')}"
    elif update_type == "searching":
        return f"🔍 {update.get('content', 'Searching...')}"
    elif update_type == "synthesizing":
        return f"✨ {update.get('content', 'Synthesizing...')}"
    elif update_type == "generating":
        return f"✍️ {update.get('content', 'Generating response...')}"
    elif update_type == "error":
        return f"❌ Error: {update.get('error', 'Unknown error')}"
    elif update_type == "confidence_reached":
        return f"✅ Confidence threshold reached: {update.get('confidence', 0):.0%}"
    elif update_type == "iteration_start":
        return f"🔄 Starting iteration {update.get('iteration')} of {update.get('max_iterations')}"
    
    # For other types, only show if there's meaningful content
    content = update.get("content")
    if content and update_type not in ["session_start", "search_complete", "complete"]:
        return f"• {content}"
    
    return ""


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)