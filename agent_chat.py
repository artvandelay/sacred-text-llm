#!/usr/bin/env python3
"""
Universal CLI entry point for all modes.

This is a thin dispatcher that:
1. Loads the selected mode
2. Runs queries through it
3. Displays results

Simple, minimal, focused.
"""

import sys
import argparse
import logging
from typing import Dict, Any

import chromadb
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from app.core.providers import create_provider
from app.core.vector_store import ChromaVectorStore
from app.modes.registry import MODES, get_mode, list_modes
from app import config as agent_config


console = Console()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def display_update(update: Dict[str, Any]):
    """Display mode updates in a clean format."""
    update_type = update.get("type", "info")
    
    if update_type == "planning":
        console.print(f"[blue]🤔 {update.get('content', 'Planning...')}[/blue]")
    elif update_type == "searching":
        console.print(f"[green]🔍 {update.get('content', 'Searching...')}[/green]")
    elif update_type == "synthesizing":
        console.print(f"[yellow]✨ {update.get('content', 'Synthesizing...')}[/yellow]")
    elif update_type == "error":
        console.print(f"[red]❌ Error: {update.get('error', 'Unknown error')}[/red]")
    else:
        # Generic update - only show if there's content
        content = update.get('content')
        if content:
            console.print(f"[dim]• {content}[/dim]")


def run_query(mode_name: str, query: str, show_progress: bool = True):
    """Run a single query through the specified mode."""
    # Initialize dependencies
    llm = create_provider(agent_config.LLM_PROVIDER)
    db = chromadb.PersistentClient(path=agent_config.VECTOR_STORE_DIR)
    
    # Get mode instance
    try:
        collection = db.get_or_create_collection(
            name=agent_config.COLLECTION_NAME, 
            metadata={"hnsw:space": "cosine"}
        )
        store = ChromaVectorStore(collection)
        mode = get_mode(mode_name, llm, store)
    except ValueError as e:
        logging.error("Mode selection error: %s", e)
        console.print(f"[red]{e}[/red]")
        return
    
    # Run query
    try:
        generator = mode.run(query)
        
        # Process updates and get final response
        response = None
        try:
            # Manually iterate to catch the return value
            while True:
                try:
                    update = next(generator)
                    if show_progress:
                        display_update(update)
                except StopIteration as e:
                    # This captures the return value from the generator
                    response = e.value
                    break
        except Exception as e:
            console.print(f"[red]Generator error: {e}[/red]")
            response = f"Error during generation: {str(e)}"
        
        if response is None:
            response = "No response generated."
            
    except Exception as e:
        logging.exception("Run query error")
        response = f"Error: {str(e)}"
    
    # Display response
    console.print(f"\n[bold]Response:[/bold]")
    console.print(Panel(response, expand=False))


def interactive_chat(initial_mode: str = "deep_research"):
    """Run interactive chat with mode switching."""
    console.print(Panel.fit("🕉️ Sacred Texts Multi-Mode Chat", style="bold cyan"))
    console.print(f"Current mode: [bold]{initial_mode}[/bold]")
    console.print("[dim]Commands: quit, switch <mode>, list modes[/dim]\n")
    
    current_mode = initial_mode
    
    while True:
        query = Prompt.ask("\n[bold green]Ask a question[/bold green]")
        
        if query.lower() in ["quit", "exit"]:
            break
        elif query.lower() == "list modes":
            console.print("\n[bold]Available modes:[/bold]")
            console.print(list_modes())
        elif query.lower().startswith("switch "):
            new_mode = query[7:].strip()
            if new_mode in MODES:
                current_mode = new_mode
                console.print(f"[green]Switched to {current_mode} mode[/green]")
            else:
                console.print(f"[red]Unknown mode: {new_mode}[/red]")
        else:
            run_query(current_mode, query)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Sacred Texts LLM - Multi-mode spiritual wisdom"
    )
    parser.add_argument("--mode", default="deep_research", help="Mode to use")
    parser.add_argument("--query", help="Direct query (non-interactive)")
    parser.add_argument("--list-modes", action="store_true", help="List available modes")
    
    args = parser.parse_args()
    
    if args.list_modes:
        console.print("[bold]Available modes:[/bold]")
        console.print(list_modes())
    elif args.query:
        run_query(args.mode, args.query)
    else:
        interactive_chat(args.mode)


if __name__ == "__main__":
    main()