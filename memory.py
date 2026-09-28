"""
DON v3.0 memory — simple, reliable SQLite store.

Keeps conversation history (for context) and reminders. Kept intentionally
small and dependency-free (stdlib sqlite3) so it always works.
"""
from __future__ import annotations

import datetime as _dt
import sqlite3
import threading

import config


class Memory:
    def __init__(self, path=None) -> None:
        self.path = str(path or config.SQLITE_PATH)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init()

    def _init(self) -> None:
        with self._lock, self._conn:
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS conversation_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT NOT NULL,
                    user TEXT,
                    assistant TEXT
                );
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    due TEXT NOT NULL,
                    message TEXT NOT NULL,
                    done INTEGER NOT NULL DEFAULT 0
                );
                """
            )

    def log_turn(self, user_text: str, assistant_text: str) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT INTO conversation_log(ts, user, assistant) VALUES(?,?,?)",
                (_dt.datetime.now().isoformat(timespec="seconds"), user_text, assistant_text),
            )

    def recent_turns(self, limit: int = 6) -> list[dict]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT user, assistant FROM conversation_log ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in reversed(rows)]

    def add_reminder(self, due: _dt.datetime, message: str) -> int:
        with self._lock, self._conn:
            cur = self._conn.execute(
                "INSERT INTO reminders(due, message) VALUES(?, ?)",
                (due.isoformat(timespec="seconds"), message),
            )
            return int(cur.lastrowid)

    def pending_reminders(self) -> list[dict]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM reminders WHERE done=0 ORDER BY due"
            ).fetchall()
        return [dict(r) for r in rows]

    def due_reminders(self, now: _dt.datetime | None = None) -> list[dict]:
        now = now or _dt.datetime.now()
        with self._lock, self._conn:
            rows = self._conn.execute(
                "SELECT * FROM reminders WHERE done=0 AND due<=?",
                (now.isoformat(timespec="seconds"),),
            ).fetchall()
            ids = [r["id"] for r in rows]
            if ids:
                self._conn.executemany("UPDATE reminders SET done=1 WHERE id=?",
                                       [(i,) for i in ids])
        return [dict(r) for r in rows]


if __name__ == "__main__":
    import tempfile, os
    m = Memory(os.path.join(tempfile.mkdtemp(), "t.db"))
    m.log_turn("hi", "Good day.")
    assert m.recent_turns()[-1]["assistant"] == "Good day."
    m.add_reminder(_dt.datetime.now() - _dt.timedelta(seconds=1), "test")
    assert m.due_reminders()
    print("memory self-test: OK")
