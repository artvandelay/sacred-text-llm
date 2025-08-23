import sys
import types


if "ollama" not in sys.modules:
    sys.modules["ollama"] = types.SimpleNamespace(
        embeddings=lambda model, prompt: {"embedding": [0.0] * 768}
    )

if "chromadb" not in sys.modules:
    sys.modules["chromadb"] = types.SimpleNamespace()

