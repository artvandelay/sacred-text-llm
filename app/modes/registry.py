"""
Mode Registry - Single source of truth for all available modes.

This registry is imported by both CLI and web interfaces to avoid duplication.
"""

from app.modes.deep_research import DeepResearchMode
from app.modes.contemplative import ContemplativeMode
from app.modes.content_creator import ContentCreatorMode


# Single registry of all available modes
MODES = {
    "deep_research": {
        "class": DeepResearchMode,
        "description": "Comprehensive research with iterative planning and synthesis",
        "aliases": ["research", "deep"]
    },
    "contemplative": {
        "class": ContemplativeMode,
        "description": "Reflective mode that offers a passage and thoughtful question",
        "aliases": ["contemplate", "reflect"]
    },
    "content_creator": {
        "class": ContentCreatorMode,
        "description": "Generates an engaging tweet with auto-critique",
        "aliases": ["tweet", "social"]
    }
}


def get_mode(mode_name: str, llm_provider, vector_store):
    """
    Get a mode instance by name or alias.
    
    Args:
        mode_name: Name or alias of the mode
        llm_provider: LLM provider instance
        vector_store: Vector store instance
        
    Returns:
        Mode instance
        
    Raises:
        ValueError: If mode not found
    """
    # Check direct name first
    if mode_name in MODES:
        return MODES[mode_name]["class"](llm_provider, vector_store)
    
    # Check aliases
    for name, info in MODES.items():
        if mode_name in info.get("aliases", []):
            return info["class"](llm_provider, vector_store)
    
    # Not found
    available = list(MODES.keys())
    raise ValueError(f"Unknown mode: {mode_name}. Available: {available}")


def list_modes():
    """Get a formatted list of available modes."""
    lines = []
    for name, info in MODES.items():
        aliases = info.get("aliases", [])
        alias_str = f" (aliases: {', '.join(aliases)})" if aliases else ""
        lines.append(f"  {name}: {info['description']}{alias_str}")
    return "\n".join(lines)
