import types

from app.modes.contemplative import ContemplativeMode


class DummyLLM:
    def generate_response(self, messages, model):
        return "What does this passage invite you to practice right now?"


class DummyCollection:
    def query(self, query_embeddings=None, n_results=1, include=None, **kwargs):
        # Mimic chroma response shape
        return {
            "documents": [[
                "A gentle answer turns away wrath, but a harsh word stirs up anger."
            ]],
            "metadatas": [[{"source": "proverbs/15:1"}]],
            "distances": [[0.01]],
        }


def test_contemplative_yields_and_returns(monkeypatch):
    # Patch ollama.embeddings to avoid network
    import ollama
    monkeypatch.setattr(ollama, "embeddings", lambda model, prompt: {"embedding": [0.0] * 768})

    mode = ContemplativeMode(DummyLLM(), DummyCollection())
    gen = mode.run("kindness")

    updates = []
    try:
        while True:
            try:
                updates.append(next(gen))
            except StopIteration as e:
                final = e.value
                break
    except Exception as e:
        raise AssertionError(f"Mode errored: {e}")

    assert any(u.get("type") == "passage_found" for u in updates)
    assert isinstance(final, str) and len(final) > 0

