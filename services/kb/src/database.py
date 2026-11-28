"""Connections and migrations. Connection settings come from DATABASE_URL or the PG* variables."""

import os
import threading
from pathlib import Path

import psycopg
from psycopg.rows import DictRow, dict_row

MIGRATIONS = Path(__file__).parent / "migrations"
# Any constant works; it stops two replicas from migrating at the same time
LOCK_KEY = 815_006

Connection = psycopg.Connection[DictRow]


class Database:
    def __init__(self, dsn: str | None = None) -> None:
        self._dsn = dsn if dsn is not None else os.environ.get("DATABASE_URL", "")
        self._migrated = False
        self._lock = threading.Lock()

    def _open(self) -> Connection:
        return psycopg.connect(self._dsn, connect_timeout=5, row_factory=dict_row)

    def connect(self) -> Connection:
        """A connection to a migrated database. Commits when the `with` block succeeds."""
        if not self._migrated:
            with self._lock:
                if not self._migrated:
                    self.migrate()
                    self._migrated = True
        return self._open()

    def migrate(self) -> list[str]:
        applied: list[str] = []
        with self._open() as connection:
            connection.execute("SELECT pg_advisory_xact_lock(%s)", (LOCK_KEY,))
            connection.execute(
                "CREATE TABLE IF NOT EXISTS schema_migrations (name text PRIMARY KEY)"
            )
            done = {r["name"] for r in connection.execute("SELECT name FROM schema_migrations")}
            for script in sorted(MIGRATIONS.glob("*.sql")):
                if script.name not in done:
                    connection.execute(script.read_bytes())
                    connection.execute(
                        "INSERT INTO schema_migrations (name) VALUES (%s)", (script.name,)
                    )
                    applied.append(script.name)
        return applied
