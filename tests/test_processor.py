import threading
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from src.processor import Processor
from src.queue import WorkItem


def make_item(note_path: str = "notes/a.md") -> WorkItem:
    return WorkItem(id=1, note_path=Path(note_path))


@pytest.fixture()
def queue():
    mock = MagicMock()
    mock.claim.return_value = []
    return mock


@pytest.fixture()
def pipeline():
    return MagicMock()


@pytest.fixture()
def state():
    return MagicMock()


@pytest.fixture()
def processor(queue, pipeline, state):
    return Processor(queue, pipeline, state)


# ── _process_one ─────────────────────────────────────────────────────────────


class TestProcessOne:
    def test_calls_pipeline_and_marks_done_on_success(self, processor, queue, pipeline):
        item = make_item()

        processor._process_one(item)

        pipeline.process.assert_called_once_with(item.note_path)
        queue.mark_done.assert_called_once_with(item)
        queue.mark_failed.assert_not_called()

    def test_marks_failed_with_error_string_when_pipeline_raises(
        self, processor, queue, pipeline
    ):
        item = make_item()
        pipeline.process.side_effect = RuntimeError("disk full")

        processor._process_one(item)

        queue.mark_failed.assert_called_once_with(item, "disk full")
        queue.mark_done.assert_not_called()


# ── _run_batch ────────────────────────────────────────────────────────────────


class TestRunBatch:
    def test_processes_all_items_in_batch(self, processor, pipeline):
        items = [make_item(f"notes/{i}.md") for i in range(5)]

        processor._run_batch(items)

        assert pipeline.process.call_count == 5
        pipeline.process.assert_has_calls(
            [call(item.note_path) for item in items], any_order=True
        )


# ── run() — empty poll exhaustion ────────────────────────────────────────────


class TestRunEmptyPolls:
    def test_marks_stopped_after_max_empty_polls(self, processor, queue, state):
        # claim always returns empty → exhausts _MAX_EMPTY_POLLS (3)
        with patch("os.getpid", return_value=42):
            processor.run()

        state.mark_stopped.assert_called_once()
        assert queue.claim.call_count == 3

    def test_non_empty_claim_resets_empty_poll_counter(self, queue, pipeline, state):
        # 2 empties (below threshold), 1 item (resets counter), 3 empties → stops
        # Total: 6 claims. Without the reset the loop would stop at poll 3.
        item = make_item()
        queue.claim.side_effect = [[], [], [item], [], [], []]

        processor = Processor(queue, pipeline, state)
        with patch("os.getpid", return_value=1):
            processor.run()

        state.mark_stopped.assert_called_once()
        assert queue.claim.call_count == 6


# ── run() — stop() interrupts the wait ───────────────────────────────────────


class TestStop:
    def test_stop_interrupts_run_mid_wait(self, queue, pipeline, state):
        # claim returns empty once so run() enters the wait; stop() wakes it
        queue.claim.return_value = []

        processor = Processor(queue, pipeline, state)

        t = threading.Thread(target=processor.run)
        t.start()
        processor.stop()
        t.join(timeout=2.0)

        assert not t.is_alive(), "run() did not return within 2 s after stop()"
