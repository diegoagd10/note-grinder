from pathlib import Path

import pytest

from src.persistence import Persistence
from src.queue import Queue, WorkItem


@pytest.fixture()
def db(tmp_path):
    return Persistence(tmp_path / "notes.db")


@pytest.fixture()
def queue(db):
    return Queue(db)


class TestEnqueue:
    def test_inserts_row_with_status_queued(self, db, queue):
        queue.enqueue(Path("notes/a.md"))

        rows = db.execute("SELECT note_path, status FROM queue_items")
        assert rows == [("notes/a.md", "queued")]

    def test_idempotent_when_row_is_queued(self, db, queue):
        queue.enqueue(Path("notes/a.md"))
        queue.enqueue(Path("notes/a.md"))

        rows = db.execute("SELECT COUNT(*) FROM queue_items WHERE note_path = 'notes/a.md'")
        assert rows == [(1,)]

    def test_idempotent_when_row_is_processing(self, db, queue):
        queue.enqueue(Path("notes/a.md"))
        db.execute("UPDATE queue_items SET status = 'processing' WHERE note_path = 'notes/a.md'")

        queue.enqueue(Path("notes/a.md"))

        rows = db.execute("SELECT COUNT(*) FROM queue_items WHERE note_path = 'notes/a.md'")
        assert rows == [(1,)]

    def test_reenqueues_done_note(self, db, queue):
        queue.enqueue(Path("notes/a.md"))
        db.execute("UPDATE queue_items SET status = 'done' WHERE note_path = 'notes/a.md'")

        queue.enqueue(Path("notes/a.md"))

        rows = db.execute("SELECT COUNT(*) FROM queue_items WHERE note_path = 'notes/a.md'")
        assert rows == [(2,)]


class TestClaim:
    def test_returns_up_to_limit_work_items(self, queue):
        queue.enqueue(Path("notes/a.md"))
        queue.enqueue(Path("notes/b.md"))
        queue.enqueue(Path("notes/c.md"))

        items = queue.claim(2)

        assert len(items) == 2
        assert all(isinstance(item, WorkItem) for item in items)

    def test_marks_returned_items_as_processing(self, db, queue):
        queue.enqueue(Path("notes/a.md"))
        queue.enqueue(Path("notes/b.md"))

        items = queue.claim(2)
        ids = [item.id for item in items]

        rows = db.execute(
            f"SELECT status FROM queue_items WHERE id IN ({','.join('?' * len(ids))})", ids
        )
        assert all(status == "processing" for (status,) in rows)

    def test_includes_already_processing_items_for_crash_recovery(self, db, queue):
        queue.enqueue(Path("notes/a.md"))
        db.execute("UPDATE queue_items SET status = 'processing' WHERE note_path = 'notes/a.md'")

        items = queue.claim(10)

        assert len(items) == 1
        assert items[0].note_path == Path("notes/a.md")

    def test_returns_empty_list_when_queue_is_empty(self, queue):
        items = queue.claim(10)

        assert items == []


class TestMarkDone:
    def test_sets_status_to_done(self, db, queue):
        queue.enqueue(Path("notes/a.md"))
        (item,) = queue.claim(1)

        queue.mark_done(item)

        rows = db.execute("SELECT status FROM queue_items WHERE id = ?", (item.id,))
        assert rows == [("done",)]


class TestMarkFailed:
    def test_sets_status_to_failed(self, db, queue):
        queue.enqueue(Path("notes/a.md"))
        (item,) = queue.claim(1)

        queue.mark_failed(item, "timeout")

        rows = db.execute("SELECT status FROM queue_items WHERE id = ?", (item.id,))
        assert rows == [("failed",)]

    def test_stores_error_string(self, db, queue):
        queue.enqueue(Path("notes/a.md"))
        (item,) = queue.claim(1)

        queue.mark_failed(item, "connection refused")

        rows = db.execute("SELECT error FROM queue_items WHERE id = ?", (item.id,))
        assert rows == [("connection refused",)]
