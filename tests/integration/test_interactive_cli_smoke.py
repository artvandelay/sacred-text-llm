import subprocess
import sys
import time


def test_interactive_cli_starts_and_exits_quickly():
    # Start interactive CLI and immediately send 'quit' to ensure clean startup
    proc = subprocess.Popen(
        [sys.executable, "agent_chat.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        time.sleep(1)
        proc.stdin.write("quit\n")
        proc.stdin.flush()
        out, _ = proc.communicate(timeout=10)
        assert proc.returncode == 0
        assert "Sacred Texts Multi-Mode Chat" in out
    finally:
        try:
            proc.kill()
        except Exception:
            pass


