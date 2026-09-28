"""
DON v3.0 assistant — wires the Gemini brain to the tools and memory.

Single entry point: Assistant.handle(text) -> str. Used by both the CLI test
(test_brain.py) and the web server, so behaviour is identical everywhere.
"""
from __future__ import annotations

import config
from brain import Brain
from memory import Memory
import tools as T


class Assistant:
    def __init__(self) -> None:
        self.memory = Memory()

        # Register the tools DON can use. add_reminder is bound to memory.
        self.tools = {
            "web_search": T.web_search,
            "get_weather": T.get_weather,
            "open_app": T.open_app,
            "take_screenshot": T.take_screenshot,
            "add_reminder": T.make_reminder_tool(self.memory),
        }
        self.brain = Brain(tools=self.tools, memory=self.memory)

    @property
    def brain_ready(self) -> bool:
        return self.brain.available

    # Keywords that suggest a tool/action is needed (use non-stream tool path).
    _TOOL_HINTS = (
        "search", "google", "look up", "news", "latest", "weather", "temperature",
        "open ", "launch", "screenshot", "remind", "reminder", "price", "stock",
        "who won", "today", "current", "right now",
    )

    def _needs_tool(self, text: str) -> bool:
        t = text.lower()
        return any(h in t for h in self._TOOL_HINTS)

    def handle(self, text: str) -> str:
        text = (text or "").strip()
        if not text:
            return "I'm listening."
        reply = self.brain.chat(text)
        self.memory.log_turn(text, reply)
        return reply

    def handle_stream(self, text: str):
        """Yield the reply in chunks for fast, live output.

        For tool-needing requests we fall back to the full (non-stream) path so
        web search / actions still work, then yield the whole answer at once.
        For plain conversation we stream token-by-token (feels instant).
        """
        text = (text or "").strip()
        if not text:
            yield "I'm listening."
            return
        if self._needs_tool(text):
            reply = self.brain.chat(text)
            self.memory.log_turn(text, reply)
            yield reply
            return
        collected = []
        for piece in self.brain.chat_stream(text):
            collected.append(piece)
            yield piece
        self.memory.log_turn(text, "".join(collected))


if __name__ == "__main__":
    a = Assistant()
    print("Brain ready:", a.brain_ready)
