import os
import threading
from concurrent.futures import ThreadPoolExecutor

from src.pipeline import Pipeline
from src.processor_state import ProcessorState
from src.queue import Queue, WorkItem

_BATCH_SIZE = 5
_POLL_INTERVAL = 5.0
_MAX_EMPTY_POLLS = 3


class Processor:
    def __init__(self, queue: Queue, pipeline: Pipeline, state: ProcessorState) -> None:
        self._queue = queue
        self._pipeline = pipeline
        self._state = state
        self._stop_event = threading.Event()

    def run(self) -> None:
        empty_polls = 0
        while True:
            self._state.heartbeat(os.getpid())
            items = self._queue.claim(_BATCH_SIZE)

            if not items:
                empty_polls += 1
                if empty_polls >= _MAX_EMPTY_POLLS:
                    self._state.mark_stopped()
                    return
                self._stop_event.wait(_POLL_INTERVAL)
                if self._stop_event.is_set():
                    return
            else:
                empty_polls = 0
                self._run_batch(items)

    def stop(self) -> None:
        self._stop_event.set()

    def _run_batch(self, items: list[WorkItem]) -> None:
        with ThreadPoolExecutor(max_workers=_BATCH_SIZE) as pool:
            futures = [pool.submit(self._process_one, item) for item in items]
            for f in futures:
                f.result()

    def _process_one(self, item: WorkItem) -> None:
        try:
            self._pipeline.process(item.note_path)
            self._queue.mark_done(item)
        except Exception as e:
            self._queue.mark_failed(item, str(e))
