import signal
from pathlib import Path

from src.distill import Distiller
from src.grammar import GrammarReviewer
from src.mmx import MmxClient
from src.persistence import Persistence
from src.pipeline import Pipeline
from src.processor import Processor
from src.processor_state import ProcessorState
from src.queue import Queue

_DB_PATH = Path.home() / ".local/share/note-grinder/queue.db"
_OUTPUT_DIR = Path.home() / "Documents/Diego_Second_Brain/03_Study/Notes"


def main() -> None:
    db = Persistence(_DB_PATH)
    mmx = MmxClient()

    queue = Queue(db)
    state = ProcessorState(db)

    grammar = GrammarReviewer(mmx)
    distiller = Distiller(mmx)

    pipeline = Pipeline(grammar, distiller, _OUTPUT_DIR)
    processor = Processor(queue, pipeline, state)

    signal.signal(signal.SIGTERM, lambda *_: processor.stop())

    processor.run()
