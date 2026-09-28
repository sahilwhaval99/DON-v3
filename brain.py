"""
DON v3.0 brain — Google Gemini via the NEW `google-genai` SDK.

Google deprecated the old `google-generativeai` package; this uses the current
`google-genai` client, which has clean automatic function-calling: you pass
plain Python functions as `tools` and the SDK handles the call/response loop
for you (automatic function calling), so DON can search the web, open apps, etc.

Defensive: if the key or library is missing, chat() returns a clear setup
message instead of crashing.
"""
from __future__ import annotations

import config


class Brain:
    def __init__(self, tools: dict | None = None, memory=None) -> None:
        # tools: {name: callable}; the callables' signatures + docstrings are
        # what the SDK shows to Gemini, so they must be well-typed/documented.
        self.tools = tools or {}
        self.memory = memory
        self._client = None
        self._types = None
        self.model = config.GEMINI_MODEL  # may be replaced by _resolve_model()
        self._init()

    def _init(self) -> None:
        if not config.GEMINI_API_KEY:
            print("[brain] GEMINI_API_KEY not set. Add it to your .env file. "
                  "Get a free key at https://aistudio.google.com/apikey")
            return
        try:
            from google import genai
            from google.genai import types

            self._client = genai.Client(api_key=config.GEMINI_API_KEY)
            self._types = types
            # Resolve a model that actually works with this key/SDK version.
            self.model = self._resolve_model(config.GEMINI_MODEL)
            print(f"[brain] Using model: {self.model}")
        except Exception as exc:
            print(f"[brain] Gemini unavailable ({exc}). "
                  f"Install: pip install google-genai")
            self._client = None

    def _resolve_model(self, preferred: str) -> str:
        """Return a usable model name in the exact format this SDK expects.

        The .list() call returns names like 'models/gemini-2.5-flash'. Some SDK
        versions want the full 'models/...' path. We find the preferred model
        among the key's real models and return its exact name; if not found, we
        fall back to the first flash model available.
        """
        try:
            usable = []
            for m in self._client.models.list():
                name = getattr(m, "name", "") or ""
                actions = (getattr(m, "supported_actions", None)
                           or getattr(m, "supported_generation_methods", None) or [])
                if actions and "generateContent" not in actions:
                    continue
                usable.append(name)  # e.g. 'models/gemini-2.5-flash'

            # Try to match the preferred name (with or without 'models/' prefix).
            pref_short = preferred.split("/")[-1]
            for full in usable:
                if full.split("/")[-1] == pref_short:
                    return full

            # Fall back to the first plain 'flash' text model (avoid tts/image).
            for full in usable:
                short = full.split("/")[-1]
                if "flash" in short and not any(x in short for x in
                                                ("tts", "image", "audio", "vision", "preview")):
                    return full
            # Last resort: any flash, then any usable model.
            for full in usable:
                if "flash" in full.split("/")[-1]:
                    return full
            if usable:
                return usable[0]
        except Exception as exc:
            print(f"[brain] Could not list models ({exc}); using preferred as-is.")
        return preferred

    @property
    def available(self) -> bool:
        return self._client is not None

    def _contents(self, user_text: str) -> str:
        """Build the prompt, prepending a little recent history for context."""
        if self.memory is None:
            return user_text
        try:
            turns = self.memory.recent_turns(limit=6)
            if not turns:
                return user_text
            history_lines = []
            for t in turns:
                if t.get("user"):
                    history_lines.append(f"User: {t['user']}")
                if t.get("assistant"):
                    history_lines.append(f"DON: {t['assistant']}")
            history = "\n".join(history_lines)
            return f"(Recent conversation:\n{history}\n)\nUser: {user_text}"
        except Exception:
            return user_text

    def chat(self, user_text: str) -> str:
        """Return DON's reply, using tools automatically. Never raises."""
        if not self._client:
            return ("My brain isn't connected yet. Please add your free Gemini API "
                    "key to the .env file (GEMINI_API_KEY=...), then restart me. "
                    "Get one at https://aistudio.google.com/apikey.")
        try:
            types = self._types
            tool_fns = list(self.tools.values())
            config_obj = types.GenerateContentConfig(
                system_instruction=config.SYSTEM_PROMPT,
                tools=tool_fns if tool_fns else None,
            )
            # Use the chat interface: recommended for automatic function calling.
            chat = self._client.chats.create(
                model=self.model,
                config=config_obj,
            )
            resp = chat.send_message(self._contents(user_text))
            text = (getattr(resp, "text", None) or "").strip()
            return text or "I processed that but have nothing further to add."
        except Exception as exc:
            msg = str(exc)
            if "NOT_FOUND" in msg or "not found" in msg or "404" in msg:
                return (f"The model '{self.model}' isn't available on your "
                        f"key. {self._suggest_models()}")
            return (f"I hit a problem thinking about that: {exc}. "
                    f"(If this mentions the API key, double-check it in your .env.)")

    def _suggest_models(self) -> str:
        """List models the key can actually use — so we never guess blindly."""
        try:
            names = []
            for m in self._client.models.list():
                actions = getattr(m, "supported_actions", None) or \
                          getattr(m, "supported_generation_methods", []) or []
                name = getattr(m, "name", "")
                if "generateContent" in actions or not actions:
                    short = name.split("/")[-1]
                    if "flash" in short or "pro" in short:
                        names.append(short)
            names = sorted(set(names))[:6]
            if names:
                return ("Try setting DON_GEMINI_MODEL in your .env to one of: "
                        + ", ".join(names))
        except Exception:
            pass
        return ("Set DON_GEMINI_MODEL in your .env to a current model, e.g. "
                "gemini-2.0-flash or gemini-2.5-flash.")


if __name__ == "__main__":
    b = Brain()
    print("Gemini available:", b.available)
    if b.available:
        print(b.chat("In one sentence, who are you?"))
