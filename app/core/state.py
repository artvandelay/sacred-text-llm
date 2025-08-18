"""
Shared data structures for Sacred Texts LLM.

Contains only the data structures actually used by the current modes system.
Legacy agent state management has been removed.
"""

import json
import time
from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class SearchResult:
    """Container for search results with metadata"""
    query: str
    documents: List[str]
    metadatas: List[Dict[str, Any]]
    distances: List[float]
    timestamp: float = field(default_factory=time.time)


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
