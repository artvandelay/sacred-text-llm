"""
Agent Progress UI for Sacred Texts LLM Agent
Displays collapsible progress like Cursor/Perplexity/ChatGPT
"""

import time
import threading
from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.text import Text
from rich.tree import Tree
from rich.live import Live
from rich.layout import Layout
from rich.align import Align

from app.agent.state import AgentState, AgentStep, AgentIteration
from app.agent import config


class AgentProgressUI:
    """
    Progress display for the agent's thinking process
    Shows current step, completed steps, and can collapse/expand
    """
    
    def __init__(self, console: Console):
        self.console = console
        self.live = None
        self.layout = Layout()
        self.current_panel = None
        self.completed_steps = []
        self.show_progress = config.SHOW_AGENT_PROGRESS
        
    def start_session(self, question: str):
        """Start a new agent session with progress tracking"""
        if not self.show_progress:
            return
            
        self.completed_steps = []
        
        # Create initial layout
        header = Panel(
            f"🤖 Thinking about: [bold cyan]{question}[/bold cyan]",
            title="Sacred Texts Agent",
            border_style="blue"
        )
        
        self.layout.split_column(
            Layout(header, name="header", size=3),
            Layout(Panel("Starting...", title="Current Step"), name="current"),
            Layout(name="completed", size=0)  # Hidden initially
        )
        
        # Start live display
        self.live = Live(self.layout, console=self.console, refresh_per_second=4)
        self.live.start()
    
    def update_step(self, step: AgentStep, details: str = "", progress: Optional[float] = None):
        """Update the current step display"""
        if not self.show_progress or not self.live:
            return
        
        # Step icons and colors
        step_info = {
            AgentStep.PLANNING: ("🧠", "Planning search strategy", "yellow"),
            AgentStep.SEARCHING: ("🔍", "Searching sacred texts", "blue"),  
            AgentStep.REFLECTING: ("🤔", "Evaluating evidence", "magenta"),
            AgentStep.GENERATING: ("✍️", "Generating response", "green"),
            AgentStep.COMPLETE: ("✅", "Complete", "green")
        }
        
        icon, default_text, color = step_info.get(step, ("⚙️", "Processing", "white"))
        display_text = details or default_text
        
        # Create current step panel
        if progress is not None:
            # Show progress bar if provided
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=None  # Don't auto-render
            ) as prog:
                task = prog.add_task(display_text, total=100)
                prog.update(task, completed=progress * 100)
                current_panel = Panel(
                    prog,
                    title=f"{icon} {step.value.title()}",
                    border_style=color
                )
        else:
            # Show spinner
            current_panel = Panel(
                f"[{color}]{icon} {display_text}[/{color}]",
                title=f"{step.value.title()}",
                border_style=color
            )
        
        self.layout["current"].update(current_panel)
    
    def complete_step(self, step: AgentStep, summary: str, details: List[str] = None):
        """Mark a step as completed and add to completed steps"""
        if not self.show_progress or not self.live:
            return
        
        # Add to completed steps
        step_info = {
            AgentStep.PLANNING: "🧠",
            AgentStep.SEARCHING: "🔍", 
            AgentStep.REFLECTING: "🤔",
            AgentStep.GENERATING: "✍️",
        }
        
        icon = step_info.get(step, "✅")
        
        completed_step = {
            "icon": icon,
            "title": step.value.title(),
            "summary": summary,
            "details": details or []
        }
        
        self.completed_steps.append(completed_step)
        
        # Update completed steps display
        if config.COLLAPSE_COMPLETED_STEPS and len(self.completed_steps) > 0:
            self._update_completed_steps_display()
    
    def show_parallel_searches(self, queries: List[str]):
        """Show multiple search queries running in parallel"""
        if not self.show_progress or not self.live:
            return
            
        if not config.SHOW_SEARCH_QUERIES:
            self.update_step(AgentStep.SEARCHING, f"Running {len(queries)} searches in parallel")
            return
        
        # Create tree of search queries
        tree = Tree("🔍 Parallel Searches")
        for i, query in enumerate(queries, 1):
            tree.add(f"[cyan]Query {i}:[/cyan] {query[:60]}{'...' if len(query) > 60 else ''}")
        
        current_panel = Panel(
            tree,
            title="Searching Sacred Texts",
            border_style="blue"
        )
        
        self.layout["current"].update(current_panel)
    
    def show_evidence_evaluation(self, confidence: float, evidence_count: int):
        """Show confidence and evidence evaluation"""
        if not self.show_progress or not self.live:
            return
            
        if not config.SHOW_CONFIDENCE_SCORES:
            self.update_step(AgentStep.REFLECTING, f"Evaluating {evidence_count} pieces of evidence")
            return
        
        # Confidence bar
        conf_color = "green" if confidence >= 0.7 else "yellow" if confidence >= 0.5 else "red"
        conf_bar = "█" * int(confidence * 20) + "░" * (20 - int(confidence * 20))
        
        content = f"""
[bold]Evidence Evaluation:[/bold]
📊 Confidence: [{conf_color}]{conf_bar}[/{conf_color}] {confidence:.1%}
📚 Evidence pieces: {evidence_count}
        """.strip()
        
        current_panel = Panel(
            content,
            title="🤔 Reflecting on Evidence", 
            border_style="magenta"
        )
        
        self.layout["current"].update(current_panel)
    
    def _update_completed_steps_display(self):
        """Update the collapsed completed steps display"""
        if not self.completed_steps:
            self.layout["completed"].size = 0
            return
        
        # Create summary of completed steps
        step_summaries = []
        for step in self.completed_steps:
            step_summaries.append(f"{step['icon']} {step['title']}: {step['summary']}")
        
        completed_text = "\n".join(step_summaries)
        completed_panel = Panel(
            completed_text,
            title=f"✅ Completed ({len(self.completed_steps)} steps)",
            border_style="dim",
            expand=False
        )
        
        self.layout["completed"].update(completed_panel)
        self.layout["completed"].size = len(self.completed_steps) + 2  # +2 for borders
    
    def finish_session(self, final_response: str, agent_state: AgentState):
        """Complete the session and show final summary"""
        if not self.show_progress or not self.live:
            return
        
        # Mark as complete
        self.update_step(AgentStep.COMPLETE, "Response generated")
        
        # Show brief summary if configured
        if config.COLLAPSE_COMPLETED_STEPS:
            summary = f"""
✅ [green]Complete in {agent_state.current_iteration} iterations[/green]
📊 Confidence: {agent_state.final_confidence:.1%}
🔍 Searched {len(agent_state.all_search_queries)} queries
📚 Found {len(agent_state.all_evidence)} relevant passages
⏱️  Duration: {time.time() - agent_state.session_start_time:.1f}s
            """.strip()
            
            final_panel = Panel(
                summary,
                title="🎯 Agent Summary",
                border_style="green"
            )
            
            self.layout["current"].update(final_panel)
            
            # Brief pause to show completion
            time.sleep(1.0)
        
        # Stop the live display
        self.stop()
    
    def stop(self):
        """Stop the live progress display"""
        if self.live:
            self.live.stop()
            self.live = None
    
    def show_error(self, error_msg: str):
        """Show error state"""
        if not self.show_progress or not self.live:
            return
            
        error_panel = Panel(
            f"[red]❌ Error: {error_msg}[/red]",
            title="Agent Error",
            border_style="red"
        )
        
        self.layout["current"].update(error_panel)
        time.sleep(2.0)  # Show error briefly
        self.stop()

    def show_query_decomposition(self, iteration: int, original_question: str, generated_queries: List[str], reasoning: str):
        """Show the query decomposition step in detailed progress mode"""
        if not config.SHOW_DETAILED_PROGRESS or not self.show_progress:
            return
            
        self.console.print(Panel.fit(
            f"[bold blue]🎯 Query Decomposition (Iteration {iteration + 1})[/bold blue]\n\n"
            f"[dim]Original Question:[/dim] {original_question}\n\n"
            f"[dim]Strategy:[/dim] {reasoning}\n\n"
            f"[dim]Generated Queries ({len(generated_queries)}):[/dim]\n" + 
            "\n".join(f"  {i+1}. {query}" for i, query in enumerate(generated_queries)),
            title="🧠 Planning",
            border_style="blue"
        ))
    
    def show_insight_synthesis(self, iteration: int, search_results: List, insight_preview: str):
        """Show the insight synthesis step in detailed progress mode"""
        if not config.SHOW_DETAILED_PROGRESS or not self.show_progress:
            return
            
        passages_count = sum(len(getattr(result, 'documents', [])) for result in search_results)
        
        self.console.print(Panel.fit(
            f"[bold green]🔬 Insight Synthesis (Iteration {iteration + 1})[/bold green]\n\n"
            f"[dim]Synthesizing {passages_count} passages from {len(search_results)} queries[/dim]\n\n"
            f"[dim]Preview:[/dim]\n{insight_preview}",
            title="🧪 Synthesis", 
            border_style="green"
        ))


