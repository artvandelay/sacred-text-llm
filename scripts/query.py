import argparse
import textwrap
import re

import ollama

from app.config import (
    EMBEDDING_MODEL, LLM_PROVIDER, OLLAMA_CHAT_MODEL, OPENROUTER_CHAT_MODEL
)
from app.core.providers import create_provider
from app.core.vector_store import get_vector_store


def build_prompt(question: str, context: str) -> str:
    return textwrap.dedent(
        f"""
        You are a helpful research assistant drawing upon a corpus of sacred, philosophical, and spiritual texts.
        Use only the provided CONTEXT to answer the QUESTION. If the answer is not in the context, say you don't know.

        Provide a concise, faithful answer. Include short quotes when directly relevant.

        QUESTION:
        {question}

        CONTEXT:
        {context}
        """
    ).strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("question", type=str, help="User question to query the corpus")
    parser.add_argument("--k", type=int, default=5, help="Number of passages to retrieve")
    args = parser.parse_args()

    store = get_vector_store()
    q_embed = ollama.embeddings(model=EMBEDDING_MODEL, prompt=args.question)["embedding"]
    
    # Query using the abstraction
    search_results = store.query_embeddings([q_embed], k=args.k)
    if not search_results:
        print("No results found.")
        return
    
    # Extract from SearchResult 
    result = search_results[0]
    docs = result.documents
    metas = result.metadatas

    context_blocks = []
    for doc, meta in zip(docs, metas):
        source = meta.get("source_path", "unknown") if isinstance(meta, dict) else "unknown"
        context_blocks.append(f"Source: {source}\n{doc}")
    context = "\n\n---\n\n".join(context_blocks)

    prompt = build_prompt(args.question, context)

    # Use modular provider system
    llm_provider = create_provider(LLM_PROVIDER)
    chat_model = OLLAMA_CHAT_MODEL if LLM_PROVIDER == "ollama" else OPENROUTER_CHAT_MODEL
    
    messages = [
        {"role": "system", "content": "Answer using only the provided context."},
        {"role": "user", "content": prompt},
    ]
    
    content = llm_provider.generate_response(messages, chat_model)
    print(content)


if __name__ == "__main__":
    main()


