#!/usr/bin/env python3
"""
CLI entrypoint for Sacred Texts Agent
"""

from app.agent.core import SacredTextsAgent


def main() -> None:
    agent = SacredTextsAgent()
    agent.run()


if __name__ == "__main__":
    main()


