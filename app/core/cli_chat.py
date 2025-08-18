#!/usr/bin/env python3
"""
CLI entrypoint for Sacred Texts Chat
"""

from app.chat.core import SacredTextsChat


def main() -> None:
    chat = SacredTextsChat()
    chat.run()


if __name__ == "__main__":
    main()


