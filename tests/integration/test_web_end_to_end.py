import subprocess
import sys
import time
import os
import requests


def test_web_query_end_to_end():
    env = os.environ.copy()
    # Start server
    proc = subprocess.Popen([sys.executable, "deploy/web_app.py"], env=env)
    try:
        # Wait a moment for server to start
        time.sleep(3)
        for mode, text in [("contemplative", "What is kindness?"), ("deep_research", "What is wisdom?")]:
            r = requests.post(
                "http://127.0.0.1:8001/query",
                json={"text": text, "mode": mode},
                timeout=90,
            )
            assert r.status_code == 200, r.text
            data = r.json()
            assert isinstance(data.get("updates"), list)
            assert isinstance(data.get("response"), str)
            assert len(data["response"].strip()) > 20
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()

