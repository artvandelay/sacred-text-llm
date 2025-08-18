# Modes Architecture Implementation Plan

This document provides a detailed, step-by-step implementation plan for refactoring the Sacred Texts LLM to support multiple experimental "modes" with minimal disruption to the core codebase.

## Overview

The goal is to create an architecture where different experimental features (modes) can be added as isolated modules without touching the core agent logic, UI, or deployment infrastructure. Each mode follows a simple contract: it receives a query and returns a response, optionally yielding intermediate updates during processing.

## Core Concepts

1. **Mode**: A self-contained experimental feature (e.g., Deep Research, Contemplative, Koan Generator)
2. **Generator Pattern**: Each mode's `run()` method is a Python generator that yields intermediate updates and returns the final response
3. **Centralized Selection**: Entry points (`agent_chat.py` and `web_app.py`) handle mode selection and output rendering
4. **Shared Configuration**: Single config file for all mode-specific settings

## Implementation Steps

### Phase 1: Create the Modes Infrastructure

#### Step 1.1: Create the Modes Directory Structure

```bash
# From project root
mkdir -p app/modes
touch app/modes/__init__.py
```

#### Step 1.2: Create the Base Mode Contract

Create `app/modes/base.py`:

```python
from abc import ABC, abstractmethod
from typing import Generator, Dict, Any, List, Optional

class BaseMode(ABC):
    """
    Abstract base class for all experimental modes.
    
    The contract is simple:
    - Input: query string and optional chat history
    - Output: Generator that yields intermediate steps and returns final response
    """
    
    def __init__(self, llm_provider, vector_store):
        """
        Initialize the mode with required dependencies.
        
        Args:
            llm_provider: The LLM provider instance (from app.providers)
            vector_store: The vector store instance (ChromaDB)
        """
        self.llm = llm_provider
        self.db = vector_store
    
    @abstractmethod
    def run(self, query: str, chat_history: Optional[List[Dict]] = None) -> Generator[Dict[str, Any], None, str]:
        """
        Execute the mode logic.
        
        Args:
            query: The user's input query
            chat_history: Optional conversation history
            
        Yields:
            Dict[str, Any]: Intermediate updates with at least a "type" field
            Example: {"type": "planning", "content": "Analyzing query..."}
            
        Returns:
            str: The final response to the user
        """
        yield {}  # This line is for type checking only
        return ""
```

#### Step 1.3: Create Centralized Configuration

Create `app/modes/config.py`:

```python
"""
Centralized configuration for all experimental modes.

Each mode's config is a dictionary that can be accessed by the mode implementation.
To add a new mode, simply add a new CONFIG dictionary here.
"""

# Deep Research Mode (existing agent refactored)
DEEP_RESEARCH_CONFIG = {
    "max_iterations": 4,
    "confidence_threshold": 0.75,
    "max_parallel_queries": 3,
    "max_total_evidence_chunks": 15,
    "show_confidence_scores": True,
}

# Contemplative Mode - ONLY settings, NO prompts
CONTEMPLATIVE_CONFIG = {
    "max_results": 1,
}

# Koan Generator Mode (future) - ONLY settings, NO prompts
KOAN_GENERATOR_CONFIG = {
    "style": "zen",
    "temperature": 0.9,
    "examples_to_analyze": 5,
}

# Add more mode configs as needed...
```

### Phase 2: Refactor Existing Agent into Deep Research Mode

#### Step 2.1: Extract Core Agent Logic

Create `app/modes/deep_research.py`:

