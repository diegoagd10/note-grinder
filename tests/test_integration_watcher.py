from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.persistence import Persistence
from src.queue import Queue
from src.watcher import Watcher


def make_note(path: Path, status: str) -> None:
    path.write_text(f"---\nprocess_status: {status}\n---\n\nBody text.\n")


def make_event(path: Path) -> object:
    event = MagicMock()
    event.is_directory = False
    event.src_path = str(path)
    return event


class TestWatcherIntegration:
    @pytest.fixture()
    def db(self, tmp_path: Path) -> Persistence:
        return Persistence(tmp_path / "queue.db")

    @pytest.fixture()
    def queue(self, db: Persistence) -> Queue:
        return Queue(db)

    @pytest.fixture()
    def supervisor(self) -> MagicMock:
        mock = MagicMock()
        mock.ensure_running = MagicMock()
        return mock

    @pytest.fixture()
    def watcher(self, tmp_path: Path, queue: Queue, supervisor: MagicMock) -> Watcher:
        return Watcher(source_dir=tmp_path, queue=queue, supervisor=supervisor)

    def test_creating_note_is_not_enqueued(
        self, tmp_path: Path, watcher: Watcher, queue: Queue
    ) -> None:
        note_path = tmp_path / "wip.md"
        make_note(note_path, "Creating")
        event = make_event(note_path)

        watcher.on_modified(event)
        watcher.on_modified(event)

        assert queue.claim(10) == []

    def test_ready_note_enqueued_exactly_once(
        self, tmp_path: Path, watcher: Watcher, queue: Queue
    ) -> None:
        note_path = tmp_path / "ready.md"
        make_note(note_path, "Ready")
        event = make_event(note_path)

        watcher.on_modified(event)
        watcher.on_modified(event)
        watcher.on_modified(event)

        items = queue.claim(10)
        assert len(items) == 1
        assert items[0].note_path == note_path

    def test_ready_note_starts_supervisor(
        self, tmp_path: Path, watcher: Watcher, supervisor: MagicMock
    ) -> None:
        note_path = tmp_path / "ready.md"
        make_note(note_path, "Ready")
        event = make_event(note_path)

        watcher.on_modified(event)

        supervisor.ensure_running.assert_called()

    def test_creating_note_does_not_start_supervisor(
        self, tmp_path: Path, watcher: Watcher, supervisor: MagicMock
    ) -> None:
        note_path = tmp_path / "wip.md"
        make_note(note_path, "Creating")
        event = make_event(note_path)

        watcher.on_modified(event)

        supervisor.ensure_running.assert_not_called()

    def test_missing_file_is_ignored(
        self, tmp_path: Path, watcher: Watcher, queue: Queue, supervisor: MagicMock
    ) -> None:
        note_path = tmp_path / "ghost.md"
        event = make_event(note_path)

        watcher.on_modified(event)

        assert queue.claim(10) == []
        supervisor.ensure_running.assert_not_called()
