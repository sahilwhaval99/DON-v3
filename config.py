"""
DON v3.0 — configuration.

Reads settings from environment variables / a local .env file.
The only REQUIRED setting is GEMINI_API_KEY (get one free at
https://aistudio.google.com/apikey). Everything else has sane defaults.
"""
from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
SCREENSHOTS_DIR = DATA_DIR / "screenshots"
for _d in (DATA_DIR, SCREENSHOTS_DIR):
    _d.mkdir(parents=True, exist_ok=True)

SQLITE_PATH = DATA_DIR / "don3.db"

# ---------------- Gemini (the brain) ----------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
# Fast + free model. Can bump to "gemini-1.5-pro" for deeper answers.
GEMINI_MODEL = os.getenv("DON_GEMINI_MODEL", "gemini-1.5-flash")

SYSTEM_PROMPT = (
    "You are DON, a highly capable personal AI assistant, similar to JARVIS. "
    "You are witty, concise, and helpful, with a polite, slightly British tone. "
    "You can search the web, control the user's PC, and manage tasks. "
    "When you use tools or search results, ground your answer in them and cite "
    "sources briefly. Never invent facts; if unsure, say so."
)

# ---------------- Web server ----------------
SERVER_HOST = os.getenv("DON_SERVER_HOST", "127.0.0.1")
SERVER_PORT = int(os.getenv("DON_SERVER_PORT", "8000"))
AUTO_OPEN_BROWSER = os.getenv("DON_AUTO_OPEN_BROWSER", "true").lower() == "true"

# ---------------- Skills ----------------
WEATHER_LAT = float(os.getenv("DON_WEATHER_LAT", "12.9716"))
WEATHER_LON = float(os.getenv("DON_WEATHER_LON", "77.5946"))

THEME = {
    "bg": "#0a0e17", "red": "#ff3b3b", "blue": "#00d4ff", "text": "#e0e0e0",
}