```python
"""
Deep Research Mode - The original powerful agent refactored as a mode.

This mode performs iterative research with planning, parallel search, and reflection.
"""

from typing import Generator, Dict, Any, List, Optional
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.modes.base import BaseMode
from app.modes.config import DEEP_RESEARCH_CONFIG
from app.core.state import AgentState, AgentIteration  # Reuse existing state management

class DeepResearchMode(BaseMode):
    """The original deep research agent as a mode."""
    
    def __init__(self, llm_provider, vector_store):
        super().__init__(llm_provider, vector_store)
        self.config = DEEP_RESEARCH_CONFIG
        
    def run(self, query: str, chat_history: Optional[List[Dict]] = None) -> Generator[Dict[str, Any], None, str]:
        """
        Execute the deep research process.
        
        Yields intermediate updates for:
        - Planning steps
        - Search queries and results
        - Reflection and confidence scores
        - Final synthesis progress
        """
        # Initialize state
        state = AgentState(query=query)
        
        # Main research loop
        for iteration in range(self.config["max_iterations"]):
            yield {
                "type": "iteration_start",
                "iteration": iteration + 1,
                "max_iterations": self.config["max_iterations"]
            }
            
            # Step 1: Planning
            yield {"type": "planning", "content": "Analyzing query and planning search strategy..."}
            
            plan = self._plan_search_strategy(state, chat_history)
            
            yield {
                "type": "plan_complete",
                "reasoning": plan.get("reasoning", ""),
                "search_queries": plan.get("search_queries", []),
                "confidence_estimate": plan.get("confidence_estimate", 0.0)
            }
            
            if not plan.get("needs_search", True):
                yield {"type": "skip_search", "reason": "Sufficient information already gathered"}
                break
            
            # Step 2: Parallel Search
            queries = plan.get("search_queries", [])[:self.config["max_parallel_queries"]]
            
            yield {
                "type": "searching",
                "query_count": len(queries),
                "queries": queries
            }
            
            results = self._search_parallel(queries)
            
            yield {
                "type": "search_complete",
                "results_count": sum(len(r.passages) for r in results),
                "sources": list(set(p.metadata.get("source", "Unknown") for r in results for p in r.passages))
            }
            
            # Add evidence to state
            state.add_iteration(AgentIteration(
                iteration_number=iteration,
                search_queries=queries,
                search_results=results,
                confidence=plan.get("confidence_estimate", 0.0)
            ))
            
            # Step 3: Reflection
            yield {"type": "reflecting", "content": "Evaluating gathered evidence..."}
            
            reflection = self._reflect_on_evidence(state)
            
            yield {
                "type": "reflection_complete",
                "confidence": reflection.get("confidence", 0.0),
                "evidence_quality": reflection.get("evidence_quality", "unknown"),
                "gaps_identified": reflection.get("gaps_identified", [])
            }
            
            # Check termination conditions
            if reflection.get("confidence", 0.0) >= self.config["confidence_threshold"]:
                yield {
                    "type": "terminating",
                    "reason": f"Confidence threshold reached: {reflection['confidence']:.0%}"
                }
                break
                
            if not reflection.get("needs_more_search", True):
                yield {
                    "type": "terminating",
                    "reason": "Agent determined sufficient information gathered"
                }
                break
        
        # Step 4: Final Synthesis
        yield {"type": "synthesizing", "content": "Generating comprehensive response..."}
        
        final_response = self._generate_final_response(state, chat_history)
        
        yield {
            "type": "synthesis_complete",
            "total_iterations": len(state.iterations),
            "total_evidence": state.total_evidence_chunks(),
            "final_confidence": state.get_confidence()
        }
        
        return final_response
    
    def _plan_search_strategy(self, state: AgentState, chat_history: Optional[List[Dict]]) -> Dict:
        """Plan the next search strategy based on current state."""
        # Implementation details...
        # This would contain the LLM prompting logic from the original agent
        pass
    
    def _search_parallel(self, queries: List[str]) -> List:
        """Execute searches in parallel."""
        # Implementation details...
        # This would contain the parallel search logic from the original agent
        pass
    
    def _reflect_on_evidence(self, state: AgentState) -> Dict:
        """Reflect on gathered evidence and determine next steps."""
        # Implementation details...
        # This would contain the reflection logic from the original agent
        pass
    
    def _generate_final_response(self, state: AgentState, chat_history: Optional[List[Dict]]) -> str:
        """Generate the final comprehensive response."""
        # Implementation details...
        # This would contain the synthesis logic from the original agent
        pass
```

#### Step 2.2: Update app/agent/core.py

The existing `app/agent/core.py` should be refactored to remove the main agent loop (now in the mode) but keep reusable utilities:

