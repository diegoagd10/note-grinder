from __future__ import annotations

import signal
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from src.notes import RawNote, Status
from src.persistence import Persistence
from src.queue import Queue
from src.supervisor import ProcessorSupervisor


class Watcher(FileSystemEventHandler):
    def __init__(self, source_dir: Path, queue: Queue, supervisor: ProcessorSupervisor) -> None:
        super().__init__()
        self._source_dir = source_dir
        self._queue = queue
        self._supervisor = supervisor
        self._observer: Observer | None = None

    def run(self) -> None:
        observer = Observer()
        self._observer = observer
        observer.schedule(self, str(self._source_dir), recursive=False)
        observer.start()
        observer.join()

    def stop(self) -> None:
        if self._observer is not None:
            self._observer.stop()

    def on_modified(self, event) -> None:
        if event.is_directory:
            return
        note = RawNote.load(Path(event.src_path))
        if note is None or note.status is not Status.READY:
            return
        self._queue.enqueue(Path(event.src_path))
        self._supervisor.ensure_running()


def main() -> None:
    source_dir = Path.home() / "Documents/Diego_Second_Brain/03_Study/RawNotes"
    db_path = Path.home() / ".local/share/note-grinder/queue.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    persistence = Persistence(db_path)
    queue = Queue(persistence)
    supervisor = ProcessorSupervisor("note-processor")
    watcher = Watcher(source_dir=source_dir, queue=queue, supervisor=supervisor)

    signal.signal(signal.SIGTERM, lambda *_: watcher.stop())
    watcher.run()
