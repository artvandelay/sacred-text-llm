#!/usr/bin/env python3
"""
Interactive chat interface for Sacred Texts LLM
Provides a conversational interface to query wisdom from sacred texts
"""

import os
import sys
import textwrap
import re
from typing import List, Dict, Any, Optional

import chromadb
import ollama
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich.markdown import Markdown

from config import (
    EMBEDDING_MODEL, VECTOR_STORE_DIR, COLLECTION_NAME,
    LLM_PROVIDER, OLLAMA_CHAT_MODEL, OPENROUTER_CHAT_MODEL
)
from providers import create_provider

console = Console()

class SacredTextsChat:
    def __init__(self):
        self.console = console
        self.client = None
        self.collection = None
        self.chat_history: List[Dict[str, str]] = []
        
        # Initialize the LLM provider (Ollama or OpenRouter)
        self.llm_provider = create_provider(LLM_PROVIDER)
        self.chat_model = OLLAMA_CHAT_MODEL if LLM_PROVIDER == "ollama" else OPENROUTER_CHAT_MODEL
        
    def initialize(self) -> bool:
        """Initialize the vector database connection"""
        try:
            if not os.path.exists(VECTOR_STORE_DIR):
                self.console.print("[red]Error: Vector store not found. Please run ingestion first.[/red]")
                return False
                
            self.client = chromadb.PersistentClient(path=VECTOR_STORE_DIR)
            self.collection = self.client.get_or_create_collection(
                name=COLLECTION_NAME, 
                metadata={"hnsw:space": "cosine"}
            )
            
            # Check if collection has any data
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
        """Search for relevant passages"""
        try:
            # Get embedding for the question
            q_embed = ollama.embeddings(model=EMBEDDING_MODEL, prompt=question)["embedding"]
            
            # Search the collection
            results = self.collection.query(
                query_embeddings=[q_embed], 
                n_results=k,
                include=["documents", "metadatas", "distances"]
            )
            
            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]
            
            return docs, metas
            
        except Exception as e:
            self.console.print(f"[red]Search error: {e}[/red]")
            return [], []
    
    def build_context(self, docs: List[str], metas: List[Dict[str, Any]]) -> str:
        """Build context from retrieved documents"""
        context_blocks = []
        
        for doc, meta in zip(docs, metas):
            source = meta.get("source_path", "unknown") if isinstance(meta, dict) else "unknown"
            # Clean up source path for display
            source = source.replace("sacred_texts_archive/extracted/", "").replace(".txt", "")
            
            # Add some metadata if available
            strategy = meta.get("strategy", "") if isinstance(meta, dict) else ""
            char_count = meta.get("char_count", 0) if isinstance(meta, dict) else 0
            
            context_blocks.append(f"**Source:** {source}\n{doc.strip()}")
        
        return "\n\n---\n\n".join(context_blocks)
    
    def build_prompt(self, question: str, context: str) -> str:
        """Build the prompt for the LLM"""
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
        """Get AI response to a question"""
        try:
            # Search for relevant passages
            docs, metas = self.search_texts(question, k)
            
            if not docs:
                return "I couldn't find any relevant passages to answer your question. The database may be empty or still being built."
            
            # Build context and prompt
            context = self.build_context(docs, metas)
            prompt = self.build_prompt(question, context)
            
            # Get response from LLM (Ollama or OpenRouter)
            messages = [
                {"role": "system", "content": "You are a wise spiritual guide. Answer using only the provided context from sacred texts."},
                {"role": "user", "content": prompt},
            ]
            
            # Use the modular provider system
            response = self.llm_provider.generate_response(messages, self.chat_model)
            
            return response
            
        except Exception as e:
            self.console.print(f"[red]Error getting response: {e}[/red]")
            return None
    
    def display_welcome(self):
        """Display welcome message"""
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
    
    def display_sources(self, metas: List[Dict[str, Any]]):
        """Display source information"""
        if not metas:
            return
            
        sources = []
        for meta in metas:
            if isinstance(meta, dict):
                source = meta.get("source_path", "unknown").replace("sacred_texts_archive/extracted/", "").replace(".txt", "")
                sources.append(source)
        
        unique_sources = list(dict.fromkeys(sources))  # Remove duplicates while preserving order
        
        if unique_sources:
            sources_text = "**Sources consulted:** " + ", ".join(unique_sources[:3])
            if len(unique_sources) > 3:
                sources_text += f" (+{len(unique_sources)-3} more)"
            
            self.console.print(f"[dim]{sources_text}[/dim]")
    
    def run(self):
        """Main chat loop"""
        if not self.initialize():
            return
        
        self.display_welcome()
        
        while True:
            try:
                question = Prompt.ask("\n[bold cyan]Ask a question[/bold cyan]", default="").strip()
                
                if not question:
                    continue
                
                # Handle commands
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
                
                # Process the question
                self.console.print("[dim]Searching sacred texts...[/dim]")
                
                # Get sources for display
                docs, metas = self.search_texts(question, k=5)
                
                # Get response
                response = self.get_response(question, k=5)
                
                if response:
                    # Display response
                    self.console.print(f"\n[bold green]Response:[/bold green]")
                    self.console.print(Panel(response, border_style="green"))
                    
                    # Display sources
                    self.display_sources(metas)
                    
                    # Add to history
                    self.chat_history.append({
                        "question": question,
                        "answer": response
                    })
                else:
                    self.console.print("[red]Sorry, I couldn't generate a response. Please try again.[/red]")
                
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Chat interrupted. Goodbye![/yellow]")
                break
            except Exception as e:
                self.console.print(f"[red]Unexpected error: {e}[/red]")


def main():
    """Main entry point"""
    chat = SacredTextsChat()
    chat.run()


if __name__ == "__main__":
    main()