```python
# app/agent/core.py - After refactoring

"""
Core utilities for agent functionality.

This module contains reusable components that modes can leverage,
but no longer contains the main agent loop (moved to deep_research mode).
"""

from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import chromadb

def search_texts(query: str, vector_store, n_results: int = 5) -> Dict[str, Any]:
    """
    Perform a single vector search.
    
    This is a utility function that any mode can use.
    """
    # Existing search implementation
    pass

def search_parallel(queries: List[str], vector_store, max_workers: int = 3) -> List[Dict[str, Any]]:
    """
    Execute multiple searches in parallel.
    
    This is a utility function that any mode can use for parallel search.
    """
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(search_texts, q, vector_store): q for q in queries}
        results = []
        for future in as_completed(futures):
            results.append(future.result())
    return results

# Other reusable utilities...
```

### Phase 3: Create Example Experimental Mode

#### Step 3.1: Implement Contemplative Mode

Create `app/modes/contemplative.py`:

```python
"""
Contemplative Mode - A simple mode for spiritual reflection.

This mode returns a single passage and a thoughtful question for contemplation.
"""

from typing import Generator, Dict, Any, List, Optional

from app.modes.base import BaseMode
from app.modes.config import CONTEMPLATIVE_CONFIG
# No core utilities - each mode implements its own logic

class ContemplativeMode(BaseMode):
    """A mode focused on contemplative reflection rather than comprehensive research."""
    
    def __init__(self, llm_provider, vector_store):
        super().__init__(llm_provider, vector_store)
        self.config = CONTEMPLATIVE_CONFIG
        
    def run(self, query: str, chat_history: Optional[List[Dict]] = None) -> Generator[Dict[str, Any], None, str]:
        """
        Find a relevant passage and generate a contemplative question.
        
        This is a simple mode that demonstrates the architecture.
        """
        # Step 1: Search for relevant passage
        yield {"type": "searching", "content": f"Finding wisdom about: {query}"}
        
        results = search_texts(query, self.db, n_results=self.config["max_results"])
        
        if not results or not results.get("passages"):
            yield {"type": "error", "content": "No relevant passages found"}
            return "I couldn't find relevant passages for contemplation on this topic."
        
        # Get the top passage
        passage = results["passages"][0]
        text = passage.get("text", "")
        source = passage.get("metadata", {}).get("source", "Unknown source")
        
        yield {
            "type": "passage_found",
            "source": source,
            "preview": text[:100] + "..." if len(text) > 100 else text
        }
        
        # Step 2: Generate contemplative question
        yield {"type": "generating", "content": "Crafting a question for reflection..."}
        
        prompt = self.config["prompt_template"].format(
            passage=text,
            source=source
        )
        
        # Call LLM to generate question
        response = self.llm.complete(prompt, max_tokens=200)
        
        # Format final response
        final_response = f"""**Sacred Text:**
{text}

*Source: {source}*

**For Your Contemplation:**
{response}"""
        
        yield {"type": "complete", "content": "Reflection prepared"}
        
        return final_response
```

### Phase 4: Update Entry Points

#### Step 4.1: Update agent_chat.py

Modify the main script to support mode selection:

