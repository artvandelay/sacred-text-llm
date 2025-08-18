"""
Deep Research Mode - A comprehensive research agent that performs iterative search, planning, and synthesis.

This mode is completely self-contained and includes all logic needed for deep research.
It does NOT depend on app.agent.core which is now minimal.
"""

import os
import time
import json
import concurrent.futures
from typing import Generator, Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field

from app.modes.base import BaseMode
from app.modes.config import DEEP_RESEARCH_CONFIG
from app.agent import config as agent_config
from app.core.state import SearchResult, parse_json_response
from app.core.vector_store import VectorStore, ChromaVectorStore
import ollama


@dataclass
class DeepResearchState:
    """Encapsulates the state for a deep research session."""
    original_question: str
    iterations: List[Dict[str, Any]] = field(default_factory=list)
    all_evidence_chunks: List[Dict[str, Any]] = field(default_factory=list)
    accumulated_insights: List[str] = field(default_factory=list)
    chat_history: Optional[List[Dict]] = None
    
    def add_iteration(self, iteration_data: Dict[str, Any]):
        """Add a new iteration to the state."""
        self.iterations.append(iteration_data)
    
    def add_evidence(self, chunks: List[Dict[str, Any]]):
        """Add evidence chunks to the state."""
        self.all_evidence_chunks.extend(chunks)
    
    def add_insight(self, insight: str):
        """Add an insight to accumulated insights."""
        self.accumulated_insights.append(insight)


