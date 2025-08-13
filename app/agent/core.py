#!/usr/bin/env python3
"""
Core agent implementation extracted from root agent_chat.py
"""

import os
import time
import concurrent.futures
from typing import List, Dict, Any

import chromadb
import ollama
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown

from app.agent import config as config
from app.agent.state import AgentState, AgentStep, SearchResult, parse_json_response
from app.agent.ui import AgentProgressUI, SimpleProgressUI
from app.providers import create_provider


console = Console()


class SacredTextsAgent:
    """
    Agentic Sacred Texts Chat with iterative planning, parallel search, and reflection
    """

    def __init__(self):
        self.console = console
        self.client = None
        self.collection = None
        self.chat_history: List[Dict[str, str]] = []

        # Initialize LLM provider
        self.llm_provider = create_provider(config.LLM_PROVIDER)
        self.chat_model = (
            config.OLLAMA_CHAT_MODEL if config.LLM_PROVIDER == "ollama" else config.OPENROUTER_CHAT_MODEL
        )

        # Progress UI - choose based on terminal capabilities
        try:
            self.progress_ui = AgentProgressUI(console)
        except Exception:
            self.progress_ui = SimpleProgressUI(console)

    def initialize(self) -> bool:
        """Initialize the vector database connection"""
        try:
            if not os.path.exists(config.VECTOR_STORE_DIR):
                self.console.print("[red]Error: Vector store not found. Please run ingestion first.[/red]")
                return False

            self.client = chromadb.PersistentClient(path=config.VECTOR_STORE_DIR)
            self.collection = self.client.get_or_create_collection(
                name=config.COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
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

    def search_texts(self, query: str, k: int = None) -> SearchResult:
        """Search for relevant passages and return SearchResult"""
        k = k or config.DEFAULT_SEARCH_K

        try:
            # Get embedding for the query
            q_embed = ollama.embeddings(model=config.EMBEDDING_MODEL, prompt=query)["embedding"]

            # Search the collection
            results = self.collection.query(
                query_embeddings=[q_embed], n_results=k, include=["documents", "metadatas", "distances"]
            )

            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]

            return SearchResult(query=query, documents=docs, metadatas=metas, distances=distances)

        except Exception as e:
            self.console.print(f"[red]Search error: {e}[/red]")
            return SearchResult(query=query, documents=[], metadatas=[], distances=[])

    def search_parallel(self, queries: List[str], k: int = None) -> List[SearchResult]:
        """Execute multiple searches in parallel"""
        if len(queries) == 1:
            return [self.search_texts(queries[0], k)]

        # Use ThreadPoolExecutor for parallel searches
        with concurrent.futures.ThreadPoolExecutor(max_workers=config.MAX_PARALLEL_QUERIES) as executor:
            future_to_query = {executor.submit(self.search_texts, query, k): query for query in queries}

            results: List[SearchResult] = []
            for future in concurrent.futures.as_completed(future_to_query):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    query = future_to_query[future]
                    self.console.print(f"[red]Error searching '{query}': {e}[/red]")
                    results.append(SearchResult(query=query, documents=[], metadatas=[], distances=[]))

        # Sort by original query order
        query_order = {query: i for i, query in enumerate(queries)}
        results.sort(key=lambda r: query_order.get(r.query, 999))
        return results

    def plan_search_strategy(self, state: AgentState) -> Dict[str, Any]:
        """LLM plans what to search for next"""
        current_evidence = state.get_evidence_summary()
        search_history = state.get_search_history()
        planning_prompt = f"""
You are a research assistant planning searches through sacred texts to answer a spiritual question.

QUESTION: {state.original_question}

CURRENT EVIDENCE: 
{current_evidence if current_evidence != "No evidence collected yet." else "None collected yet."}

PREVIOUS SEARCH QUERIES:
{chr(10).join(f"- {q}" for q in search_history) if search_history else "None yet."}

Your task: Plan the next search strategy. Consider:
1. What aspects of the question are still unclear or need more evidence?
2. What specific terms, concepts, or traditions should we search for?
3. Should we search broadly or focus on specific aspects?

If we already have sufficient evidence to answer the question well, set needs_search to false.

Respond in JSON format:
{{
    "needs_search": boolean,
    "reasoning": "Why we need more searches or why current evidence is sufficient",
    "search_queries": ["query1", "query2", "query3"],
    "search_focus": "What these searches aim to find",
    "confidence_estimate": 0.0-1.0
}}

Generate 1-{config.MAX_PARALLEL_QUERIES} diverse search queries if needed.
"""
        try:
            response = self.llm_provider.generate_response(
                [
                    {
                        "role": "system",
                        "content": "You are a strategic research planner for sacred texts. Be precise and thoughtful.",
                    },
                    {"role": "user", "content": planning_prompt},
                ],
                self.chat_model,
            )
            fallback = {
                "needs_search": True,
                "reasoning": "Planning failed, defaulting to basic search",
                "search_queries": [state.original_question],
                "search_focus": "Basic search for the original question",
                "confidence_estimate": 0.3,
            }
            return parse_json_response(response, fallback)
        except Exception as e:
            self.console.print(f"[red]Planning error: {e}[/red]")
            return {
                "needs_search": True,
                "reasoning": "Planning failed, defaulting to basic search",
                "search_queries": [state.original_question],
                "search_focus": "Basic search for the original question",
                "confidence_estimate": 0.3,
            }

    def reflect_on_evidence(self, state: AgentState) -> Dict[str, Any]:
        """LLM evaluates current evidence sufficiency"""
        evidence_summary = state.get_evidence_summary()
        reflection_prompt = f"""
You are evaluating evidence collected to answer a spiritual question.

QUESTION: {state.original_question}

EVIDENCE COLLECTED:
{evidence_summary}

SEARCH QUERIES USED:
{chr(10).join(f"- {q}" for q in state.get_search_history())}

Evaluate the evidence:
1. How confident are you that this evidence can answer the question? (0.0 = no confidence, 1.0 = very confident)
2. What gaps exist in the evidence?
3. Are there important perspectives or traditions missing?
4. Should we search for more information?

Respond in JSON format:
{{
    "confidence": 0.0-1.0,
    "evidence_quality": "excellent|good|fair|poor",
    "gaps_identified": ["gap1", "gap2"],
    "needs_more_search": boolean,
    "reasoning": "Detailed reasoning for your assessment",
    "coverage_assessment": "What the evidence covers well and what it misses"
}}
"""
        try:
            response = self.llm_provider.generate_response(
                [
                    {
                        "role": "system",
                        "content": "You are an evidence evaluator for spiritual research. Be honest about gaps and limitations.",
                    },
                    {"role": "user", "content": reflection_prompt},
                ],
                self.chat_model,
            )
            fallback = {
                "confidence": 0.5,
                "evidence_quality": "fair",
                "gaps_identified": ["Unknown gaps due to reflection failure"],
                "needs_more_search": True,
                "reasoning": "Reflection failed, being conservative",
                "coverage_assessment": "Cannot assess due to reflection failure",
            }
            return parse_json_response(response, fallback)
        except Exception:
            return {
                "confidence": 0.5,
                "evidence_quality": "fair",
                "gaps_identified": ["Unknown gaps due to reflection failure"],
                "needs_more_search": True,
                "reasoning": "Reflection failed, being conservative",
                "coverage_assessment": "Cannot assess due to reflection failure",
            }

    def generate_final_response(self, state: AgentState) -> str:
        """Generate the final response using all collected evidence"""
        evidence_summary = state.get_evidence_summary()
        response_prompt = f"""
You are a wise spiritual guide with access to sacred texts from many traditions.
Use the provided EVIDENCE to answer the QUESTION comprehensively and thoughtfully.

QUESTION: {state.original_question}

EVIDENCE FROM SACRED TEXTS:
{evidence_summary}

Guidelines for your response:
1. Provide a thoughtful, well-structured answer
2. Include relevant quotes when they directly support your points
3. Acknowledge different perspectives if present in the evidence
4. Be respectful of all spiritual traditions
5. If multiple traditions address the topic, synthesize their wisdom
6. Be honest about any limitations in the evidence
7. Structure your response clearly with main points

Generate a comprehensive response that draws wisdom from the sacred texts provided.
"""
        try:
            response = self.llm_provider.generate_response(
                [
                    {
                        "role": "system",
                        "content": "You are a wise spiritual guide. Synthesize wisdom from sacred texts thoughtfully and respectfully.",
                    },
                    {"role": "user", "content": response_prompt},
                ],
                self.chat_model,
            )
            return response
        except Exception as e:
            return f"I apologize, but I encountered an error generating the response: {e}"

    def run(self) -> None:
        """
        Interactive chat loop for the Sacred Texts Agent
        """
        self.console.print(Panel.fit("🕉️ Sacred Texts Agent", style="bold cyan"))
        self.console.print("Ask questions about spiritual wisdom from sacred texts across traditions.")
        
        # Show which model is being used
        provider = config.LLM_PROVIDER
        model = self.chat_model
        self.console.print(f"[dim]Using {provider} with model: {model}[/dim]")
        self.console.print("[dim]Type 'quit', 'exit', or press Ctrl+C to stop.[/dim]\n")

        # Initialize the agent
        if not self.initialize():
            self.console.print("[red]Failed to initialize. Please check your setup.[/red]")
            return

        try:
            while True:
                # Get user question
                question = Prompt.ask("\n[bold cyan]Your question[/bold cyan]").strip()
                
                if not question:
                    continue
                    
                if question.lower() in ['quit', 'exit', 'q']:
                    self.console.print("[dim]Goodbye! 🙏[/dim]")
                    break
                
                # Get agent response
                try:
                    response = self.agent_response(question)
                    
                    # Display response
                    self.console.print("\n" + "="*60)
                    self.console.print(Panel(
                        Markdown(response),
                        title="🤖 Sacred Texts Agent Response",
                        border_style="green"
                    ))
                    
                    # Add to chat history
                    self.chat_history.append({"role": "user", "content": question})
                    self.chat_history.append({"role": "assistant", "content": response})
                    
                except KeyboardInterrupt:
                    self.console.print("\n[yellow]Response generation interrupted.[/yellow]")
                    continue
                except Exception as e:
                    self.console.print(f"\n[red]Error generating response: {e}[/red]")
                    continue
                    
        except KeyboardInterrupt:
            self.console.print("\n[dim]Goodbye! 🙏[/dim]")

    def agent_response(self, question: str) -> str:
        """
        Main agentic response loop:
        Plan → Search (parallel) → Reflect → Decide → Repeat or Respond
        """
        state = AgentState(
            original_question=question,
            max_iterations=config.MAX_ITERATIONS_PER_QUERY,
            confidence_threshold=config.CONFIDENCE_THRESHOLD,
            max_parallel_queries=config.MAX_PARALLEL_QUERIES,
        )

        # Start progress tracking
        self.progress_ui.start_session(question)
        try:
            for iteration in range(state.max_iterations):
                state.current_iteration = iteration
                current_iter = state.start_iteration()

                # Planning
                state.set_step(AgentStep.PLANNING)
                self.progress_ui.update_step(AgentStep.PLANNING, f"Planning iteration {iteration + 1}")
                plan = self.plan_search_strategy(state)
                current_iter.plan = plan
                self.progress_ui.complete_step(
                    AgentStep.PLANNING,
                    plan.get("reasoning", "Strategy planned"),
                    [f"Focus: {plan.get('search_focus', 'General search')}"]
                )

                if not plan.get("needs_search", True):
                    state.complete(self.generate_final_response(state), "sufficient_evidence", plan.get("confidence_estimate", 0.8))
                    break

                # Searching
                search_queries = plan.get("search_queries", [state.original_question])
                search_queries = search_queries[: config.MAX_PARALLEL_QUERIES]
                state.set_step(AgentStep.SEARCHING)
                self.progress_ui.show_parallel_searches(search_queries)
                search_results = self.search_parallel(search_queries)
                for result in search_results:
                    state.add_search_result(result)
                total_docs_found = sum(len(r.documents) for r in search_results)
                self.progress_ui.complete_step(
                    AgentStep.SEARCHING,
                    f"Found {total_docs_found} relevant passages",
                    [f"Query: {r.query} → {len(r.documents)} results" for r in search_results],
                )

                # Reflection
                state.set_step(AgentStep.REFLECTING)
                self.progress_ui.update_step(AgentStep.REFLECTING, "Evaluating evidence sufficiency")
                reflection = self.reflect_on_evidence(state)
                current_iter.reflection = reflection
                current_iter.confidence = reflection.get("confidence", 0.0)
                confidence = reflection.get("confidence", 0.0)
                evidence_count = len(state.all_evidence)
                self.progress_ui.show_evidence_evaluation(confidence, evidence_count)
                self.progress_ui.complete_step(
                    AgentStep.REFLECTING,
                    f"Confidence: {confidence:.1%}",
                    [
                        f"Quality: {reflection.get('evidence_quality', 'unknown')}",
                        f"Gaps: {', '.join(reflection.get('gaps_identified', []))}",
                    ],
                )

                # Decision
                if confidence >= state.confidence_threshold:
                    state.complete(self.generate_final_response(state), "confidence_threshold", confidence)
                    break
                if not reflection.get("needs_more_search", True):
                    state.complete(self.generate_final_response(state), "no_more_search_needed", confidence)
                    break
                if len(state.all_evidence) >= config.MAX_TOTAL_EVIDENCE_CHUNKS:
                    state.complete(self.generate_final_response(state), "max_evidence_reached", confidence)
                    break

            if not state.is_complete:
                state.complete(
                    self.generate_final_response(state),
                    "max_iterations",
                    current_iter.confidence if current_iter else 0.0,
                )

            if not state.final_response:
                state.set_step(AgentStep.GENERATING)
                self.progress_ui.update_step(AgentStep.GENERATING, "Synthesizing final response")
                state.final_response = self.generate_final_response(state)

            self.progress_ui.finish_session(state.final_response, state)
            return state.final_response

        except Exception as e:
            error_msg = f"Agent encountered an error: {e}"
            self.progress_ui.show_error(error_msg)
            return f"I apologize, but I encountered an error while processing your question: {e}"