```python
# Key changes to agent_chat.py

import argparse
from typing import Dict, Any

# Import all modes
from app.modes.deep_research import DeepResearchMode
from app.modes.contemplative import ContemplativeMode
# Future: from app.modes.koan_generator import KoanGeneratorMode

# Mode registry
AVAILABLE_MODES = {
    "deep_research": DeepResearchMode,
    "contemplative": ContemplativeMode,
    # Add new modes here as they're created
}

def get_mode(mode_name: str, llm_provider, vector_store):
    """Get a mode instance by name."""
    mode_class = AVAILABLE_MODES.get(mode_name)
    if not mode_class:
        raise ValueError(f"Unknown mode: {mode_name}. Available: {list(AVAILABLE_MODES.keys())}")
    return mode_class(llm_provider, vector_store)

def display_intermediate(update: Dict[str, Any], ui):
    """Display intermediate updates based on their type."""
    update_type = update.get("type", "unknown")
    
    # Map update types to UI display methods
    if update_type == "planning":
        ui.show_planning(update.get("content", ""))
    elif update_type == "searching":
        ui.show_searching(update.get("queries", []))
    elif update_type == "reflecting":
        ui.show_reflecting(update.get("content", ""))
    # ... handle other update types
    else:
        # Fallback for unknown types
        ui.show_generic_update(update)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", 
                       choices=list(AVAILABLE_MODES.keys()),
                       default="deep_research",
                       help="Which mode to run")
    parser.add_argument("--query", 
                       type=str,
                       help="Direct query (non-interactive)")
    args = parser.parse_args()
    
    # Initialize dependencies
    llm = get_llm_provider()  # Existing function
    vector_store = get_vector_store()  # Existing function
    ui = get_ui()  # Existing function
    
    # Handle direct query (for testing)
    if args.query:
        mode = get_mode(args.mode, llm, vector_store)
        run_single_query(mode, args.query, ui)
        return
    
    # Interactive chat loop
    chat_history = []
    
    print(f"Starting Sacred Texts LLM in {args.mode} mode...")
    print("Type 'exit' to quit, 'switch <mode>' to change modes\n")
    
    current_mode_name = args.mode
    
    while True:
        try:
            query = input("You: ").strip()
            
            if query.lower() == "exit":
                break
                
            if query.lower().startswith("switch "):
                # Handle mode switching
                new_mode = query.split()[1]
                if new_mode in AVAILABLE_MODES:
                    current_mode_name = new_mode
                    print(f"Switched to {new_mode} mode")
                else:
                    print(f"Unknown mode. Available: {list(AVAILABLE_MODES.keys())}")
                continue
            
            # Run the query in current mode
            mode = get_mode(current_mode_name, llm, vector_store)
            run_query_with_mode(mode, query, chat_history, ui)
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break

def run_query_with_mode(mode, query: str, chat_history: list, ui):
    """Run a query using the specified mode and handle its output."""
    try:
        # Get the generator
        generator = mode.run(query, chat_history)
        
        # Process intermediate updates
        final_response = None
        while True:
            try:
                update = next(generator)
                display_intermediate(update, ui)
            except StopIteration as e:
                # Generator completed, get return value
                final_response = e.value
                break
        
        # Display final response
        ui.show_final_response(final_response)
        
        # Update chat history
        chat_history.append({"role": "user", "content": query})
        chat_history.append({"role": "assistant", "content": final_response})
        
    except Exception as e:
        ui.show_error(f"Error running mode: {str(e)}")
```

#### Step 4.2: Update web_app.py

Similar changes for the web interface:

```python
# Key changes to deploy/web_app.py

from fastapi import FastAPI, WebSocket
from app.modes.deep_research import DeepResearchMode
from app.modes.contemplative import ContemplativeMode

# Mode registry (same as CLI)
AVAILABLE_MODES = {
    "deep_research": DeepResearchMode,
    "contemplative": ContemplativeMode,
}

@app.post("/query")
async def query(request: QueryRequest):
    """Handle query with specified mode."""
    mode_name = request.mode or "deep_research"
    
    # Get mode instance
    mode_class = AVAILABLE_MODES.get(mode_name)
    if not mode_class:
        raise HTTPException(400, f"Unknown mode: {mode_name}")
    
    mode = mode_class(llm_provider, vector_store)
    
    # For simple HTTP request, we collect all output
    updates = []
    final_response = ""
    
    try:
        generator = mode.run(request.text, request.chat_history)
        while True:
            try:
                update = next(generator)
                updates.append(update)
            except StopIteration as e:
                final_response = e.value
                break
    except Exception as e:
        raise HTTPException(500, str(e))
    
    return {
        "response": final_response,
        "mode": mode_name,
        "updates": updates,  # Client can use these for progress display
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time streaming of mode updates."""
    await websocket.accept()
    
    try:
        while True:
            # Receive query
            data = await websocket.receive_json()
            query = data.get("text", "")
            mode_name = data.get("mode", "deep_research")
            chat_history = data.get("chat_history", [])
            
            # Get mode
            mode_class = AVAILABLE_MODES.get(mode_name)
            if not mode_class:
                await websocket.send_json({"type": "error", "content": f"Unknown mode: {mode_name}"})
                continue
            
            mode = mode_class(llm_provider, vector_store)
            
            # Stream updates
            try:
                generator = mode.run(query, chat_history)
                while True:
                    try:
                        update = next(generator)
                        await websocket.send_json(update)
                    except StopIteration as e:
                        # Send final response
                        await websocket.send_json({
                            "type": "final_response",
                            "content": e.value
                        })
                        break
            except Exception as e:
                await websocket.send_json({"type": "error", "content": str(e)})
                
    except Exception as e:
        print(f"WebSocket error: {e}")
```

