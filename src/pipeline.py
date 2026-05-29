from pathlib import Path

from src.distill import Distiller
from src.grammar import GrammarReviewer
from src.granular_note import GranularNote
from src.notes import RawNote, Status


class Pipeline:
    def __init__(self, grammar: GrammarReviewer, distiller: Distiller, output_dir: Path) -> None:
        self._grammar = grammar
        self._distiller = distiller
        self._output_dir = output_dir

    def process(self, path: Path) -> None:
        note = RawNote.load(path)
        if note is None:
            return

        if note.status is Status.READY:
            corrected = self._grammar.correct(note.content)
            note.update_content(corrected)
            note.mark(Status.GRAMMAR_REVIEWED)

        if note.status is Status.GRAMMAR_REVIEWED:
            concepts = self._distiller.distill(note.content)
            filenames = [
                GranularNote(c, source=note.name).write_to(self._output_dir) for c in concepts
            ]
            note.add_created_notes(filenames)
            note.mark(Status.DONE)
