from dataclasses import dataclass
from pathlib import Path

from src import clock
from src.persistence import Persistence

_SCHEMA = """
    CREATE TABLE IF NOT EXISTS queue_items (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        note_path  TEXT    NOT NULL,
        status     TEXT    NOT NULL DEFAULT 'queued',
        error      TEXT,
        created_at TEXT    NOT NULL,
        updated_at TEXT    NOT NULL
    )
"""

# Guards against duplicate active work: a path already queued or in-flight
# must not produce a second row. A 'done' row allows re-enqueueing.
_ENQUEUE = """
    INSERT INTO queue_items (note_path, status, created_at, updated_at)
    SELECT ?, 'queued', ?, ?
    WHERE NOT EXISTS (
        SELECT 1 FROM queue_items
        WHERE note_path = ? AND status IN ('queued', 'processing')
    )
"""

# Atomically promotes queued *and* already-processing items up to the limit.
# Re-selecting processing items recovers work that was claimed before a crash.
_CLAIM = """
    UPDATE queue_items
    SET status = 'processing', updated_at = ?
    WHERE id IN (
        SELECT id FROM queue_items
        WHERE status IN ('queued', 'processing')
        ORDER BY id
        LIMIT ?
    )
    RETURNING id, note_path
"""

_MARK_DONE = "UPDATE queue_items SET status = 'done',   updated_at = ? WHERE id = ?"
_MARK_FAILED = "UPDATE queue_items SET status = 'failed', error = ?, updated_at = ? WHERE id = ?"


@dataclass
class WorkItem:
    id: int
    note_path: Path


class Queue:
    def __init__(self, db: Persistence):
        self._db = db
        db.define(_SCHEMA)

    def enqueue(self, note_path: Path) -> None:
        ts = clock.now()
        self._db.execute(_ENQUEUE, (str(note_path), ts, ts, str(note_path)))

    def claim(self, limit: int) -> list[WorkItem]:
        rows = self._db.execute(_CLAIM, (clock.now(), limit))
        return [WorkItem(id=row[0], note_path=Path(row[1])) for row in rows]

    def mark_done(self, item: WorkItem) -> None:
        self._db.execute(_MARK_DONE, (clock.now(), item.id))

    def mark_failed(self, item: WorkItem, error: str) -> None:
        self._db.execute(_MARK_FAILED, (error, clock.now(), item.id))
