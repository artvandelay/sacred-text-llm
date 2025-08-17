import types

from app.modes.deep_research import DeepResearchMode


class DummyLLM:
    def __init__(self):
        self.calls = []

    def generate_response(self, messages, model):
        # Record prompt type for basic assurance
        self.calls.append((messages[0]["content"][:20], model))
        # Return minimal valid JSON for planner/reflector; full text for final/synthesis
        user = messages[-1]["content"]
        if "Respond in JSON" in user or "Respond in JSON format" in user:
            return '{"reasoning":"ok","needs_search":false,"search_queries":["q"],"expected_insights":"ok"}'
        return "Some synthesis"


class DummyCollection:
    def __init__(self):
        self.queries = 0

    def query(self, query_embeddings=None, n_results=5, include=None, **kwargs):
        self.queries += 1
        return {
            "documents": [["doc one", "doc two"]],
            "metadatas": [[{"source": "s1"}, {"source": "s2"}]],
            "distances": [[0.01, 0.02]],
        }


def test_deep_research_runs_minimal(monkeypatch):
    # Patch embeddings to fixed size
    import ollama
    monkeypatch.setattr(ollama, "embeddings", lambda model, prompt: {"embedding": [0.0] * 768})

    llm = DummyLLM()
    db = DummyCollection()

    mode = DeepResearchMode(llm, db)
    gen = mode.run("what is wisdom?")

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

    # Ensures it streamed and produced a final string
    assert any(u.get("type") == "planning" or u.get("type") == "synthesizing" for u in updates)
    assert isinstance(final, str)

