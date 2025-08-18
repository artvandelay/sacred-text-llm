import io
import sys
from types import SimpleNamespace


class DummyLLM:
    def generate_response(self, messages, model):
        # Return fixed answer regardless of input
        return "dummy answer"


class DummyCollection:
    def query(self, query_embeddings=None, n_results=5, include=None, **kwargs):
        return {
            "documents": [["Some context passage about kindness."]],
            "metadatas": [[{"source_path": "dummy/source.txt"}]],
            "distances": [[0.01]],
        }


class DummyClient:
    def __init__(self, *args, **kwargs):
        pass

    def get_or_create_collection(self, name, metadata=None):
        return DummyCollection()


def test_query_single_offline(monkeypatch, capsys):
    # Import target after monkeypatching modules it relies on
    import ollama
    import chromadb

    # Patch embeddings to fixed-size vector
    monkeypatch.setattr(ollama, "embeddings", lambda model, prompt: {"embedding": [0.0] * 768})

    # Patch chroma client
    monkeypatch.setattr(chromadb, "PersistentClient", lambda path=None: DummyClient())

    # Patch provider factory to avoid network
    import app.core.providers as providers
    monkeypatch.setattr(providers, "create_provider", lambda provider_name: DummyLLM())

    # Execute query.main with argv
    import importlib
    from importlib import reload
    import query as query_module

    # Simulate CLI args
    monkeypatch.setattr(sys, "argv", [sys.executable, "kindness", "--k", "3"]) 

    # Run main
    query_module.main()

    # Capture output
    out = capsys.readouterr().out
    assert "dummy answer" in out


