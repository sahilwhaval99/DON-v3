"""
DON v3.0 — entry point.

Starts the dashboard server and opens your browser.

Run:
    python main.py

Then the dashboard opens at http://127.0.0.1:8000
"""
from __future__ import annotations

import threading
import time
import webbrowser

import config


def _open_browser():
    if not config.AUTO_OPEN_BROWSER:
        return
    time.sleep(1.5)
    try:
        webbrowser.open(f"http://{config.SERVER_HOST}:{config.SERVER_PORT}")
    except Exception:
        pass


def main():
    try:
        import uvicorn
    except Exception:
        raise SystemExit("Install dependencies first: pip install -r requirements.txt")

    print("=" * 56)
    print("  DON v3.0 — AI Assistant")
    print(f"  Dashboard: http://{config.SERVER_HOST}:{config.SERVER_PORT}")
    print("=" * 56)

    threading.Thread(target=_open_browser, daemon=True).start()
    uvicorn.run("server:app", host=config.SERVER_HOST, port=config.SERVER_PORT,
                log_level="info")


if __name__ == "__main__":
    main()
