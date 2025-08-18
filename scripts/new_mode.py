#!/usr/bin/env python3
import sys
from pathlib import Path

TEMPLATE = """
from typing import Generator, Dict, Any, List, Optional
import ollama

from app.modes.base import BaseMode
from app.core.vector_store import VectorStore, ChromaVectorStore
from app import config as agent_config


class {mode_class}(BaseMode):
    def __init__(self, llm_provider, vector_store):
        super().__init__(llm_provider, vector_store)
        if hasattr(vector_store, "query"):
            self.store: VectorStore = ChromaVectorStore(vector_store)
        else:
            self.store = vector_store

    def run(self, query: str, chat_history: Optional[List[Dict]] = None) -> Generator[Dict[str, Any], None, str]:
        yield {{"type": "planning", "content": "Thinking..."}}
        # TODO: implement search + LLM usage here
        return f"{mode_name} mode is not implemented yet for: {query}"
"""


def main():
    if len(sys.argv) < 2:
        print("Usage: scripts/new_mode.py <mode_name>")
        sys.exit(1)
    mode_name = sys.argv[1]
    mode_class = ''.join(part.capitalize() for part in mode_name.split('_')) + 'Mode'
    mode_upper = mode_name.upper()

    root = Path(__file__).resolve().parents[1]
    modes_dir = root / 'app' / 'modes'
    modes_dir.mkdir(parents=True, exist_ok=True)
    target = modes_dir / f'{mode_name}.py'
    if target.exists():
        print(f"Mode file already exists: {target}")
        sys.exit(1)
    code = TEMPLATE.replace('{mode_class}', mode_class).replace('{mode_upper}', mode_upper).replace('{mode_name}', mode_name)
    target.write_text(code)
    print(f"Created: {target}")
    print("Don't forget to register it in app/modes/registry.py")


if __name__ == '__main__':
    main()


