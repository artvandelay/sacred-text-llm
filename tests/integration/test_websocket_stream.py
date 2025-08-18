import subprocess
import sys
import time
import json
import pytest

try:
    import websockets
    import asyncio
except Exception:
    websockets = None


def test_websocket_streaming_if_available():
    if websockets is None:
        pytest.skip("websockets not installed")
        return  # skip if websockets not installed

    # Start server
    env = None
    proc = subprocess.Popen([sys.executable, "deploy/web_app.py"], env=env)
    try:
        time.sleep(3)

        async def run_ws():
            uri = "ws://127.0.0.1:8001/ws"
            async with websockets.connect(uri) as ws:
                await ws.send(json.dumps({"text": "What is kindness?", "mode": "contemplative"}))
                updates = []
                while True:
                    msg = await ws.recv()
                    data = json.loads(msg)
                    updates.append(data)
                    if data.get("type") in {"response", "error"}:
                        break
                assert any(u.get("type") == "update" for u in updates) or any(
                    u.get("type") == "response" for u in updates
                )

        asyncio.get_event_loop().run_until_complete(run_ws())
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()


