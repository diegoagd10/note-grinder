from datetime import datetime, timezone

from src import clock
from src.persistence import Persistence

_STALE_AFTER = 30.0

_SCHEMA = """
    CREATE TABLE IF NOT EXISTS processor_state (
        id        INTEGER PRIMARY KEY CHECK(id = 1),
        status    TEXT,
        pid       INTEGER,
        last_seen TEXT
    )
"""

_HEARTBEAT = """
    INSERT OR REPLACE INTO processor_state(id, status, pid, last_seen)
    VALUES(1, 'running', ?, ?)
"""

_MARK_STOPPED = "UPDATE processor_state SET status = 'stopped' WHERE id = 1"

_SELECT = "SELECT status, last_seen FROM processor_state WHERE id = 1"


class ProcessorState:
    def __init__(self, db: Persistence):
        self._db = db
        db.define(_SCHEMA)

    def heartbeat(self, pid: int) -> None:
        self._db.execute(_HEARTBEAT, (pid, clock.now()))

    def mark_stopped(self) -> None:
        self._db.execute(_MARK_STOPPED)

    def is_healthy(self) -> bool:
        rows = self._db.execute(_SELECT)
        if not rows:
            return False
        status, last_seen = rows[0]
        if status != "running":
            return False
        last_seen_dt = datetime.fromisoformat(last_seen)
        age = (datetime.now(timezone.utc) - last_seen_dt).total_seconds()
        return age <= _STALE_AFTER
