from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.concept import Concept
from src.notes import RawNote, Status
from src.pipeline import Pipeline

# ── shared fixtures ──────────────────────────────────────────────────────────

CONCEPTS = [
    Concept(question="¿Qué es Python?", conclusion="Un lenguaje interpretado."),
    Concept(question="¿Qué es una clase?", conclusion="Una plantilla de objetos."),
]

NOTE_READY = """\
---
process_status: Ready
---

Contenido original de la nota.
"""

NOTE_GRAMMAR_REVIEWED = """\
---
process_status: Grammar Reviewed
---

Contenido ya revisado gramaticalmente.
"""

NOTE_DONE = """\
---
process_status: Done
---

Nota completamente procesada.
"""


@pytest.fixture()
def grammar():
    mock = MagicMock()
    mock.correct.return_value = "Contenido corregido."
    return mock


@pytest.fixture()
def distiller():
    mock = MagicMock()
    mock.distill.return_value = CONCEPTS
    return mock


@pytest.fixture()
def output_dir(tmp_path: Path) -> Path:
    d = tmp_path / "output"
    d.mkdir()
    return d


def make_note(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "my-note.md"
    path.write_text(content)
    return path


# ── 0. Missing file is silently skipped ──────────────────────────────────────


def test_missing_file_does_nothing(grammar, distiller, output_dir, tmp_path):
    pipeline = Pipeline(grammar, distiller, output_dir)

    pipeline.process(tmp_path / "nonexistent.md")

    grammar.correct.assert_not_called()
    distiller.distill.assert_not_called()


# ── 1. READY note calls both grammar.correct and distiller.distill ───────────


def test_ready_note_calls_grammar_and_distiller(tmp_path, grammar, distiller, output_dir):
    path = make_note(tmp_path, NOTE_READY)
    pipeline = Pipeline(grammar, distiller, output_dir)

    pipeline.process(path)

    grammar.correct.assert_called_once()
    distiller.distill.assert_called_once()


# ── 2. READY note ends with status DONE ─────────────────────────────────────


def test_ready_note_ends_done(tmp_path, grammar, distiller, output_dir):
    path = make_note(tmp_path, NOTE_READY)
    pipeline = Pipeline(grammar, distiller, output_dir)

    pipeline.process(path)

    reloaded = RawNote.load(path)
    assert reloaded.status == Status.DONE


# ── 3. READY note produces granular note files in output_dir ─────────────────


def test_ready_note_produces_granular_files(tmp_path, grammar, distiller, output_dir):
    path = make_note(tmp_path, NOTE_READY)
    pipeline = Pipeline(grammar, distiller, output_dir)

    pipeline.process(path)

    files = list(output_dir.iterdir())
    assert len(files) == len(CONCEPTS)


# ── 4. GRAMMAR_REVIEWED note skips grammar but calls distiller ───────────────


def test_grammar_reviewed_skips_grammar_runs_distiller(
    tmp_path, grammar, distiller, output_dir
):
    path = make_note(tmp_path, NOTE_GRAMMAR_REVIEWED)
    pipeline = Pipeline(grammar, distiller, output_dir)

    pipeline.process(path)

    grammar.correct.assert_not_called()
    distiller.distill.assert_called_once()


# ── 5. GRAMMAR_REVIEWED note ends with status DONE ───────────────────────────


def test_grammar_reviewed_note_ends_done(tmp_path, grammar, distiller, output_dir):
    path = make_note(tmp_path, NOTE_GRAMMAR_REVIEWED)
    pipeline = Pipeline(grammar, distiller, output_dir)

    pipeline.process(path)

    reloaded = RawNote.load(path)
    assert reloaded.status == Status.DONE


# ── 6. DONE note runs neither phase ──────────────────────────────────────────


def test_done_note_skips_both_phases(tmp_path, grammar, distiller, output_dir):
    path = make_note(tmp_path, NOTE_DONE)
    pipeline = Pipeline(grammar, distiller, output_dir)

    pipeline.process(path)

    grammar.correct.assert_not_called()
    distiller.distill.assert_not_called()


# ── 7. add_created_notes is called with write_to() filenames ─────────────────


def test_created_notes_section_appears_in_note_body(tmp_path, grammar, distiller, output_dir):
    path = make_note(tmp_path, NOTE_READY)
    pipeline = Pipeline(grammar, distiller, output_dir)

    pipeline.process(path)

    reloaded = RawNote.load(path)
    assert "## Created Notes" in reloaded.content
    for concept in CONCEPTS:
        sanitized = concept.question.replace("/", "-").replace("\\", "-").replace(" ", "_")
        assert sanitized in reloaded.content
