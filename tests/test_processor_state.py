from datetime import datetime, timedelta, timezone

import pytest

from src.persistence import Persistence
from src.processor_state import ProcessorState


@pytest.fixture()
def db(tmp_path):
    return Persistence(tmp_path / "notes.db")


@pytest.fixture()
def state(db):
    return ProcessorState(db)


class TestHeartbeat:
    def test_sets_status_to_running(self, db, state):
        state.heartbeat(pid=42)

        rows = db.execute("SELECT status FROM processor_state WHERE id = 1")
        assert rows == [("running",)]

    def test_records_pid(self, db, state):
        state.heartbeat(pid=1234)

        rows = db.execute("SELECT pid FROM processor_state WHERE id = 1")
        assert rows == [(1234,)]


class TestMarkStopped:
    def test_sets_status_to_stopped(self, db, state):
        state.heartbeat(pid=99)
        state.mark_stopped()

        rows = db.execute("SELECT status FROM processor_state WHERE id = 1")
        assert rows == [("stopped",)]


class TestIsHealthy:
    def test_returns_true_right_after_heartbeat(self, state):
        state.heartbeat(pid=7)

        assert state.is_healthy() is True

    def test_returns_false_after_mark_stopped(self, state):
        state.heartbeat(pid=7)
        state.mark_stopped()

        assert state.is_healthy() is False

    def test_returns_false_when_no_row_exists(self, state):
        assert state.is_healthy() is False

    def test_returns_false_when_last_seen_is_stale(self, db, state):
        state.heartbeat(pid=7)

        stale_ts = (datetime.now(timezone.utc) - timedelta(seconds=31)).isoformat()
        db.execute(
            "UPDATE processor_state SET last_seen = ? WHERE id = 1",
            (stale_ts,),
        )

        assert state.is_healthy() is False
