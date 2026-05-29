import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src import clock
from src.distill import Distiller
from src.grammar import GrammarReviewer
from src.notes import RawNote, Status
from src.persistence import Persistence
from src.pipeline import Pipeline
from src.processor import Processor
from src.processor_state import ProcessorState
from src.queue import Queue


def make_note(path: Path, status: str, body: str = "Body text.") -> None:
    path.write_text(f"---\nprocess_status: {status}\n---\n\n{body}\n")


class TestProcessorIntegration:
    @pytest.fixture()
    def db(self, tmp_path: Path) -> Persistence:
        return Persistence(tmp_path / "queue.db")

    @pytest.fixture()
    def queue(self, db: Persistence) -> Queue:
        return Queue(db)

    @pytest.fixture()
    def state(self, db: Persistence) -> ProcessorState:
        return ProcessorState(db)

    @pytest.fixture()
    def output_dir(self, tmp_path: Path) -> Path:
        d = tmp_path / "output"
        d.mkdir()
        return d

    @pytest.fixture()
    def mmx(self) -> MagicMock:
        return MagicMock()

    @pytest.fixture()
    def pipeline(self, mmx: MagicMock, output_dir: Path) -> Pipeline:
        grammar = GrammarReviewer(mmx)
        distiller = Distiller(mmx)
        return Pipeline(grammar=grammar, distiller=distiller, output_dir=output_dir)

    @pytest.fixture()
    def processor(self, queue: Queue, pipeline: Pipeline, state: ProcessorState) -> Processor:
        return Processor(queue=queue, pipeline=pipeline, state=state)

    def test_full_pipeline_ready_to_done(
        self,
        tmp_path: Path,
        queue: Queue,
        processor: Processor,
        mmx: MagicMock,
        output_dir: Path,
    ) -> None:
        note_path = tmp_path / "my_note.md"
        body = "El objeto es una instancia de clase."
        make_note(note_path, "Ready", body)

        distill_json = (
            '[{"filename": "🧠¿Qué es un objeto?", "body": "Es una instancia de una clase.",'
            ' "tags": ["OOP"], "example": ""}]'
        )
        mmx.chat.side_effect = [body, distill_json]

        queue.enqueue(note_path)

        with patch("src.processor._POLL_INTERVAL", 0.05):
            t = threading.Thread(target=processor.run)
            t.start()
            t.join(timeout=10)

        assert not t.is_alive(), "Processor did not stop within 10 s"

        note = RawNote.load(note_path)
        assert note is not None
        assert note.status is Status.DONE

        content = note_path.read_text()
        assert "## Created Notes" in content

        granular_files = list(output_dir.glob("*.md"))
        assert len(granular_files) >= 1

    def test_self_stops_after_empty_polls(
        self,
        queue: Queue,
        processor: Processor,
        state: ProcessorState,
    ) -> None:
        with patch("src.processor._POLL_INTERVAL", 0.05):
            t = threading.Thread(target=processor.run)
            t.start()
            t.join(timeout=5)

        assert not t.is_alive(), "Processor did not self-stop within 5 s"
        assert not state.is_healthy()

    def test_recovers_processing_items_on_restart(
        self,
        tmp_path: Path,
        db: Persistence,
        queue: Queue,
        processor: Processor,
        mmx: MagicMock,
    ) -> None:
        note_path = tmp_path / "inflight_note.md"
        make_note(note_path, "Grammar Reviewed", "El objeto es una instancia de clase.")

        ts = clock.now()
        db.execute(
            "INSERT INTO queue_items(note_path, status, created_at, updated_at)"
            " VALUES(?, 'processing', ?, ?)",
            (str(note_path), ts, ts),
        )

        distill_json = (
            '[{"filename": "🧠¿Qué es un objeto?", "body": "Es una instancia de una clase.",'
            ' "tags": ["OOP"], "example": ""}]'
        )
        mmx.chat.return_value = distill_json

        with patch("src.processor._POLL_INTERVAL", 0.05):
            t = threading.Thread(target=processor.run)
            t.start()
            t.join(timeout=10)

        assert not t.is_alive(), "Processor did not stop within 10 s"

        note = RawNote.load(note_path)
        assert note is not None
        assert note.status is Status.DONE
