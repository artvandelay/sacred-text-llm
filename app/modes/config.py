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

# Contemplative Mode
CONTEMPLATIVE_CONFIG = {
    "max_results": 1,
}

# Koan Generator Mode (future)
KOAN_GENERATOR_CONFIG = {
    "style": "zen",
    "temperature": 0.9,
    "examples_to_analyze": 5,
}

# Add more mode configs as needed...
