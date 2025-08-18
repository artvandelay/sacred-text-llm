#!/usr/bin/env python3
"""
Thin wrapper to preserve `python chat.py` entrypoint after reorg.
"""

from app.core.cli_chat import main


if __name__ == "__main__":
    main()
