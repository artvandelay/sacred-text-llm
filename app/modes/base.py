"""
Base class for all experimental modes.

This module defines the contract that all modes must follow.
"""

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
