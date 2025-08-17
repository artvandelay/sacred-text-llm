# Creating New Modes for Sacred Texts LLM

This guide explains how to create new experimental modes for the Sacred Texts LLM. The modes architecture allows you to add new ways of interacting with the sacred texts without modifying the core system.

## Quick Start

To create a new mode, you need to:

1. Create a new Python file in `app/modes/`
2. Implement a class that extends `BaseMode`
3. Add configuration to `app/modes/config.py`
4. Register the mode in the entry points
5. Test your mode

## Step-by-Step Guide

### Step 1: Create Your Mode File

Create a new file `app/modes/your_mode_name.py`:

```python
"""
Your Mode Name - Brief description

Longer description of what this mode does and how it's different.
"""

from typing import Generator, Dict, Any, List, Optional
import ollama

from app.modes.base import BaseMode
from app.modes.config import YOUR_MODE_CONFIG  # You'll create this
from app.agent import config as agent_config


class YourMode(BaseMode):
    """A brief description of your mode."""
    
    def __init__(self, llm_provider, vector_store):
        super().__init__(llm_provider, vector_store)
        self.config = YOUR_MODE_CONFIG
        
    def run(self, query: str, chat_history: Optional[List[Dict]] = None) -> Generator[Dict[str, Any], None, str]:
        """
        Execute your mode logic.
        
        Yields intermediate updates and returns final response.
        """
        # Step 1: Initialize
        yield {"type": "starting", "content": f"Starting {self.__class__.__name__}..."}
        
        try:
            # Step 2: Your custom logic here
            result = self._do_your_processing(query)
            
            yield {"type": "processing", "content": "Processing completed"}
            
            # Step 3: Generate final response
            final_response = self._format_response(result)
            
            yield {"type": "complete", "content": "Mode execution completed"}
            
            return final_response
            
        except Exception as e:
            yield {"type": "error", "content": f"Error in {self.__class__.__name__}: {str(e)}"}
            return f"I encountered an error: {str(e)}"
    
    def _do_your_processing(self, query: str):
        """Implement your custom processing logic here."""
        # Example: Search for relevant passages
        q_embed = ollama.embeddings(model=agent_config.EMBEDDING_MODEL, prompt=query)["embedding"]
        results = self.db.query(
            query_embeddings=[q_embed], 
            n_results=self.config["max_results"], 
            include=["documents", "metadatas", "distances"]
        )
        return results
    
    def _format_response(self, result):
        """Format your final response."""
        # ALL prompts and logic go here in the mode file, NOT in config
        prompt = f"""You are a helpful assistant.
        
Process this data: {result}
        
Generate a thoughtful response."""

        response = self.llm.generate_response([
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ])
        
        return response
```

### Step 2: Add Configuration

Add your mode's configuration to `app/modes/config.py`:

```python
# Your Mode Configuration - ONLY settings, NO prompts or logic
YOUR_MODE_CONFIG = {
    "max_results": 5,
    "temperature": 0.7,
    "max_iterations": 3,
    # Add any other SETTINGS your mode needs (no prompts!)
}
```

### Step 3: Register Your Mode

Update the mode registries in both entry points:

**In `agent_chat.py`:**
```python
# Import your mode
from app.modes.your_mode_name import YourMode

# Add to registry
AVAILABLE_MODES = {
    "deep_research": {
        "class": DeepResearchMode,
        "description": "Comprehensive research with iterative planning and synthesis"
    },
    "contemplative": {
        "class": ContemplativeMode,
        "description": "Find a meaningful passage and question for reflection"
    },
    "your_mode": {  # Add this
        "class": YourMode,
        "description": "Brief description of what your mode does"
    },
}
```

