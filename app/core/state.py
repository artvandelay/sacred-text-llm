"""
Agent State Management for Sacred Texts LLM Agent
Tracks iterations, evidence, confidence, and search queries
"""

import json
import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class AgentStep(Enum):
    """Agent step types for progress tracking"""
    PLANNING = "planning"
    SEARCHING = "searching"
    REFLECTING = "reflecting"
    GENERATING = "generating"
    COMPLETE = "complete"


@dataclass
class SearchResult:
    """Container for search results with metadata"""
    query: str
    documents: List[str]
    metadatas: List[Dict[str, Any]]
    distances: List[float]
    timestamp: float = field(default_factory=time.time)
    

@dataclass
class AgentIteration:
    """Single iteration of the agent loop"""
    iteration_num: int
    plan: Dict[str, Any] = field(default_factory=dict)
    searches: List[SearchResult] = field(default_factory=list)
    reflection: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    timestamp: float = field(default_factory=time.time)


@dataclass 
class AgentState:
    """Complete state for an agent session"""
    
    # Input
    original_question: str
    
    # Configuration
    max_iterations: int = 4
    confidence_threshold: float = 0.75
    max_parallel_queries: int = 3
    
    # State tracking
    current_iteration: int = 0
    iterations: List[AgentIteration] = field(default_factory=list)
    all_evidence: List[str] = field(default_factory=list)
    all_search_queries: List[str] = field(default_factory=list)
    
    # Status
    is_complete: bool = False
    final_confidence: float = 0.0
    final_response: str = ""
    completion_reason: str = ""  # "confidence", "max_iterations", "error"
    
    # Progress tracking
    current_step: AgentStep = AgentStep.PLANNING
    step_start_time: float = field(default_factory=time.time)
    session_start_time: float = field(default_factory=time.time)
    
    def start_iteration(self) -> AgentIteration:
        """Start a new iteration"""
        iteration = AgentIteration(iteration_num=self.current_iteration)
        self.iterations.append(iteration)
        return iteration
    
    def current_iteration_obj(self) -> Optional[AgentIteration]:
        """Get current iteration object"""
        return self.iterations[-1] if self.iterations else None
    
    def add_search_result(self, result: SearchResult):
        """Add search result to current iteration and global evidence"""
        if current_iter := self.current_iteration_obj():
            current_iter.searches.append(result)
        
        # Add to global evidence (deduplicate)
        for doc in result.documents:
            if doc not in self.all_evidence:
                self.all_evidence.append(doc)
        
        # Track search queries
        if result.query not in self.all_search_queries:
            self.all_search_queries.append(result.query)
    
    def set_step(self, step: AgentStep):
        """Update current step and timestamp"""
        self.current_step = step
        self.step_start_time = time.time()
    
    def complete(self, response: str, reason: str, confidence: float = 0.0):
        """Mark the agent session as complete"""
        self.is_complete = True
        self.final_response = response
        self.completion_reason = reason
        self.final_confidence = confidence
        self.set_step(AgentStep.COMPLETE)
    
    def should_continue(self) -> bool:
        """Check if agent should continue iterating"""
        if self.is_complete:
            return False
        
        if self.current_iteration >= self.max_iterations:
            return False
            
        # Check if we have enough evidence
        if len(self.all_evidence) == 0:
            return True  # Need at least some evidence
            
        return True
    
    def get_evidence_summary(self) -> str:
        """Get formatted summary of all evidence"""
        if not self.all_evidence:
            return "No evidence collected yet."
        
        # Limit evidence length for prompts
        evidence_parts = []
        total_chars = 0
        max_chars = 8000  # Reasonable limit for context
        
        for i, evidence in enumerate(self.all_evidence):
            if total_chars + len(evidence) > max_chars:
                evidence_parts.append(f"... and {len(self.all_evidence) - i} more pieces of evidence")
                break
            evidence_parts.append(f"Evidence {i+1}: {evidence}")
            total_chars += len(evidence)
        
        return "\n\n".join(evidence_parts)
    
    def get_search_history(self) -> List[str]:
        """Get list of all search queries attempted"""
        return self.all_search_queries.copy()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/debugging"""
        return {
            "question": self.original_question,
            "iterations": self.current_iteration,
            "evidence_count": len(self.all_evidence),
            "queries_tried": len(self.all_search_queries),
            "confidence": self.final_confidence,
            "completion_reason": self.completion_reason,
            "is_complete": self.is_complete,
            "duration_seconds": time.time() - self.session_start_time
        }


def parse_json_response(response: str, fallback: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse JSON from LLM response with fallback
    Handles common LLM JSON formatting issues
    """
    try:
        # Try to find JSON in the response
        response = response.strip()
        
        # Look for JSON between ```json and ``` or just {} 
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            json_str = response[start:end].strip()
        elif "{" in response and "}" in response:
            start = response.find("{")
            end = response.rfind("}") + 1
            json_str = response[start:end]
        else:
            json_str = response
        
        return json.loads(json_str)
        
    except (json.JSONDecodeError, ValueError) as e:
        # Return fallback with error info
        fallback["_parse_error"] = str(e)
        fallback["_original_response"] = response
        return fallback
