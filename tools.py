"""
DON v3.0 tools — the actions DON can perform.

These functions are passed directly to the Gemini SDK for *automatic function
calling*. That means the SDK reads each function's NAME, TYPE HINTS, and
DOCSTRING to decide when and how to call it — so those must stay clear and
accurate. Each returns a short human-readable string. All are defensive.

Web search uses DuckDuckGo's free HTML endpoint (no API key). PC-control tools
only work on the user's own machine.
"""
from __future__ import annotations

import datetime as _dt
import os
import platform
import re
import subprocess
import urllib.parse
import urllib.request

import config

OS_NAME = platform.system()  # 'Windows', 'Linux', 'Darwin'


def web_search(query: str) -> str:
    """Search the live internet and return the top results.

    Use this for anything current, recent, or factual that you don't already
    know: news, prices, events, people, "search for X", "what's the latest ...".

    Args:
        query: The search query, e.g. "latest AI news" or "population of Japan".
    """
    query = (query or "").strip()
    if not query:
        return "No search query provided."
    try:
        url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(query)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode(errors="replace")
        titles = re.findall(r'class="result__a"[^>]*>(.*?)</a>', html, re.S)
        snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</a>', html, re.S)

        def clean(x):
            return re.sub(r"<[^>]+>", "", x).replace("&amp;", "&").strip()

        results = []
        for i, t in enumerate(titles[:5]):
            title = clean(t)
            snip = clean(snippets[i]) if i < len(snippets) else ""
            if title:
                results.append(f"{title} — {snip}" if snip else title)
        if not results:
            return f"No results found for '{query}'."
        return "Search results:\n" + "\n".join(f"• {r}" for r in results)
    except Exception as exc:
        return f"Web search failed: {exc}"


def get_weather(location: str = "") -> str:
    """Get the current weather for a location.

    Args:
        location: City name, e.g. "London". If empty, uses the user's default.
    """
    lat, lon = config.WEATHER_LAT, config.WEATHER_LON
    label = "your area"
    try:
        import json
        if location.strip():
            geo_url = ("https://geocoding-api.open-meteo.com/v1/search?count=1&name="
                       + urllib.parse.quote(location.strip()))
            with urllib.request.urlopen(geo_url, timeout=15) as r:
                g = json.loads(r.read().decode())
            if g.get("results"):
                lat = g["results"][0]["latitude"]
                lon = g["results"][0]["longitude"]
                label = g["results"][0]["name"]
        url = (f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
               f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m")
        with urllib.request.urlopen(url, timeout=15) as r:
            data = json.loads(r.read().decode())
        c = data.get("current", {})
        return (f"Weather in {label}: {c.get('temperature_2m')}°C, "
                f"{c.get('relative_humidity_2m')}% humidity, "
                f"wind {c.get('wind_speed_10m')} km/h.")
    except Exception as exc:
        return f"Couldn't get weather: {exc}"


_WEBSITES = {
    "youtube": "https://youtube.com", "google": "https://google.com",
    "gmail": "https://mail.google.com", "github": "https://github.com",
    "chatgpt": "https://chat.openai.com", "maps": "https://maps.google.com",
    "whatsapp": "https://web.whatsapp.com",
}
_WIN_APPS = {
    "notepad": "notepad", "calculator": "calc", "calc": "calc",
    "paint": "mspaint", "explorer": "explorer", "cmd": "cmd",
    "settings": "start ms-settings:", "camera": "start microsoft.windows.camera:",
}


def open_app(name: str) -> str:
    """Open an application or website on the user's computer.

    Args:
        name: What to open, e.g. "notepad", "calculator", "youtube", "gmail".
    """
    name = (name or "").strip().lower()
    if not name:
        return "Which app or website should I open?"
    try:
        if name in _WEBSITES or name.startswith("http") or "." in name:
            import webbrowser
            url = _WEBSITES.get(name, name if name.startswith("http") else f"https://{name}")
            webbrowser.open(url)
            return f"Opening {name} in your browser."
        if OS_NAME == "Windows":
            os.system(_WIN_APPS.get(name, f"start {name}"))
        elif OS_NAME == "Darwin":
            subprocess.Popen(["open", "-a", name])
        else:
            subprocess.Popen([name])
        return f"Opening {name}."
    except Exception as exc:
        return f"Couldn't open {name}: {exc}"


def take_screenshot() -> str:
    """Capture a screenshot of the user's screen and save it to disk."""
    try:
        import pyautogui
        fname = _dt.datetime.now().strftime("shot_%Y%m%d_%H%M%S.png")
        path = config.SCREENSHOTS_DIR / fname
        pyautogui.screenshot(str(path))
        return f"Screenshot saved to {path}."
    except Exception as exc:
        return f"Couldn't take a screenshot: {exc}"


# Reminder tool is created with memory bound in; see make_reminder_tool.
def make_reminder_tool(memory):
    """Return an add_reminder(text, when) function bound to the memory store."""
    def add_reminder(text: str, when: str = "") -> str:
        """Save a reminder or note for the user.

        Args:
            text: What to be reminded about, e.g. "call mom".
            when: When, e.g. "5pm" or "in 10 minutes". Defaults to 1 hour.
        """
        due = _parse_when(when)
        memory.add_reminder(due, text)
        return f"Reminder set: '{text}' at {due.strftime('%I:%M %p on %d %b')}."
    return add_reminder


def _parse_when(when: str) -> _dt.datetime:
    now = _dt.datetime.now()
    when = (when or "").lower()
    rel = re.search(r"in\s+(\d+)\s*(min|hour|hr)", when)
    if rel:
        n = int(rel.group(1))
        return now + (_dt.timedelta(minutes=n) if rel.group(2).startswith("min")
                      else _dt.timedelta(hours=n))
    at = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", when)
    if at:
        h = int(at.group(1)); m = int(at.group(2) or 0); ap = at.group(3)
        if ap == "pm" and h < 12: h += 12
        if ap == "am" and h == 12: h = 0
        due = now.replace(hour=h % 24, minute=m, second=0, microsecond=0)
        return due if due > now else due + _dt.timedelta(days=1)
    return now + _dt.timedelta(hours=1)


if __name__ == "__main__":
    print(_parse_when("in 10 min"))
    print(_parse_when("5pm"))
    print(open_app(""))
