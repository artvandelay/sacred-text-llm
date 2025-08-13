#!/usr/bin/env python3
"""
Thin wrapper to preserve `python agent_chat.py` entrypoint after reorg.
"""

from app.agent.cli import main


if __name__ == "__main__":
    main()
