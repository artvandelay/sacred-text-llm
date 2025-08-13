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

    def generate_research_queries(self, state: AgentState, accumulated_insights: List[str] = None) -> Dict[str, Any]:
        """Generate diverse research queries for deep investigation"""
        current_evidence = state.get_evidence_summary()
        search_history = state.get_search_history()
        
        # Build context based on whether we have accumulated insights
        context_section = ""
        if accumulated_insights:
            insights_text = "\n".join(f"- {insight}" for insight in accumulated_insights)
            context_section = f"""
ACCUMULATED INSIGHTS FROM PREVIOUS RESEARCH:
{insights_text}

Based on these insights, generate queries that:
1. Explore concepts, terms, or perspectives mentioned but not fully explained
2. Seek deeper understanding or different viewpoints 
3. Look for practical applications or examples
4. Investigate related traditions or complementary teachings
"""
        else:
            context_section = """
This is the initial research phase. Generate diverse queries that:
1. Explore different aspects and dimensions of the question
2. Look for various traditions and perspectives
3. Seek both theoretical understanding and practical applications
4. Consider historical, mystical, and philosophical angles
"""

        planning_prompt = f"""
You are a deep research assistant investigating sacred texts with scholarly rigor.

ORIGINAL QUESTION: {state.original_question}

CURRENT EVIDENCE SUMMARY: 
{current_evidence if current_evidence != "No evidence collected yet." else "None collected yet."}

PREVIOUS SEARCH QUERIES:
{chr(10).join(f"- {q}" for q in search_history) if search_history else "None yet."}

{context_section}

Your task: Generate {config.MAX_QUERIES_PER_ITERATION} diverse, specific research queries that will provide comprehensive coverage of the topic. Each query should:

- Be specific enough to retrieve relevant passages
- Explore different angles, traditions, or concepts
- Build upon or complement previous research
- Use varied terminology (synonyms, traditional terms, modern concepts)

Respond in JSON format:
{{
    "reasoning": "Your strategic thinking about what areas need investigation and why these specific queries will advance understanding",
    "search_queries": ["query1", "query2", "query3", "query4", "query5"],
    "research_focus": "What these searches collectively aim to accomplish",
    "expected_insights": "What types of insights or understanding you expect these queries to reveal"
}}

Generate exactly {config.MAX_QUERIES_PER_ITERATION} diverse search queries.
"""
        try:
            response = self.llm_provider.generate_response(
                [
                    {
                        "role": "system", 
                        "content": "You are a deep research strategist specializing in sacred texts and spiritual inquiry. Be thorough and scholarly in your approach."
                    },
                    {"role": "user", "content": planning_prompt},
                ],
                self.chat_model,
            )
            fallback = {
                "reasoning": "Query generation failed, using basic search approach",
                "search_queries": [state.original_question],
                "research_focus": "Basic search for the original question",
                "expected_insights": "Direct answers to the question"
            }
            return parse_json_response(response, fallback)
        except Exception as e:
            self.console.print(f"[red]Query generation error: {e}[/red]")
            return fallback

    def summarize_search_batch(self, search_results: List[SearchResult], original_question: str) -> str:
        """Synthesize all retrieved passages from a search iteration into coherent insights"""
        if not search_results:
            return "No search results to summarize."
        
        # Group passages by source and query for better organization
        passages_text = ""
        for i, result in enumerate(search_results, 1):
            passages_text += f"\n--- Search Result {i} (Query: '{result.query}') ---\n"
            # Extract source from first document's metadata if available
            source = "Unknown"
            if result.metadatas and len(result.metadatas) > 0:
                source = result.metadatas[0].get('source', 'Unknown')
            passages_text += f"Source: {source}\n"
            # Use documents content (SearchResult has documents, not content)
            for j, doc in enumerate(result.documents):
                passages_text += f"Content {j+1}: {doc}\n"
        
        synthesis_prompt = f"""
You are a scholar synthesizing retrieved passages from sacred texts to develop deep insights.

ORIGINAL RESEARCH QUESTION: {original_question}

RETRIEVED PASSAGES:
{passages_text}

Your task: Synthesize these passages into coherent, scholarly insights that advance understanding of the research question. Focus on:

1. **Key Concepts & Themes**: What major ideas, principles, or teachings emerge?
2. **Cross-References & Connections**: How do different passages relate to or complement each other?
3. **Deeper Implications**: What profound insights or wisdom can be drawn from these texts?
4. **Practical Applications**: How might these teachings apply to spiritual practice or life?
5. **Areas for Further Investigation**: What questions or concepts mentioned here deserve deeper exploration?

Provide a thoughtful synthesis that:
- Integrates information from multiple passages
- Identifies patterns and recurring themes
- Draws out deeper meaning and significance
- Maintains scholarly rigor while being accessible
- Highlights both convergent and divergent perspectives where present

Write your synthesis as a flowing, comprehensive analysis (not bullet points).
"""
        try:
            response = self.llm_provider.generate_response(
                [
                    {
                        "role": "system",
                        "content": "You are a sacred texts scholar specializing in synthesis and deep textual analysis. Provide thoughtful, nuanced interpretations that honor the wisdom traditions while offering clear insights."
                    },
                    {"role": "user", "content": synthesis_prompt}
                ],
                self.chat_model,
            )
            return response
        except Exception as e:
            self.console.print(f"[red]Synthesis error: {e}[/red]")
            # Fallback to simple concatenation
            simple_summary = f"Retrieved {len(search_results)} passages related to: {original_question}\n\n"
            for result in search_results[:3]:  # Show first 3 for brevity
                simple_summary += f"- {result.content[:200]}...\n"
            return simple_summary

    def reflect_on_evidence(self, state: AgentState, accumulated_insights: List[str] = None, current_iteration: int = 0) -> Dict[str, Any]:
        """Enhanced reflection with depth assessment and accumulated insights consideration"""
        evidence_summary = state.get_evidence_summary()
        search_history = state.get_search_history()
        
        # Build accumulated insights context
        insights_context = ""
        if accumulated_insights:
            insights_text = "\n".join(f"- {insight}" for insight in accumulated_insights)
            insights_context = f"""
ACCUMULATED INSIGHTS FROM RESEARCH:
{insights_text}

"""

        reflection_prompt = f"""
You are evaluating the depth and completeness of research on a spiritual question.

ORIGINAL QUESTION: {state.original_question}

{insights_context}CURRENT EVIDENCE SUMMARY:
{evidence_summary}

SEARCH QUERIES USED:
{chr(10).join(f"- {q}" for q in search_history)}

RESEARCH CONTEXT:
- Current iteration: {current_iteration + 1}
- Maximum iterations allowed: {config.MAX_RESEARCH_ITERATIONS}

Your task: Provide a comprehensive assessment of research completeness and depth. Consider:

1. **Depth Assessment**: How thoroughly has the question been explored?
   - Surface level: Basic definitions and simple answers
   - Moderate depth: Multiple perspectives, some analysis
   - Deep level: Comprehensive understanding, synthesis, practical wisdom
   - Scholarly depth: Nuanced analysis, cross-references, profound insights

2. **Coverage Assessment**: What aspects are well-covered vs. what's missing?

3. **Research Quality**: Are the insights substantive and well-supported?

4. **Termination Decision**: Should research continue or can we provide a comprehensive response?

Respond in JSON format:
{{
    "confidence": 0.0-1.0,
    "evidence_quality": "excellent|good|fair|poor",
    "depth_assessment": "surface|moderate|deep|scholarly",
    "gaps_identified": ["specific gap 1", "specific gap 2"],
    "needs_more_research": boolean,
    "reasoning": "Detailed reasoning for your assessment and decision",
    "coverage_assessment": "What the evidence covers well and what it misses",
    "research_completeness": 0.0-1.0,
    "termination_confidence": 0.0-1.0
}}

Consider that deeper questions may need multiple iterations to achieve scholarly depth, while simpler questions might be adequately answered sooner.
"""
        try:
            response = self.llm_provider.generate_response(
                [
                    {
                        "role": "system",
                        "content": "You are a research depth assessor specializing in spiritual and philosophical inquiry. Balance thoroughness with practical completion. Be honest about limitations while recognizing when sufficient depth has been achieved."
                    },
                    {"role": "user", "content": reflection_prompt},
                ],
                self.chat_model,
            )
            fallback = {
                "confidence": 0.5,
                "evidence_quality": "fair", 
                "depth_assessment": "moderate",
                "gaps_identified": ["Assessment failed - assuming gaps exist"],
                "needs_more_research": current_iteration < 2,  # Conservative default
                "reasoning": "Reflection failed, using conservative assessment",
                "coverage_assessment": "Cannot assess due to reflection failure",
                "research_completeness": 0.5,
                "termination_confidence": 0.3
            }
            return parse_json_response(response, fallback)
        except Exception as e:
            self.console.print(f"[red]Reflection error: {e}[/red]")
            return fallback

    def generate_final_response_from_insights(self, state: AgentState, accumulated_insights: List[str]) -> str:
        """Generate the final response using accumulated insights from deep research"""
        
        # Include recent chat history for context
        chat_context = ""
        if self.chat_history:
            recent_history = self.chat_history[-3:]  # Last 3 exchanges
            chat_context = "RECENT CONVERSATION CONTEXT:\n"
            for exchange in recent_history:
                human_msg = exchange.get('content', '') if exchange.get('role') == 'user' else ''
                assistant_msg = exchange.get('content', '') if exchange.get('role') == 'assistant' else ''
                if human_msg:
                    chat_context += f"Human: {human_msg}\n"
                if assistant_msg:
                    chat_context += f"Assistant: {assistant_msg[:200]}...\n\n"
        
        insights_text = "\n\n".join(f"=== Research Iteration {i+1} ===\n{insight}" 
                                  for i, insight in enumerate(accumulated_insights))
        
        response_prompt = f"""
You are a profound spiritual teacher synthesizing wisdom from extensive research through sacred texts.

{chat_context}CURRENT QUESTION: {state.original_question}

COMPREHENSIVE RESEARCH INSIGHTS:
{insights_text}

Your task: Provide a masterful, comprehensive response that demonstrates the depth of your research. Your response should:

**STRUCTURE & DEPTH:**
1. **Opening**: Acknowledge the depth and complexity of the question
2. **Core Teachings**: Present the fundamental principles and wisdom discovered
3. **Multiple Perspectives**: Weave together insights from different traditions where relevant
4. **Deeper Synthesis**: Show how different teachings complement or contrast with each other
5. **Practical Wisdom**: Offer actionable insights for spiritual practice or life application
6. **Contemplative Closing**: End with profound reflections or questions for further contemplation

**SCHOLARLY APPROACH:**
- Demonstrate mastery by connecting themes across your research
- Include specific references to texts, concepts, or traditions when relevant
- Show nuanced understanding rather than surface-level answers
- Acknowledge complexity and avoid oversimplification
- Honor the wisdom of each tradition while finding universal principles

**TONE & STYLE:**
- Write with the authority of deep study and contemplation
- Be reverent yet accessible
- Use rich, thoughtful language appropriate for spiritual discourse
- Balance scholarly depth with practical wisdom

Your response should feel like the culmination of extensive spiritual scholarship - comprehensive, nuanced, and profoundly insightful.
"""
        
        try:
            response = self.llm_provider.generate_response(
                [
                    {
                        "role": "system",
                        "content": "You are a master spiritual teacher and scholar who has spent extensive time researching sacred texts. Your responses demonstrate profound understanding, synthesis across traditions, and practical wisdom. You write with the depth and authority that comes from genuine spiritual scholarship."
                    },
                    {"role": "user", "content": response_prompt},
                ],
                self.chat_model,
            )
            return response
        except Exception as e:
            self.console.print(f"[red]Final response generation error: {e}[/red]")
            # Fallback to basic response using insights
            fallback_response = f"Based on my research into your question '{state.original_question}', here are the key insights I discovered:\n\n"
            for i, insight in enumerate(accumulated_insights, 1):
                fallback_response += f"**Research Phase {i}:**\n{insight}\n\n"
            return fallback_response

    def generate_final_response(self, state: AgentState) -> str:
        """Legacy method - generate basic final response using evidence (kept for compatibility)"""
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
                try:
                    question = Prompt.ask("\n[bold cyan]Your question[/bold cyan]").strip()
                except EOFError:
                    # Handle piped input gracefully
                    self.console.print("\n[dim]Input stream ended. Goodbye! 🙏[/dim]")
                    break
                
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
        Enhanced iterative research loop:
        Generate Queries → Search (parallel) → Summarize → Reflect → Decide → Repeat or Respond
        """
        state = AgentState(
            original_question=question,
            max_iterations=config.MAX_RESEARCH_ITERATIONS,  # Use research iterations limit
            confidence_threshold=config.CONFIDENCE_THRESHOLD,
            max_parallel_queries=config.MAX_PARALLEL_QUERIES,
        )

        accumulated_insights = []  # Track insights across iterations
        reflection = None  # Initialize reflection for use after loop
        depth_assessment = "moderate"  # Initialize depth assessment
        
        # Start progress tracking
        self.progress_ui.start_session(question)
        
        try:
            for iteration in range(config.MAX_RESEARCH_ITERATIONS):
                state.current_iteration = iteration
                current_iter = state.start_iteration()

                # === QUERY GENERATION ===
                state.set_step(AgentStep.PLANNING)
                self.progress_ui.update_step(AgentStep.PLANNING, f"Generating research queries (iteration {iteration + 1})")
                
                query_plan = self.generate_research_queries(state, accumulated_insights if iteration > 0 else None)
                current_iter.plan = query_plan
                
                # Show detailed query decomposition
                if config.SHOW_DETAILED_PROGRESS:
                    self.progress_ui.show_query_decomposition(
                        iteration,
                        question, 
                        query_plan.get("search_queries", []),
                        query_plan.get("reasoning", "")
                    )
                
                self.progress_ui.complete_step(
                    AgentStep.PLANNING,
                    query_plan.get("reasoning", "Queries generated"),
                    [f"Generated {len(query_plan.get('search_queries', []))} research queries"]
                )

                # === PARALLEL SEARCH ===
                search_queries = query_plan.get("search_queries", [question])
                # Use all generated queries, not limited by parallel processing limit
                # (search_parallel method will handle batching internally if needed)
                
                state.set_step(AgentStep.SEARCHING)
                self.progress_ui.show_parallel_searches(search_queries)
                
                search_results = self.search_parallel(search_queries)
                for result in search_results:
                    state.add_search_result(result)
                
                total_docs_found = sum(len(r.documents) for r in search_results)
                self.progress_ui.complete_step(
                    AgentStep.SEARCHING,
                    f"Found {total_docs_found} relevant passages across {len(search_queries)} queries",
                    [f"Query: {r.query} → {len(r.documents)} results" for r in search_results],
                )

                # === BATCH SUMMARIZATION ===
                state.set_step(AgentStep.REFLECTING)
                self.progress_ui.update_step(AgentStep.REFLECTING, "Synthesizing retrieved passages")
                
                # Synthesize all search results from this iteration into coherent insights
                iteration_insight = self.summarize_search_batch(search_results, question)
                accumulated_insights.append(iteration_insight)
                
                # Show detailed insight synthesis
                if config.SHOW_DETAILED_PROGRESS:
                    insight_preview = iteration_insight[:200] + "..." if len(iteration_insight) > 200 else iteration_insight
                    self.progress_ui.show_insight_synthesis(iteration, search_results, insight_preview)

                # === ENHANCED REFLECTION ===
                self.progress_ui.update_step(AgentStep.REFLECTING, "Assessing research depth and completeness")
                
                reflection = self.reflect_on_evidence(state, accumulated_insights, iteration)
                current_iter.reflection = reflection
                current_iter.confidence = reflection.get("confidence", 0.0)
                
                confidence = reflection.get("confidence", 0.0)
                depth_assessment = reflection.get("depth_assessment", "moderate")
                research_completeness = reflection.get("research_completeness", 0.5)
                
                self.progress_ui.show_evidence_evaluation(confidence, len(state.all_evidence))
                self.progress_ui.complete_step(
                    AgentStep.REFLECTING,
                    f"Depth: {depth_assessment} | Completeness: {research_completeness:.1%}",
                    [
                        f"Confidence: {confidence:.1%}",
                        f"Quality: {reflection.get('evidence_quality', 'unknown')}",
                        f"Continue research: {'Yes' if reflection.get('needs_more_research', True) else 'No'}",
                    ],
                )

                # === TERMINATION DECISION ===
                # Agent decides when it has achieved sufficient depth
                needs_more_research = reflection.get("needs_more_research", True)
                termination_confidence = reflection.get("termination_confidence", 0.5)
                
                if not needs_more_research and termination_confidence > 0.7:
                    self.console.print(f"[green]✓ Research complete after {iteration + 1} iterations (agent decision)[/green]")
                    break
                    
                if confidence >= state.confidence_threshold and research_completeness > 0.8:
                    self.console.print(f"[green]✓ High confidence threshold reached[/green]")
                    break
                    
                if len(state.all_evidence) >= config.MAX_TOTAL_EVIDENCE_CHUNKS:
                    self.console.print(f"[yellow]⚠ Maximum evidence limit reached[/yellow]")
                    break

                # Continue to next iteration
                if iteration < config.MAX_RESEARCH_ITERATIONS - 1:
                    self.console.print(f"[blue]→ Continuing to iteration {iteration + 2}[/blue]")

            # === FINAL RESPONSE GENERATION ===
            state.set_step(AgentStep.GENERATING)
            self.progress_ui.update_step(AgentStep.GENERATING, "Generating comprehensive response from research")
            
            # Use accumulated insights for final response
            final_response = self.generate_final_response_from_insights(state, accumulated_insights)
            
            state.complete(final_response, "research_complete", reflection.get("confidence", 0.8) if reflection else 0.8)
            
            # Show detailed final response info
            insights_summary = f"Synthesized {len(accumulated_insights)} research iterations into comprehensive response"
            self.progress_ui.complete_step(
                AgentStep.GENERATING,
                insights_summary,
                [f"Response length: {len(final_response)} characters", f"Research depth: {depth_assessment}"]
            )

            self.progress_ui.finish_session(final_response, state)
            return final_response

        except Exception as e:
            error_msg = f"Agent encountered an error: {e}"
            self.progress_ui.show_error(error_msg)
            return f"I apologize, but I encountered an error while processing your question: {e}"


