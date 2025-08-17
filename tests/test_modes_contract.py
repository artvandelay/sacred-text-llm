import types
from typing import Dict, Any

from app.modes.base import BaseMode


class DummyMode(BaseMode):
    def run(self, query: str, chat_history=None):
        # yield two updates, then return final
        yield {"type": "planning", "content": "ok"}
        yield {"type": "searching", "content": "ok"}
        return "final"


def test_mode_generator_contract():
    mode = DummyMode(llm_provider=None, vector_store=None)
    gen = mode.run("q")

    assert isinstance(gen, types.GeneratorType)

    updates = []
    try:
        while True:
            try:
                update = next(gen)
                assert isinstance(update, dict)
                assert "type" in update
                updates.append(update)
            except StopIteration as e:
                final = e.value
                break
    except Exception as e:
        raise AssertionError(f"Generator errored: {e}")

    # Should have streamed at least one update and a final string
    assert len(updates) >= 1
    assert isinstance(final, str)