class SimpleProgressUI:
    """
    Simple progress display for when rich UI is disabled
    Just prints status messages
    """
    
    def __init__(self, console: Console):
        self.console = console
        
    def start_session(self, question: str):
        self.console.print(f"[dim]🤖 Thinking about: {question}[/dim]")
    
    def update_step(self, step: AgentStep, details: str = "", progress: Optional[float] = None):
        if config.SHOW_AGENT_PROGRESS:
            icon = {"planning": "🧠", "searching": "🔍", "reflecting": "🤔", "generating": "✍️"}.get(step.value, "⚙️")
            self.console.print(f"[dim]{icon} {details or step.value.title()}...[/dim]")
    
    def complete_step(self, step: AgentStep, summary: str, details: List[str] = None):
        pass  # Don't clutter simple output
    
    def show_parallel_searches(self, queries: List[str]):
        if config.SHOW_SEARCH_QUERIES:
            self.console.print(f"[dim]🔍 Searching {len(queries)} parallel queries...[/dim]")
    
    def show_evidence_evaluation(self, confidence: float, evidence_count: int):
        if config.SHOW_CONFIDENCE_SCORES:
            self.console.print(f"[dim]🤔 Confidence: {confidence:.1%} with {evidence_count} pieces of evidence[/dim]")
    
    def finish_session(self, final_response: str, agent_state: AgentState):
        if config.SHOW_AGENT_PROGRESS:
            self.console.print(f"[dim]✅ Complete in {agent_state.current_iteration} iterations[/dim]")
    
    def stop(self):
        pass
    
    def show_query_decomposition(self, iteration: int, original_question: str, generated_queries: List[str], reasoning: str):
        """Show the query decomposition step in detailed progress mode"""
        if not config.SHOW_DETAILED_PROGRESS:
            return
            
        self.console.print(Panel.fit(
            f"[bold blue]🎯 Query Decomposition (Iteration {iteration + 1})[/bold blue]\n\n"
            f"[dim]Original Question:[/dim] {original_question}\n\n"
            f"[dim]Strategy:[/dim] {reasoning}\n\n"
            f"[dim]Generated Queries ({len(generated_queries)}):[/dim]\n" + 
            "\n".join(f"  {i+1}. {query}" for i, query in enumerate(generated_queries)),
            title="🧠 Planning",
            border_style="blue"
        ))
    
    def show_insight_synthesis(self, iteration: int, search_results: List, insight_preview: str):
        """Show the insight synthesis step in detailed progress mode"""
        if not config.SHOW_DETAILED_PROGRESS:
            return
            
        passages_count = sum(len(getattr(result, 'documents', [])) for result in search_results)
        
        self.console.print(Panel.fit(
            f"[bold green]🔬 Insight Synthesis (Iteration {iteration + 1})[/bold green]\n\n"
            f"[dim]Synthesizing {passages_count} passages from {len(search_results)} queries[/dim]\n\n"
            f"[dim]Preview:[/dim]\n{insight_preview}",
            title="🧪 Synthesis", 
            border_style="green"
        ))

    def show_error(self, error_msg: str):
        self.console.print(f"[red]❌ Agent error: {error_msg}[/red]")