**In `deploy/web_app.py`:**
```python
# Import your mode
from app.modes.your_mode_name import YourMode

# Add to registry
AVAILABLE_MODES = {
    "deep_research": {
        "class": DeepResearchMode,
        "description": "Comprehensive research with iterative planning and synthesis"
    },
    "contemplative": {
        "class": ContemplativeMode,
        "description": "Find a meaningful passage and question for reflection"
    },
    "your_mode": {  # Add this
        "class": YourMode,
        "description": "Brief description of what your mode does"
    },
}
```

### Step 4: Test Your Mode

Test your mode from the command line:

```bash
# List all modes (should include yours)
python agent_chat.py --list-modes

# Test with a direct query
python agent_chat.py --mode your_mode --query "Test question"

# Test interactively
python agent_chat.py --mode your_mode
```

## Common Patterns and Examples

### Example 1: Simple Search and Transform Mode

```python
def run(self, query: str, chat_history: Optional[List[Dict]] = None) -> Generator[Dict[str, Any], None, str]:
    """Find passages and transform them in a specific way."""
    
    yield {"type": "searching", "content": f"Searching for: {query}"}
    
    # Search for passages
    results = self._search_passages(query)
    
    yield {"type": "search_complete", "results_count": len(results)}
    
    yield {"type": "transforming", "content": "Applying transformation..."}
    
    # Transform the results
    transformed = self._transform_passages(results)
    
    yield {"type": "complete", "content": "Transformation complete"}
    
    return transformed
```

### Example 2: Multi-Step Processing Mode

```python
def run(self, query: str, chat_history: Optional[List[Dict]] = None) -> Generator[Dict[str, Any], None, str]:
    """Demonstrate multi-step processing with progress updates."""
    
    steps = ["analyze", "search", "synthesize", "format"]
    
    for i, step in enumerate(steps):
        yield {
            "type": "step_start",
            "step": step,
            "progress": i / len(steps),
            "content": f"Starting {step}..."
        }
        
        # Do the actual work
        result = getattr(self, f"_do_{step}")(query)
        
        yield {
            "type": "step_complete", 
            "step": step,
            "progress": (i + 1) / len(steps),
            "content": f"Completed {step}"
        }
    
    return "Final result"
```

### Example 3: Interactive Mode with User Input

```python
def run(self, query: str, chat_history: Optional[List[Dict]] = None) -> Generator[Dict[str, Any], None, str]:
    """Mode that might need additional user input."""
    
    yield {"type": "analyzing", "content": "Analyzing your question..."}
    
    # Analyze the query to determine what additional info might be needed
    if self._needs_clarification(query):
        yield {
            "type": "clarification_needed",
            "content": "I need more information about...",
            "suggestions": ["Option A", "Option B", "Option C"]
        }
        # Note: In the current architecture, you can't actually wait for user input
        # This is just to show how you might structure it for future enhancements
    
    # Continue with processing
    result = self._process_query(query)
    
    return result
```

## Update Types Reference

Your mode can yield different types of updates to communicate progress:

### Standard Update Types

- `"starting"` - Mode is initializing
- `"searching"` - Performing vector search
- `"processing"` - General processing step
- `"analyzing"` - Analysis phase
- `"generating"` - Generating content with LLM
- `"complete"` - Processing completed successfully
- `"error"` - An error occurred

### Custom Update Types

You can create your own update types. The display system will show them as generic updates if they're not specifically handled.

### Update Structure

All updates should be dictionaries with at least a `"type"` field:

```python
{
    "type": "your_update_type",
    "content": "Description of what's happening",
    "progress": 0.5,  # Optional: 0.0 to 1.0
    "details": {...}  # Optional: additional data
}
```

## Best Practices

### 1. Keep It Simple
- Each mode should do one thing well
- Don't try to replicate the deep research mode's complexity unless needed
- Focus on your unique value proposition

### 0. **CRITICAL**: Keep All Logic in Mode File
- **ALL prompts, logic, and processing MUST be in the mode file itself**
- **Config files are ONLY for settings** (numbers, booleans, simple strings)
- **NO prompts or templates in config files**
- **Each mode should be self-contained**

