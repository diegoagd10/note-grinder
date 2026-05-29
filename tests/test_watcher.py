from pathlib import Path
from unittest.mock import MagicMock, patch

from src.watcher import Watcher

NOTE_READY = """\
---
process_status: Ready
---

Some body content here
"""

NOTE_CREATING = """\
---
process_status: Creating
---

Work in progress
"""


def _make_file_event(path: Path, *, is_directory: bool = False) -> MagicMock:
    event = MagicMock()
    event.src_path = str(path)
    event.is_directory = is_directory
    return event


def _make_watcher(tmp_path: Path) -> tuple[Watcher, MagicMock, MagicMock]:
    queue = MagicMock()
    supervisor = MagicMock()
    watcher = Watcher(source_dir=tmp_path, queue=queue, supervisor=supervisor)
    return watcher, queue, supervisor


class TestOnModified:
    def test_ignores_directory_events(self, tmp_path):
        watcher, queue, supervisor = _make_watcher(tmp_path)
        event = _make_file_event(tmp_path / "subdir", is_directory=True)

        watcher.on_modified(event)

        queue.enqueue.assert_not_called()
        supervisor.ensure_running.assert_not_called()

    def test_ignores_file_with_non_ready_status(self, tmp_path):
        note_path = tmp_path / "wip.md"
        note_path.write_text(NOTE_CREATING)
        watcher, queue, supervisor = _make_watcher(tmp_path)
        event = _make_file_event(note_path)

        watcher.on_modified(event)

        queue.enqueue.assert_not_called()
        supervisor.ensure_running.assert_not_called()

    def test_enqueues_ready_file(self, tmp_path):
        note_path = tmp_path / "ready.md"
        note_path.write_text(NOTE_READY)
        watcher, queue, supervisor = _make_watcher(tmp_path)
        event = _make_file_event(note_path)

        watcher.on_modified(event)

        queue.enqueue.assert_called_once_with(Path(str(note_path)))

    def test_calls_ensure_running_for_ready_file(self, tmp_path):
        note_path = tmp_path / "ready.md"
        note_path.write_text(NOTE_READY)
        watcher, queue, supervisor = _make_watcher(tmp_path)
        event = _make_file_event(note_path)

        watcher.on_modified(event)

        supervisor.ensure_running.assert_called_once()

    def test_ignores_missing_file(self, tmp_path):
        watcher, queue, supervisor = _make_watcher(tmp_path)
        event = _make_file_event(tmp_path / "ghost.md")

        watcher.on_modified(event)

        queue.enqueue.assert_not_called()
        supervisor.ensure_running.assert_not_called()

    def test_ignores_file_with_no_status_field(self, tmp_path):
        note_path = tmp_path / "no_status.md"
        note_path.write_text("---\nauthor: Diego\n---\n\nBody\n")
        watcher, queue, supervisor = _make_watcher(tmp_path)
        event = _make_file_event(note_path)

        watcher.on_modified(event)

        queue.enqueue.assert_not_called()
        supervisor.ensure_running.assert_not_called()


class TestStop:
    def test_stop_calls_observer_stop(self, tmp_path):
        watcher, _, _ = _make_watcher(tmp_path)
        mock_observer = MagicMock()

        with patch("src.watcher.Observer", return_value=mock_observer):
            import threading

            thread = threading.Thread(target=watcher.run)
            thread.start()
            # Wait until observer.start() is called so the observer is stored
            import time

            time.sleep(0.05)
            watcher.stop()
            thread.join(timeout=2)

        mock_observer.stop.assert_called_once()


class TestRun:
    def test_run_schedules_and_starts_observer(self, tmp_path):
        watcher, _, _ = _make_watcher(tmp_path)
        mock_observer = MagicMock()

        with patch("src.watcher.Observer", return_value=mock_observer):
            watcher.run()

        mock_observer.schedule.assert_called_once_with(watcher, str(tmp_path), recursive=False)
        mock_observer.start.assert_called_once()
        mock_observer.join.assert_called_once()
