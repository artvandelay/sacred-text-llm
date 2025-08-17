import subprocess
import sys


def run_cli(args: list[str], timeout: int = 60) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, "agent_chat.py"] + args,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def test_cli_contemplative_response():
    code, out = run_cli(["--mode", "contemplative", "--query", "What is kindness?"], timeout=60)
    assert code == 0, out
    assert "Response:" in out
    # Ensure some non-empty content after Response
    assert len(out.split("Response:")[-1].strip()) > 20


def test_cli_deep_research_response():
    code, out = run_cli(["--mode", "deep_research", "--query", "What is wisdom?"], timeout=120)
    assert code == 0, out
    assert "Response:" in out
    assert len(out.split("Response:")[-1].strip()) > 20

