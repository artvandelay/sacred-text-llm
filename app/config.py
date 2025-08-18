"""
Unified application configuration.

This module re-exports environment-driven settings for providers,
vector stores, and agent behavior. Prefer importing from app.config
across the codebase to avoid fragmentation.
"""

# For now, reuse the existing agent config implementation.
# Future work: consolidate any duplicated settings here and delete
# legacy config modules.
from app.agent.config import *  # noqa: F401,F403


