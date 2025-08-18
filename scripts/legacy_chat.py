#!/usr/bin/env python3
"""
Legacy entrypoint - redirects to the simple chat interface.
This file maintains backward compatibility for existing workflows.
"""

from scripts.chat import main

if __name__ == "__main__":
    main()
