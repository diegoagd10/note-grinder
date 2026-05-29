from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.processor_main import main

_DB_PATH = Path.home() / ".local/share/note-grinder/queue.db"
_OUTPUT_DIR = Path.home() / "Documents/Diego_Second_Brain/03_Study/Notes"


@pytest.fixture()
def mocks():
    """Return a namespace of all patched collaborators for main()."""
    with (
        patch("src.processor_main.Persistence") as persistence_cls,
        patch("src.processor_main.MmxClient") as mmx_cls,
        patch("src.processor_main.Queue") as queue_cls,
        patch("src.processor_main.ProcessorState") as state_cls,
        patch("src.processor_main.GrammarReviewer") as grammar_cls,
        patch("src.processor_main.Distiller") as distiller_cls,
        patch("src.processor_main.Pipeline") as pipeline_cls,
        patch("src.processor_main.Processor") as processor_cls,
        patch("src.processor_main.signal") as signal_mod,
    ):
        ns = MagicMock()
        ns.persistence_cls = persistence_cls
        ns.mmx_cls = mmx_cls
        ns.queue_cls = queue_cls
        ns.state_cls = state_cls
        ns.grammar_cls = grammar_cls
        ns.distiller_cls = distiller_cls
        ns.pipeline_cls = pipeline_cls
        ns.processor_cls = processor_cls
        ns.signal_mod = signal_mod
        yield ns


class TestMain:
    def test_calls_processor_run(self, mocks):
        main()

        mocks.processor_cls.return_value.run.assert_called_once()

    def test_registers_sigterm_handler(self, mocks):
        main()

        mocks.signal_mod.signal.assert_called_once_with(
            mocks.signal_mod.SIGTERM, mocks.signal_mod.signal.call_args[0][1]
        )

    def test_sigterm_handler_calls_processor_stop(self, mocks):
        main()

        _, handler = mocks.signal_mod.signal.call_args[0]
        handler()

        mocks.processor_cls.return_value.stop.assert_called_once()

    def test_wires_persistence_with_correct_db_path(self, mocks):
        main()

        mocks.persistence_cls.assert_called_once_with(_DB_PATH)

    def test_wires_queue_with_persistence_instance(self, mocks):
        main()

        mocks.queue_cls.assert_called_once_with(mocks.persistence_cls.return_value)

    def test_wires_processor_state_with_persistence_instance(self, mocks):
        main()

        mocks.state_cls.assert_called_once_with(mocks.persistence_cls.return_value)

    def test_wires_grammar_reviewer_with_mmx_instance(self, mocks):
        main()

        mocks.grammar_cls.assert_called_once_with(mocks.mmx_cls.return_value)

    def test_wires_distiller_with_mmx_instance(self, mocks):
        main()

        mocks.distiller_cls.assert_called_once_with(mocks.mmx_cls.return_value)

    def test_wires_pipeline_with_correct_output_dir(self, mocks):
        main()

        mocks.pipeline_cls.assert_called_once_with(
            mocks.grammar_cls.return_value,
            mocks.distiller_cls.return_value,
            _OUTPUT_DIR,
        )

    def test_wires_processor_with_queue_pipeline_and_state(self, mocks):
        main()

        mocks.processor_cls.assert_called_once_with(
            mocks.queue_cls.return_value,
            mocks.pipeline_cls.return_value,
            mocks.state_cls.return_value,
        )