### 2. Provide Meaningful Progress Updates
- Users should understand what's happening
- Use descriptive content messages
- Include progress values for long operations

### 3. Handle Errors Gracefully
- Wrap risky operations in try-catch blocks
- Always return a useful response, even if something fails
- Use fallback strategies when possible

### 4. Reuse Existing Infrastructure
- Implement all required logic within your mode file (self-contained)
- Follow the established patterns from existing modes
- Don't reinvent search, LLM calling, etc.

### 5. Test Thoroughly
- Test with various types of queries
- Test error conditions
- Test both CLI and web interfaces

### 6. Document Your Configuration
- Explain what each config option does
- Provide sensible defaults
- Consider future extensibility

## Advanced Topics

### Custom Dependencies

If your mode needs special Python packages, create a `requirements.txt` file in your mode's directory:

```
app/modes/your_mode/
├── __init__.py
├── main.py           # Your mode implementation
├── config.py         # Mode-specific config
└── requirements.txt  # Special dependencies
```

Users can install with: `pip install -r app/modes/your_mode/requirements.txt`

### Using External APIs

```python
import requests

def _call_external_api(self, data):
    """Example of calling an external API."""
    try:
        response = requests.post("https://api.example.com/process", json=data)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        # Always handle API failures gracefully
        return {"error": str(e)}
```

### Complex State Management

For modes that need to maintain complex state across multiple steps:

```python
class YourMode(BaseMode):
    def __init__(self, llm_provider, vector_store):
        super().__init__(llm_provider, vector_store)
        self.config = YOUR_MODE_CONFIG
        self.state = {}  # Mode-specific state
    
    def run(self, query: str, chat_history: Optional[List[Dict]] = None) -> Generator[Dict[str, Any], None, str]:
        # Initialize state for this run
        self.state = {
            "query": query,
            "chat_history": chat_history,
            "intermediate_results": [],
            "confidence": 0.0
        }
        
        # Continue with your processing...
```

### Working with Chat History

The `chat_history` parameter contains the recent conversation:

```python
def _analyze_context(self, chat_history):
    """Analyze previous conversation for context."""
    if not chat_history:
        return "No previous context"
    
    recent_messages = chat_history[-4:]  # Last 2 exchanges
    context = ""
    for msg in recent_messages:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role == "user":
            context += f"User asked: {content}\n"
        elif role == "assistant":
            context += f"Assistant replied: {content[:100]}...\n"
    
    return context
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure your imports are correct and all dependencies are available
2. **Config Not Found**: Ensure you added your config to `app/modes/config.py`
3. **Mode Not Listed**: Check that you added it to both `agent_chat.py` and `web_app.py`
4. **Generator Errors**: Make sure your `run` method is a generator (uses `yield`) and returns a string

### Debugging Tips

1. **Use Print Statements**: Add `print()` statements to debug your logic
2. **Test Incrementally**: Start simple and add complexity gradually
3. **Check Logs**: Look at console output for error messages
4. **Test CLI First**: CLI is easier to debug than web interface

### Getting Help

If you're stuck:
1. Look at existing modes for examples
2. Check the base class documentation
3. Test with simple queries first
4. Make sure your development environment is set up correctly

## Examples of Potential Modes

Here are some ideas for modes you could implement:

- **Quote Mode**: Find and format beautiful quotes on a topic
- **Comparison Mode**: Compare how different traditions approach a concept
- **Timeline Mode**: Show historical development of an idea
- **Practice Mode**: Suggest spiritual practices based on a query
- **Meditation Mode**: Generate guided meditations based on passages
- **Story Mode**: Find and retell stories that illustrate a concept
- **Symbol Mode**: Explore symbolic meanings across traditions
- **Question Mode**: Generate thought-provoking questions about a topic

The possibilities are endless! The modes architecture gives you a clean, isolated space to experiment with new ways of interacting with the sacred texts.
