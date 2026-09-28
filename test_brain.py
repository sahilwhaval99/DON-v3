"""
DON v3.0 — Layer 1 test (run this FIRST).

A tiny command-line chat so you can confirm the Gemini brain works and can use
tools (web search, weather, etc.) BEFORE we build the full dashboard.

Usage:
    python test_brain.py

Type messages; type 'quit' to exit. Try:
    - who are you?
    - what's the weather in London?
    - search for the latest news about AI
    - what time is it in Tokyo right now?   (forces a web search)
"""
from __future__ import annotations

from assistant import Assistant


def main() -> None:
    print("=" * 56)
    print("  DON v3.0 — brain test")
    print("=" * 56)

    a = Assistant()
    if not a.brain_ready:
        print("\n[!] Gemini is NOT connected.")
        print("    1. Get a free key: https://aistudio.google.com/apikey")
        print("    2. Put it in a file named .env next to this script:")
        print("         GEMINI_API_KEY=your_key_here")
        print("    3. Run again: python test_brain.py")
        return

    print("\nDON is online. Type a message (or 'quit' to exit).\n")
    while True:
        try:
            text = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if text.lower() in {"quit", "exit", "bye"}:
            print("DON: Goodbye, sir.")
            break
        if not text:
            continue
        print("DON:", a.handle(text), "\n")


if __name__ == "__main__":
    main()