class DeepResearchMode(BaseMode):
    """
    The original deep research agent as a self-contained mode.
    
    This mode performs iterative research with:
    - Planning and query generation
    - Parallel search execution
    - Evidence synthesis
    - Reflection and confidence assessment
    - Final comprehensive response generation
    """
    
    def __init__(self, llm_provider, vector_store):
        super().__init__(llm_provider, vector_store)
        self.config = DEEP_RESEARCH_CONFIG
        # adapt collection to vector store interface if needed
        if hasattr(vector_store, "query"):
            self.store: VectorStore = ChromaVectorStore(vector_store)
        else:
            self.store = vector_store
        
    def run(self, query: str, chat_history: Optional[List[Dict]] = None) -> Generator[Dict[str, Any], None, str]:
        """
        Execute the deep research process.
        
        Yields intermediate updates and returns final response.
        """
        # Initialize research state
        state = DeepResearchState(
            original_question=query,
            chat_history=chat_history
        )
        
        yield {
            "type": "session_start",
            "question": query,
            "max_iterations": self.config["max_iterations"]
        }
        
        try:
            # Main research loop
            for iteration_num in range(self.config["max_iterations"]):
                yield {
                    "type": "iteration_start",
                    "iteration": iteration_num + 1,
                    "max_iterations": self.config["max_iterations"]
                }
                
                # Step 1: Generate research queries
                yield {"type": "planning", "content": "Analyzing query and planning search strategy..."}
                query_plan = self._generate_research_queries(state)
                
                if not query_plan.get("needs_search", True):
                    yield {"type": "planning", "content": "Sufficient information gathered. Proceeding to synthesis."}
                    break
                
                # Extract queries from plan
                search_queries = query_plan.get("search_queries", [query])[:self.config["max_parallel_queries"]]
                yield {
                    "type": "search_planned",
                    "queries": search_queries,
                    "reasoning": query_plan.get("reasoning", "")
                }
                
                # Step 2: Execute parallel searches
                yield {"type": "searching", "content": f"Searching {len(search_queries)} queries in parallel..."}
                search_results = self._search_parallel(search_queries)
                
                # Add evidence to state
                for result in search_results:
                    # Convert SearchResult to chunks format for state
                    chunks = []
                    for i, doc in enumerate(result.documents):
                        chunks.append({
                            'text': doc,
                            'source': result.metadatas[i].get('source', 'unknown') if i < len(result.metadatas) else 'unknown',
                            'distance': result.distances[i] if i < len(result.distances) else 0
                        })
                    state.add_evidence(chunks)
                
                yield {
                    "type": "search_complete",
                    "results_count": sum(len(r.documents) for r in search_results),
                    "queries": search_queries
                }
                
                # Step 3: Synthesize insights from this iteration
                yield {"type": "synthesizing", "content": "Analyzing retrieved passages..."}
                iteration_insights = self._synthesize_search_batch(search_results, query)
                
                if iteration_insights:
                    state.add_insight(iteration_insights)
                    yield {
                        "type": "synthesis_complete",
                        "insight_preview": iteration_insights[:200] + "..." if len(iteration_insights) > 200 else iteration_insights
                    }
                
                # Step 4: Reflect on progress
                yield {"type": "reflecting", "content": "Evaluating research progress..."}
                reflection = self._reflect_on_evidence(state, iteration_num)
                
                confidence = reflection.get("confidence", 0)
                yield {
                    "type": "reflection_complete",
                    "confidence": confidence,
                    "needs_more": reflection.get("needs_more_search", False),
                    "reasoning": reflection.get("reasoning", "")
                }
                
                # Record iteration
                state.add_iteration({
                    "iteration": iteration_num + 1,
                    "queries": search_queries,
                    "results_count": sum(len(r.documents) for r in search_results),
                    "confidence": confidence,
                    "insights": iteration_insights
                })
                
                # Check termination conditions
                if confidence >= self.config["confidence_threshold"]:
                    yield {"type": "confidence_reached", "confidence": confidence}
                    break
                
                if not reflection.get("needs_more_search", True):
                    yield {"type": "research_complete", "reason": "Sufficient evidence gathered"}
                    break
                
                # Check evidence limits
                if len(state.all_evidence_chunks) >= self.config.get("max_total_evidence_chunks", 15):
                    yield {"type": "evidence_limit", "chunks": len(state.all_evidence_chunks)}
                    break
            
            # Generate final response
            yield {"type": "generating", "content": "Synthesizing comprehensive response..."}
            final_response = self._generate_final_response(state)
            
            yield {
                "type": "complete",
                "iterations": len(state.iterations),
                "total_evidence": len(state.all_evidence_chunks),
                "insights_generated": len(state.accumulated_insights)
            }
            
            return final_response
            
        except Exception as e:
            yield {"type": "error", "error": str(e)}
            return f"I apologize, but I encountered an error while researching your question: {str(e)}"
    
    def _search_texts(self, query: str, k: int = None) -> SearchResult:
        """Execute a single search query."""
        k = k or agent_config.DEFAULT_SEARCH_K
        
        try:
            # Get embedding for the query using the same model as ingestion
            q_embed = ollama.embeddings(model=agent_config.EMBEDDING_MODEL, prompt=query)["embedding"]
            
            # Search the collection using manual embeddings
            results = self.store.query_embeddings([q_embed], k=k)[0]
            
            chunks = []
            # Build SearchResult from adapter result
            return SearchResult(
                query=query,
                documents=results.documents,
                metadatas=results.metadatas,
                distances=results.distances,
            )
        except Exception as e:
            return SearchResult(query=query, documents=[], metadatas=[], distances=[])
    
    def _search_parallel(self, queries: List[str], k: int = None) -> List[SearchResult]:
        """Execute multiple searches in parallel."""
        if len(queries) == 1:
            return [self._search_texts(queries[0], k)]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config["max_parallel_queries"]) as executor:
            future_to_query = {executor.submit(self._search_texts, query, k): query for query in queries}
            
            results = []
            for future in concurrent.futures.as_completed(future_to_query):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    query = future_to_query[future]
                    results.append(SearchResult(query=query, documents=[], metadatas=[], distances=[]))
            
            return results
    
    def _generate_research_queries(self, state: DeepResearchState) -> Dict[str, Any]:
        """Generate research queries based on current state."""
        try:
            # Build context from accumulated insights
            context = ""
            if state.accumulated_insights:
                context = f"""
Previous research insights:
{chr(10).join(f"- {insight[:200]}..." for insight in state.accumulated_insights[-3:])}

Based on these insights, we need to explore new angles or fill gaps.
"""
            
            # Determine LLM model based on provider
            if agent_config.LLM_PROVIDER == "openrouter":
                model = agent_config.OPENROUTER_CHAT_MODEL
            else:
                model = agent_config.OLLAMA_CHAT_MODEL
            
            prompt = f"""You are a research assistant planning searches for sacred texts.

Original question: {state.original_question}

{context}

Current iteration: {len(state.iterations) + 1} of {self.config['max_iterations']}
Evidence collected so far: {len(state.all_evidence_chunks)} passages

Generate a search strategy that:
1. Identifies what aspects still need exploration
2. Formulates 1-3 specific search queries
3. Avoids redundant searches

Respond in JSON format:
{{
    "reasoning": "Brief explanation of search strategy",
    "needs_search": true/false,
    "search_queries": ["query1", "query2", "query3"],
    "expected_insights": "What we hope to learn"
}}

Focus on diverse traditions and perspectives."""

            response = self.llm.generate_response([
                {"role": "system", "content": "You are a deep research strategist specializing in sacred texts and spiritual inquiry. Be thorough and scholarly in your approach."},
                {"role": "user", "content": prompt}
            ], model)
            
            fallback = {
                "reasoning": "Searching for relevant passages",
                "needs_search": True,
                "search_queries": [state.original_question],
                "expected_insights": "Direct answers to the question"
            }
            
            return parse_json_response(response, fallback)
            
        except Exception as e:
            import logging; logging.exception("Query generation error")
            return {
                "reasoning": "Fallback search",
                "needs_search": True,
                "search_queries": [state.original_question],
                "expected_insights": "Relevant passages"
            }
    
    def _synthesize_search_batch(self, search_results: List[SearchResult], original_question: str) -> str:
        """Synthesize insights from a batch of search results."""
        if not search_results or not any(r.documents for r in search_results):
            return ""
        
        # Prepare passages for synthesis
        all_passages = []
        for result in search_results:
            for i in range(min(3, len(result.documents))):  # Top 3 from each search
                source = result.metadatas[i].get('source', 'unknown') if i < len(result.metadatas) else 'unknown'
                text = result.documents[i]
                if text:
                    all_passages.append(f"[{source}]: {text}")
        
        if not all_passages:
            return ""
        
        passages_text = "\n\n".join(all_passages[:10])  # Limit to 10 passages
        
        # Determine LLM model based on provider
        if agent_config.LLM_PROVIDER == "openrouter":
            model = agent_config.OPENROUTER_CHAT_MODEL
        else:
            model = agent_config.OLLAMA_CHAT_MODEL
        
        prompt = f"""You are a scholar synthesizing retrieved passages from sacred texts to develop deep insights.

Original question: {original_question}

Retrieved passages:
{passages_text}

Synthesize these passages into coherent insights that:
1. **Direct Response**: How do these texts address the question?
2. **Patterns & Themes**: What common threads or contrasts emerge?
3. **Deeper Implications**: What profound insights or wisdom can be drawn?

Be concise but insightful. Focus on synthesis, not just summary."""

        try:
            response = self.llm.generate_response([
                {"role": "system", "content": "You are a sacred texts scholar specializing in synthesis and deep textual analysis. Provide thoughtful, nuanced interpretations that honor the wisdom traditions while offering clear insights."},
                {"role": "user", "content": prompt}
            ], model)
            return response.strip()
        except Exception as e:
            import logging; logging.exception("Synthesis error")
            return ""
    
    def _reflect_on_evidence(self, state: DeepResearchState, current_iteration: int) -> Dict[str, Any]:
        """Reflect on accumulated evidence and determine next steps."""
        try:
            # Prepare evidence summary
            evidence_summary = f"""
Total evidence: {len(state.all_evidence_chunks)} passages
Iterations completed: {current_iteration + 1}
Insights generated: {len(state.accumulated_insights)}

Recent insights:
{chr(10).join(f"- {insight[:200]}..." for insight in state.accumulated_insights[-3:])}
"""
            
            # Determine LLM model based on provider
            if agent_config.LLM_PROVIDER == "openrouter":
                model = agent_config.OPENROUTER_CHAT_MODEL
            else:
                model = agent_config.OLLAMA_CHAT_MODEL
            
            prompt = f"""You are a research assistant evaluating the completeness of gathered evidence.

Original question: {state.original_question}

{evidence_summary}

Evaluate:
1. How well have we answered the original question?
2. What aspects remain unexplored?
3. Is the evidence sufficient for a comprehensive response?

Respond in JSON format:
{{
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation",
    "needs_more_search": true/false,
    "missing_aspects": ["aspect1", "aspect2"],
    "termination_reasoning": "Why stop or continue"
}}"""

            response = self.llm.generate_response([
                {"role": "system", "content": "You are a research depth assessor specializing in spiritual and philosophical inquiry. Balance thoroughness with practical completion. Be honest about limitations while recognizing when sufficient depth has been achieved."},
                {"role": "user", "content": prompt}
            ], model)
            
            fallback = {
                "confidence": 0.5,
                "reasoning": "Moderate evidence gathered",
                "needs_more_search": current_iteration < 2,
                "missing_aspects": [],
                "termination_reasoning": "Continue gathering evidence"
            }
            
            return parse_json_response(response, fallback)
            
        except Exception as e:
            import logging; logging.exception("Reflection error")
            return {
                "confidence": 0.5,
                "reasoning": "Error in reflection",
                "needs_more_search": False,
                "missing_aspects": [],
                "termination_reasoning": "Error occurred"
            }
    
    def _generate_final_response(self, state: DeepResearchState) -> str:
        """Generate the final comprehensive response."""
        if not state.accumulated_insights and not state.all_evidence_chunks:
            return "I apologize, but I couldn't find relevant information to answer your question."
        
        # Prepare synthesis context
        insights_text = "\n\n".join(state.accumulated_insights) if state.accumulated_insights else "No specific insights generated."
        
        # Get unique sources
        sources = set()
        for chunk in state.all_evidence_chunks:
            source = chunk.get('source', 'unknown')
            if source != 'unknown':
                sources.add(source)
        
        sources_text = ", ".join(list(sources)[:10]) if sources else "various texts"
        
        # Determine LLM model based on provider
        if agent_config.LLM_PROVIDER == "openrouter":
            model = agent_config.OPENROUTER_CHAT_MODEL
        else:
            model = agent_config.OLLAMA_CHAT_MODEL
        
        prompt = f"""You are a wise scholar providing a comprehensive response based on deep research into sacred texts.

Original question: {state.original_question}

Research insights from {len(state.iterations)} iterations:
{insights_text}

Drawing from {len(state.all_evidence_chunks)} passages across {sources_text}, provide a complete, thoughtful response that:

1. **Directly answers** the question with clarity and depth
2. **Synthesizes wisdom** from multiple traditions where relevant
3. **Offers practical insights** that can guide understanding
4. **Acknowledges complexity** where different traditions offer varying perspectives

Structure your response with clear sections if needed. Be comprehensive yet accessible.
Do not mention the research process itself - focus on the wisdom and insights discovered."""

        try:
            response = self.llm.generate_response([
                {"role": "system", "content": "You are a master spiritual teacher and scholar who has spent extensive time researching sacred texts. Your responses demonstrate profound understanding, synthesis across traditions, and practical wisdom."},
                {"role": "user", "content": prompt}
            ], model)
            return response.strip()
        except Exception as e:
            # Fallback response
            if state.accumulated_insights:
                return f"Based on my research:\n\n{state.accumulated_insights[0]}\n\n[Note: Full synthesis could not be completed due to an error]"
            else:
                return "I apologize, but I encountered an error while generating the final response."