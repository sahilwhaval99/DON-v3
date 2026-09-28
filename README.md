# DON v3.0 — Cloud-Powered AI Assistant

A genuinely capable personal assistant powered by **Google Gemini** (free tier),
with real **web search**, **PC control**, and a red/blue dashboard.

> This is a rebuild of DON focused on *actually working*. We build and test in
> layers. **Layer 1 (this step) = the brain.** Test it before we add the UI.

---

## Layer 1: Test the brain (do this first)

### 1. Get a free Gemini API key
- Go to **https://aistudio.google.com/apikey**
- Sign in with Google → **Create API key** → copy it
- (Free tier — no credit card needed)

### 2. Set up
```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Add your key
Copy `.env.example` to `.env` and paste your key:
```
GEMINI_API_KEY=your_key_here
```
```bat
copy .env.example .env
notepad .env
```

### 4. Run the brain test
```bat
python test_brain.py
```

Try these:
- `who are you?`
- `what's the weather in London?`
- `search for the latest AI news`
- `open youtube`

If DON answers intelligently and can search the web — **Layer 1 works**, and we
build the full dashboard next.

---

## What's built
| File | Purpose |
|------|---------|
| `brain.py` | Gemini brain with tool-calling |
| `tools.py` | web search, weather, open apps/sites, screenshot, reminders |
| `memory.py` | SQLite conversation history + reminders |
| `assistant.py` | wires brain + tools + memory |
| `test_brain.py` | **Layer 1 CLI test** |

## Coming next (after Layer 1 is confirmed)
- FastAPI server + WebSocket dashboard (red/blue UI)
- More tools; optional voice
