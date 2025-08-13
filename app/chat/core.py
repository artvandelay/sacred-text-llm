#!/usr/bin/env python3
"""
Core chat implementation extracted from root chat.py
"""

from typing import List, Dict, Any, Optional
import os
import textwrap

import chromadb
import ollama
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown

from app.chat.config import (
    EMBEDDING_MODEL, VECTOR_STORE_DIR, COLLECTION_NAME,
    LLM_PROVIDER, OLLAMA_CHAT_MODEL, OPENROUTER_CHAT_MODEL
)
from app.providers import create_provider


console = Console()


class SacredTextsChat:
    def __init__(self):
        self.console = console
        self.client = None
        self.collection = None
        self.chat_history: List[Dict[str, str]] = []
        self.llm_provider = create_provider(LLM_PROVIDER)
        self.chat_model = OLLAMA_CHAT_MODEL if LLM_PROVIDER == "ollama" else OPENROUTER_CHAT_MODEL

    def initialize(self) -> bool:
        try:
            if not os.path.exists(VECTOR_STORE_DIR):
                self.console.print("[red]Error: Vector store not found. Please run ingestion first.[/red]")
                return False
            self.client = chromadb.PersistentClient(path=VECTOR_STORE_DIR)
            self.collection = self.client.get_or_create_collection(
                name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
            )
            count = self.collection.count()
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
            results = self.collection.query(
                query_embeddings=[q_embed], n_results=k, include=["documents", "metadatas", "distances"]
            )
            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]
            return docs, metas
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
        # Sacred Texts Chat Interface

        Ask questions about wisdom, spirituality, philosophy, and meaning from sacred texts across traditions.

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
        self.console.print(Panel(Markdown(welcome_text), title="Welcome", border_style="blue"))

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


