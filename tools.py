"""
DON v3.0 tools — the actions DON can actually perform.

These are the functions Gemini can call. Each returns a short human-readable
string. All are defensive: failures return a clear message, never crash.

Web search uses DuckDuckGo's free HTML endpoint (no API key). PC-control tools
(open_app, screenshot) only work on the user's own machine.
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


# --------------------------------------------------------------------------- #
# Web search (DuckDuckGo HTML — free, no key)
# --------------------------------------------------------------------------- #
def web_search(query: str, max_results: int = 5) -> str:
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
        for i, t in enumerate(titles[:max_results]):
            title = clean(t)
            snip = clean(snippets[i]) if i < len(snippets) else ""
            if title:
                results.append(f"{title} — {snip}" if snip else title)
        if not results:
            return f"No results found for '{query}'."
        return "Search results:\n" + "\n".join(f"• {r}" for r in results)
    except Exception as exc:
        return f"Web search failed: {exc}"


# --------------------------------------------------------------------------- #
# Weather (Open-Meteo — free, no key)
# --------------------------------------------------------------------------- #
def get_weather(location: str = "") -> str:
    lat, lon = config.WEATHER_LAT, config.WEATHER_LON
    label = "your area"
    try:
        # If a location name is given, geocode it (free Open-Meteo geocoding).
        if location.strip():
            geo_url = ("https://geocoding-api.open-meteo.com/v1/search?count=1&name="
                       + urllib.parse.quote(location.strip()))
            import json
            with urllib.request.urlopen(geo_url, timeout=15) as r:
                g = json.loads(r.read().decode())
            if g.get("results"):
                lat = g["results"][0]["latitude"]
                lon = g["results"][0]["longitude"]
                label = g["results"][0]["name"]
        import json
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


# --------------------------------------------------------------------------- #
# Open apps / websites
# --------------------------------------------------------------------------- #
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
    name = (name or "").strip().lower()
    if not name:
        return "Which app or website should I open?"
    try:
        # Website?
        if name in _WEBSITES or name.startswith("http") or "." in name:
            import webbrowser
            url = _WEBSITES.get(name, name if name.startswith("http") else f"https://{name}")
            webbrowser.open(url)
            return f"Opening {name} in your browser."
        # App
        if OS_NAME == "Windows":
            os.system(_WIN_APPS.get(name, f"start {name}"))
        elif OS_NAME == "Darwin":
            subprocess.Popen(["open", "-a", name])
        else:
            subprocess.Popen([name])
        return f"Opening {name}."
    except Exception as exc:
        return f"Couldn't open {name}: {exc}"


# --------------------------------------------------------------------------- #
# Screenshot
# --------------------------------------------------------------------------- #
def take_screenshot() -> str:
    try:
        import pyautogui
        fname = _dt.datetime.now().strftime("shot_%Y%m%d_%H%M%S.png")
        path = config.SCREENSHOTS_DIR / fname
        pyautogui.screenshot(str(path))
        return f"Screenshot saved to {path}."
    except Exception as exc:
        return f"Couldn't take a screenshot: {exc}"


# --------------------------------------------------------------------------- #
# Reminders (stored by the caller-provided memory; here we just format)
# --------------------------------------------------------------------------- #
def make_reminder_tool(memory):
    """Returns an add_reminder(text, when) bound to the given memory store."""
    def add_reminder(text: str, when: str = "") -> str:
        due = _parse_when(when)
        memory.add_reminder(due, text)
        when_str = due.strftime("%I:%M %p on %d %b")
        return f"Reminder set: '{text}' at {when_str}."
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
    # Web/weather need internet; safe to try.
    print(web_search("python news")[:200])
    print(_parse_when("in 10 min"))
    print(_parse_when("5pm"))
