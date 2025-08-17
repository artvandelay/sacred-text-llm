from app.modes.registry import MODES, get_mode


class DummyLLM:
    def generate_response(self, messages, model):
        return "ok"


class DummyCollection:
    def query(self, **kwargs):
        return {"documents": [["x"]], "metadatas": [[{"source": "s"}]], "distances": [[0.1]]}


def test_modes_registered_and_instantiable():
    assert "deep_research" in MODES
    assert "contemplative" in MODES

    llm = DummyLLM()
    db = DummyCollection()

    for name in MODES.keys():
        mode = get_mode(name, llm, db)
        assert mode is not None

