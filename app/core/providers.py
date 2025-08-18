"""
LLM Providers for Sacred Texts Chat
Simple, clean provider system - easy to understand and extend
"""

import os
import re
from typing import List, Dict

import logging
import ollama
import openai


class LLMProvider:
    """
    Base class for LLM providers
    Makes it easy to add new providers later
    """
    
    def generate_response(self, messages: List[Dict[str, str]], model: str) -> str:
        """
        Generate a response from the LLM
        
        Args:
            messages: List of {"role": "user/system", "content": "text"}
            model: Model name to use
            
        Returns:
            Generated response text
        """
        raise NotImplementedError("Each provider must implement this method")


class OllamaProvider(LLMProvider):
    """
    Local Ollama provider - uses your local models
    Perfect for Phase 1: everything local and private
    """
    
    def generate_response(self, messages: List[Dict[str, str]], model: str) -> str:
        try:
            response = ollama.chat(model=model, messages=messages)
            content = response["message"]["content"]
            content = re.sub(r"<think>[\s\S]*?</think>\n?", "", content)
            return content.strip()
        except Exception as e:
            logging.exception("OllamaProvider error")
            raise


class OpenRouterProvider(LLMProvider):
    """
    OpenRouter provider - access to GPT-4, Claude, etc.
    Perfect for Phase 2: better models while keeping data local
    """
    
    def __init__(self):
        # Get API key from environment
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "OpenRouter API key required!\n"
                "Set it with: export OPENROUTER_API_KEY='your-key-here'"
            )
        
        # Set up OpenAI client pointed at OpenRouter
        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url="https://openrouter.ai/api/v1"
        )
    
    def generate_response(self, messages: List[Dict[str, str]], model: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=8000,
            )
            return response.choices[0].message.content
        except Exception:
            logging.exception("OpenRouterProvider error")
            raise


def create_provider(provider_name: str) -> LLMProvider:
    """
    Factory function to create the right provider
    Makes switching providers super easy
    """
    
    if provider_name == "ollama":
        return OllamaProvider()
    
    elif provider_name == "openrouter":
        return OpenRouterProvider()
    
    else:
        raise ValueError(
            f"Unknown provider: {provider_name}\n"
            f"Available options: 'ollama', 'openrouter'"
        )
