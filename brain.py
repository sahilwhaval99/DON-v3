"""
DON v3.0 brain — Google Gemini with function-calling (agent tools).

This is the core upgrade over v2.0: instead of a dumb local model, DON now uses
Gemini and can CALL TOOLS (web search, weather, open apps, etc.). Gemini decides
when to use a tool, we run it, and feed the result back so DON answers with real,
current information.

Design:
* If GEMINI_API_KEY is missing or the library isn't installed, chat() returns a
  clear setup message instead of crashing.
* Tools are plain Python functions registered in a registry; the server passes
  in the actual implementations (so web/pc tools can be swapped/tested).
"""
from __future__ import annotations

import json

import config


class Brain:
    def __init__(self, tools: dict | None = None, memory=None) -> None:
        """
        tools: mapping of {tool_name: callable(**kwargs) -> str}
        memory: optional object with recent_turns()/log/recall for context
        """
        self.tools = tools or {}
        self.memory = memory
        self._model = None
        self._genai = None
        self._init()

    def _init(self) -> None:
        if not config.GEMINI_API_KEY:
            print("[brain] GEMINI_API_KEY not set. Add it to your .env file. "
                  "Get a free key at https://aistudio.google.com/apikey")
            return
        try:
            import google.generativeai as genai

            genai.configure(api_key=config.GEMINI_API_KEY)
            self._genai = genai
            self._model = genai.GenerativeModel(
                model_name=config.GEMINI_MODEL,
                system_instruction=config.SYSTEM_PROMPT,
                tools=list(self._tool_declarations()) or None,
            )
        except Exception as exc:
            print(f"[brain] Gemini unavailable ({exc}). "
                  f"Install: pip install google-generativeai")
            self._model = None

    @property
    def available(self) -> bool:
        return self._model is not None

    def _tool_declarations(self):
        """Describe our tools to Gemini so it knows when to call them."""
        # Keep declarations aligned with the tool functions the server registers.
        specs = {
            "web_search": {
                "description": "Search the live internet for current information "
                               "and return the top results. Use for anything recent, "
                               "factual lookups, news, prices, or 'search for X'.",
                "params": {"query": "The search query"},
            },
            "get_weather": {
                "description": "Get the current weather for a location.",
                "params": {"location": "City name, optional; defaults to user's city"},
            },
            "open_app": {
                "description": "Open an application or website on the user's PC.",
                "params": {"name": "App or website name, e.g. 'notepad', 'youtube'"},
            },
            "take_screenshot": {
                "description": "Capture a screenshot of the user's screen.",
                "params": {},
            },
            "add_reminder": {
                "description": "Save a reminder/note for the user.",
                "params": {"text": "The reminder text", "when": "When, e.g. '5pm' or 'in 10 min'"},
            },
        }
        declarations = []
        for name, spec in specs.items():
            if name not in self.tools:
                continue
            props = {k: {"type": "string", "description": v}
                     for k, v in spec["params"].items()}
            declarations.append({
                "name": name,
                "description": spec["description"],
                "parameters": {
                    "type": "object",
                    "properties": props,
                    "required": list(props.keys()) if name != "get_weather" else [],
                },
            })
        return declarations

    def chat(self, user_text: str) -> str:
        """Return DON's reply, using tools when Gemini decides to. Never raises."""
        if not self._model:
            return ("My brain isn't connected yet. Please add your free Gemini API "
                    "key to the .env file (GEMINI_API_KEY=...), then restart me. "
                    "Get one at https://aistudio.google.com/apikey.")
        try:
            chat = self._model.start_chat(history=self._history())
            response = chat.send_message(user_text)

            # Handle up to a few rounds of tool calls.
            for _ in range(5):
                calls = self._extract_calls(response)
                if not calls:
                    break
                tool_results = []
                for call in calls:
                    name = call["name"]
                    args = call["args"]
                    fn = self.tools.get(name)
                    result = fn(**args) if fn else f"(no tool named {name})"
                    tool_results.append({"name": name, "response": {"result": str(result)}})
                # Send results back to Gemini for a final natural-language answer.
                response = chat.send_message(
                    [self._genai.protos.Part(function_response=self._genai.protos.FunctionResponse(
                        name=tr["name"], response=tr["response"])) for tr in tool_results]
                )
            return self._text_of(response)
        except Exception as exc:
            return f"I hit a problem thinking about that: {exc}"

    # -- helpers ------------------------------------------------------- #
    def _history(self) -> list:
        hist = []
        if self.memory is not None:
            try:
                for turn in self.memory.recent_turns(limit=6):
                    if turn.get("user"):
                        hist.append({"role": "user", "parts": [turn["user"]]})
                    if turn.get("assistant"):
                        hist.append({"role": "model", "parts": [turn["assistant"]]})
            except Exception:
                pass
        return hist

    @staticmethod
    def _extract_calls(response) -> list[dict]:
        calls = []
        try:
            for cand in response.candidates:
                for part in cand.content.parts:
                    fc = getattr(part, "function_call", None)
                    if fc and fc.name:
                        calls.append({"name": fc.name, "args": dict(fc.args or {})})
        except Exception:
            pass
        return calls

    @staticmethod
    def _text_of(response) -> str:
        try:
            return (response.text or "").strip()
        except Exception:
            # Fallback: stitch text parts together.
            out = []
            try:
                for cand in response.candidates:
                    for part in cand.content.parts:
                        if getattr(part, "text", None):
                            out.append(part.text)
            except Exception:
                pass
            return (" ".join(out).strip()
                    or "I processed that but have nothing further to add.")


if __name__ == "__main__":
    b = Brain()
    print("Gemini available:", b.available)
    if b.available:
        print(b.chat("In one sentence, who are you?"))
