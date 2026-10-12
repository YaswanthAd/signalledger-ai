"""SQLite report store. Immutable payloads with transactional idempotency."""
from contextlib import contextmanager
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


class Conflict(Exception):
    pass


class Store:
    def __init__(self, path: str):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("""CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY, idem_key TEXT NOT NULL UNIQUE,
                digest TEXT NOT NULL, created_at TEXT NOT NULL, payload TEXT NOT NULL
            )""")

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.path, timeout=15)
        conn.row_factory = sqlite3.Row
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    @staticmethod
    def digest(request: dict) -> str:
        return hashlib.sha256(json.dumps(request, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()

    def cached(self, key: str, request: dict):
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM reports WHERE idem_key=?", (key,)).fetchone()
        if row:
            if row["digest"] != self.digest(request):
                raise Conflict("Idempotency key already used for a different request")
            return json.loads(row["payload"])

    def save(self, key: str, request: dict, payload: dict):
        report = {**payload, "id": str(uuid4()), "created_at": datetime.now(timezone.utc).isoformat(),
                  "request_digest": self.digest(request), "request": request}
        with self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("SELECT * FROM reports WHERE idem_key=?", (key,)).fetchone()
            if row:
                if row["digest"] != self.digest(request):
                    raise Conflict("Idempotency key already used for a different request")
                return json.loads(row["payload"])
            conn.execute("INSERT INTO reports VALUES (?,?,?,?,?)", (
                report["id"], key, self.digest(request), report["created_at"],
                json.dumps(report, allow_nan=False)))
        return report

    def get(self, report_id: str):
        with self.connect() as conn:
            row = conn.execute("SELECT payload FROM reports WHERE id=?", (report_id,)).fetchone()
        return json.loads(row["payload"]) if row else None

    def recent(self):
        with self.connect() as conn:
            rows = conn.execute("SELECT id, created_at FROM reports ORDER BY created_at DESC LIMIT 30").fetchall()
        return [dict(row) for row in rows]