### Phase 5: Testing and Validation

#### Step 5.1: Create Test Script

Create `test_modes.py`:

```python
"""
Test script to validate the modes architecture.
"""

import sys
from app.modes.deep_research import DeepResearchMode
from app.modes.contemplative import ContemplativeMode
from app.core.providers import get_provider
# Initialize your own dependencies as needed

def test_mode(mode_class, query: str):
    """Test a single mode."""
    print(f"\nTesting {mode_class.__name__} with query: '{query}'")
    print("-" * 80)
    
    # Initialize
    llm = get_provider()
    db = get_vector_store()
    mode = mode_class(llm, db)
    
    # Run and collect output
    updates = []
    try:
        generator = mode.run(query)
        while True:
            try:
                update = next(generator)
                updates.append(update)
                print(f"Update: {update}")
            except StopIteration as e:
                final_response = e.value
                break
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    print(f"\nFinal response:\n{final_response}\n")
    print(f"Total updates: {len(updates)}")
    return True

def main():
    # Test queries
    test_queries = [
        "What is compassion?",
        "Tell me about the nature of wisdom",
    ]
    
    # Test each mode
    modes_to_test = [DeepResearchMode, ContemplativeMode]
    
    for query in test_queries:
        for mode_class in modes_to_test:
            success = test_mode(mode_class, query)
            if not success:
                print(f"FAILED: {mode_class.__name__}")
                sys.exit(1)
    
    print("\nAll tests passed!")

if __name__ == "__main__":
    main()
```

### Phase 6: Documentation and Guidelines

#### Step 6.1: Create Mode Development Guide

Create `docs/creating-new-modes.md`:

```markdown
# Creating New Modes

This guide explains how to create a new experimental mode for the Sacred Texts LLM.

## Quick Start

1. Create a new file in `app/modes/` named after your mode (e.g., `koan_generator.py`)
2. Import and extend `BaseMode`
3. Implement the `run()` method as a generator
4. Add configuration to `app/modes/config.py`
5. Register the mode in entry points

## Example Template

```python
from typing import Generator, Dict, Any, List, Optional
from app.modes.base import BaseMode
from app.modes.config import YOUR_MODE_CONFIG

class YourMode(BaseMode):
    def __init__(self, llm_provider, vector_store):
        super().__init__(llm_provider, vector_store)
        self.config = YOUR_MODE_CONFIG
        
    def run(self, query: str, chat_history: Optional[List[Dict]] = None) -> Generator[Dict[str, Any], None, str]:
        # Yield updates as you progress
        yield {"type": "starting", "content": "Beginning process..."}
        
        # Your mode logic here
        result = self.process_query(query)
        
        # Return final response
        return result
```

## Best Practices

1. **Keep it Simple**: Each mode should do one thing well
2. **Yield Meaningful Updates**: Help users understand what's happening
3. **Handle Errors Gracefully**: Always return something useful
4. **Self-Contained Logic**: Implement all mode logic within the mode file
5. **Document Your Config**: Explain what each setting does

## Common Update Types

- `searching`: Performing vector search
- `planning`: Determining strategy
- `generating`: Creating content with LLM
- `analyzing`: Processing results
- `error`: Something went wrong
- `complete`: Process finished
```

## Success Criteria

The implementation is complete when:

1. ✅ The modes directory structure exists with base class and config
2. ✅ Deep research agent is refactored into a mode
3. ✅ At least one new experimental mode is implemented
4. ✅ Both CLI and web interfaces support mode selection
5. ✅ All existing tests pass
6. ✅ Mode switching works seamlessly
7. ✅ Documentation is complete for adding new modes

## Notes for Implementation

- Start with Phase 1 and 2 to establish the foundation
- Test frequently with simple queries
- Keep the generator pattern simple - don't over-engineer
- Focus on making it easy to add new modes
- Preserve all existing functionality of the deep research agent

This architecture will enable rapid experimentation while maintaining a clean, maintainable codebase.
