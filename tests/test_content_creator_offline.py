import json

from app.modes.content_creator import ContentCreatorMode


class DummyLLM:
    def __init__(self):
        self.calls = 0

    def generate_response(self, messages, model):
        group = self.calls // 3  # each group corresponds to one tradition
        phase = self.calls % 3
        self.calls += 1
        if phase == 0:
            return f"Tweet {group + 1} draft"
        elif phase == 1:
            return json.dumps(
                {
                    "rating": 6,
                    "critique": "needs spice",
                    "improved": f"Tweet {group + 1} improved",
                }
            )
        else:
            return json.dumps(
                {
                    "rating": 9,
                    "critique": "solid",
                    "improved": "",
                }
            )


class DummyCollection:
    def query(self, query_embeddings=None, n_results=3, include=None, **kwargs):
        return {
            "documents": [["Doc1", "Doc2", "Doc3"]],
            "metadatas": [[{"source": "s1"}, {"source": "s2"}, {"source": "s3"}]],
            "distances": [[0.1, 0.2, 0.3]],
        }


def test_content_creator_generates_five(monkeypatch):
    import ollama

    monkeypatch.setattr(
        ollama, "embeddings", lambda model, prompt: {"embedding": [0.0] * 768}
    )

    mode = ContentCreatorMode(DummyLLM(), DummyCollection())
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

    drafts = [u for u in updates if u.get("type") == "tweet_draft"]
    ratings = [u for u in updates if u.get("type") == "rating"]
    revisions = [u for u in updates if u.get("type") == "revised"]

    assert len(drafts) == 5
    assert len(ratings) >= 10
    assert len(revisions) >= 5

    for i in range(1, 6):
        assert f"Tweet {i} improved" in final

