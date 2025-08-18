#!/usr/bin/env python3
"""
Simple Sacred Texts Chat Interface

A lightweight, interactive chat for basic Q&A with sacred texts.
For advanced research capabilities, use: python agent_chat.py

Usage: python scripts/chat.py
"""

from typing import List, Dict, Any, Optional
import textwrap

import ollama
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown

from app.config import (
    EMBEDDING_MODEL, LLM_PROVIDER, OLLAMA_CHAT_MODEL, OPENROUTER_CHAT_MODEL
)
from app.core.providers import create_provider
from app.core.vector_store import get_vector_store

console = Console()


class SimpleChat:
    """Simple Q&A chat interface with sacred texts."""
    
    def __init__(self):
        self.console = console
        self.store = None
        self.chat_history: List[Dict[str, str]] = []
        self.llm_provider = create_provider(LLM_PROVIDER)
        self.chat_model = OLLAMA_CHAT_MODEL if LLM_PROVIDER == "ollama" else OPENROUTER_CHAT_MODEL

    def initialize(self) -> bool:
        try:
            self.store = get_vector_store()
            count = self.store._collection.count()
            if count == 0:
                self.console.print("[yellow]Warning: Vector store is empty. Ingestion may still be running.[/yellow]")
                return False
            self.console.print(f"[green]✓ Connected to vector store with {count:,} documents[/green]")
            return True
        except Exception as e:
            self.console.print(f"[red]Error initializing: {e}[/red]")
            return False

    def search_texts(self, question: str, k: int = 5) -> tuple[List[str], List[Dict[str, Any]]]:
        try:
            q_embed = ollama.embeddings(model=EMBEDDING_MODEL, prompt=question)["embedding"]
            search_results = self.store.query_embeddings([q_embed], k=k)
            if not search_results:
                return [], []
            result = search_results[0]
            return result.documents, result.metadatas
        except Exception as e:
            self.console.print(f"[red]Search error: {e}[/red]")
            return [], []

    def build_context(self, docs: List[str], metas: List[Dict[str, Any]]) -> str:
        blocks = []
        for doc, meta in zip(docs, metas):
            source = meta.get("source_path", "unknown") if isinstance(meta, dict) else "unknown"
            source = source.replace("sacred_texts_archive/extracted/", "").replace(".txt", "")
            blocks.append(f"**Source:** {source}\n{doc.strip()}")
        return "\n\n---\n\n".join(blocks)

    def build_prompt(self, question: str, context: str) -> str:
        return textwrap.dedent(f"""
        You are a wise spiritual guide with access to sacred texts from many traditions.
        Use ONLY the provided CONTEXT to answer the QUESTION. If the answer is not in the context, say you don't have enough information.

        Guidelines:
        - Provide thoughtful, respectful answers
        - Include short quotes when directly relevant
        - Acknowledge different perspectives when present
        - Be concise but comprehensive
        - If multiple traditions address the topic, mention them

        QUESTION: {question}

        CONTEXT:
        {context}
        """).strip()

    def get_response(self, question: str, k: int = 5) -> Optional[str]:
        try:
            docs, metas = self.search_texts(question, k)
            if not docs:
                return "I couldn't find any relevant passages to answer your question. The database may be empty or still being built."
            context = self.build_context(docs, metas)
            prompt = self.build_prompt(question, context)
            messages = [
                {"role": "system", "content": "You are a wise spiritual guide. Answer using only the provided context from sacred texts."},
                {"role": "user", "content": prompt},
            ]
            return self.llm_provider.generate_response(messages, self.chat_model)
        except Exception as e:
            self.console.print(f"[red]Error getting response: {e}[/red]")
            return None

    def display_welcome(self) -> None:
        provider_info = f"**Current LLM**: {LLM_PROVIDER.title()} ({self.chat_model})"
        welcome_text = f"""
        # Simple Sacred Texts Chat

        Quick Q&A interface for sacred texts. For advanced research, use `python agent_chat.py`

        {provider_info}

        **Available commands:**
        - Type your question naturally
        - `/help` - Show this help
        - `/history` - Show conversation history  
        - `/clear` - Clear conversation history
        - `/quit` or `/exit` - Exit the chat

        **Examples:**
        - "What is the meaning of compassion?"
        - "How do different traditions view suffering?"
        - "What teachings exist about forgiveness?"
        """
        self.console.print(Panel(Markdown(welcome_text), title="Simple Chat", border_style="blue"))

    def display_sources(self, metas: List[Dict[str, Any]]) -> None:
        if not metas:
            return
        sources = []
        for meta in metas:
            if isinstance(meta, dict):
                source = meta.get("source_path", "unknown").replace("sacred_texts_archive/extracted/", "").replace(".txt", "")
                sources.append(source)
        unique_sources = list(dict.fromkeys(sources))
        if unique_sources:
            sources_text = "**Sources consulted:** " + ", ".join(unique_sources[:3])
            if len(unique_sources) > 3:
                sources_text += f" (+{len(unique_sources)-3} more)"
            self.console.print(f"[dim]{sources_text}[/dim]")

    def run(self) -> None:
        if not self.initialize():
            return
        self.display_welcome()
        while True:
            try:
                question = Prompt.ask("\n[bold cyan]Ask a question[/bold cyan]", default="").strip()
                if not question:
                    continue
                if question.startswith('/'):
                    if question in ['/quit', '/exit']:
                        self.console.print("[yellow]Goodbye! May wisdom guide your path.[/yellow]")
                        break
                    elif question == '/help':
                        self.display_welcome()
                        continue
                    elif question == '/history':
                        if not self.chat_history:
                            self.console.print("[dim]No conversation history yet.[/dim]")
                        else:
                            for i, entry in enumerate(self.chat_history, 1):
                                self.console.print(f"\n[bold]{i}. Q:[/bold] {entry['question']}")
                                self.console.print(f"[bold]A:[/bold] {entry['answer'][:200]}...")
                        continue
                    elif question == '/clear':
                        self.chat_history.clear()
                        self.console.print("[green]Conversation history cleared.[/green]")
                        continue
                    else:
                        self.console.print("[red]Unknown command. Type /help for available commands.[/red]")
                        continue
                self.console.print("[dim]Searching sacred texts...[/dim]")
                docs, metas = self.search_texts(question, k=5)
                response = self.get_response(question, k=5)
                if response:
                    self.console.print(f"\n[bold green]Response:[/bold green]")
                    self.console.print(Panel(response, border_style="green"))
                    self.display_sources(metas)
                    self.chat_history.append({"question": question, "answer": response})
                else:
                    self.console.print("[red]Sorry, I couldn't generate a response. Please try again.[/red]")
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Chat interrupted. Goodbye![/yellow]")
                break
            except Exception as e:
                self.console.print(f"[red]Unexpected error: {e}[/red]")


def main() -> None:
    chat = SimpleChat()
    chat.run()


if __name__ == "__main__":
    main()


