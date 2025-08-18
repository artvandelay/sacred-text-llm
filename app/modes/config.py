"""
Mode-specific configuration.

DEPRECATED: Most settings should go in app.config and be environment-driven.
Only put mode-specific UI/behavior settings here that don't belong in main config.
"""

# Contemplative Mode - UI specific
CONTEMPLATIVE_CONFIG = {
    "max_results": 1,  # Only show 1 passage for contemplation
}

# Future mode-specific configs (non-environment settings only)
KOAN_GENERATOR_CONFIG = {
    "style": "zen",
    "temperature": 0.9,
    "examples_to_analyze": 5,
}

# Note: All performance/behavior settings (iterations, thresholds, etc.) 
# should be in app.config and environment-driven, not hardcoded here.
