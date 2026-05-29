from pathlib import Path

import pytest

from src.concept import Concept
from src.granular_note import GranularNote


@pytest.fixture()
def concept_full() -> Concept:
    return Concept(
        question="¿Qué es un objeto?",
        conclusion="Un objeto encapsula estado y comportamiento.",
        why="Porque agrupa datos y funciones relacionadas.",
        example="class Perro: pass",
    )


@pytest.fixture()
def concept_minimal() -> Concept:
    return Concept(
        question="¿Qué es una clase?",
        conclusion="Una clase es una plantilla para crear objetos.",
    )


# ── 1. write_to() creates a file in output_dir ──────────────────────────────

def test_write_to_creates_file(tmp_path: Path, concept_minimal: Concept) -> None:
    note = GranularNote(concept_minimal, source="MySource")
    note.write_to(tmp_path)
    files = list(tmp_path.iterdir())
    assert len(files) == 1


# ── 2. Filename starts with 💡_ and ends with .md ───────────────────────────

def test_filename_prefix_and_suffix(tmp_path: Path, concept_minimal: Concept) -> None:
    note = GranularNote(concept_minimal, source="MySource")
    note.write_to(tmp_path)
    (file,) = tmp_path.iterdir()
    assert file.name.startswith("💡_")
    assert file.name.endswith(".md")


# ── 3. Spaces in question become _ in filename ───────────────────────────────

def test_spaces_become_underscores_in_filename(tmp_path: Path) -> None:
    concept = Concept(question="what is a class", conclusion="A template.")
    note = GranularNote(concept, source="MySource")
    note.write_to(tmp_path)
    (file,) = tmp_path.iterdir()
    assert " " not in file.name
    assert "what_is_a_class" in file.name


# ── 4. write_to() returns the stem (filename without .md) ────────────────────

def test_write_to_returns_stem(tmp_path: Path, concept_minimal: Concept) -> None:
    note = GranularNote(concept_minimal, source="MySource")
    stem = note.write_to(tmp_path)
    (file,) = tmp_path.iterdir()
    assert stem == file.stem


# ── 5. Written file has frontmatter parent: [[<source>]] ─────────────────────

def test_frontmatter_parent(tmp_path: Path, concept_minimal: Concept) -> None:
    note = GranularNote(concept_minimal, source="MySource")
    note.write_to(tmp_path)
    (file,) = tmp_path.iterdir()
    content = file.read_text()
    assert "parent: [[MySource]]" in content


# ── 6. Body starts with # <question> ─────────────────────────────────────────

def test_body_starts_with_question_heading(tmp_path: Path, concept_minimal: Concept) -> None:
    note = GranularNote(concept_minimal, source="MySource")
    note.write_to(tmp_path)
    (file,) = tmp_path.iterdir()
    content = file.read_text()
    assert f"# {concept_minimal.question}" in content


# ── 7. Body contains the conclusion ──────────────────────────────────────────

def test_body_contains_conclusion(tmp_path: Path, concept_minimal: Concept) -> None:
    note = GranularNote(concept_minimal, source="MySource")
    note.write_to(tmp_path)
    (file,) = tmp_path.iterdir()
    content = file.read_text()
    assert concept_minimal.conclusion in content


# ── 8. ## Por qué section is present when why is non-empty ───────────────────

def test_por_que_section_present_when_why_non_empty(tmp_path: Path, concept_full: Concept) -> None:
    note = GranularNote(concept_full, source="MySource")
    note.write_to(tmp_path)
    (file,) = tmp_path.iterdir()
    content = file.read_text()
    assert "## Por qué" in content
    assert concept_full.why in content


# ── 9. ## Por qué section is absent when why is empty ────────────────────────

def test_por_que_section_absent_when_why_empty(tmp_path: Path, concept_minimal: Concept) -> None:
    note = GranularNote(concept_minimal, source="MySource")
    note.write_to(tmp_path)
    (file,) = tmp_path.iterdir()
    content = file.read_text()
    assert "## Por qué" not in content


# ── 10. ## Ejemplo section is present when example is non-empty ──────────────

def test_ejemplo_section_present_when_example_non_empty(
    tmp_path: Path, concept_full: Concept
) -> None:
    note = GranularNote(concept_full, source="MySource")
    note.write_to(tmp_path)
    (file,) = tmp_path.iterdir()
    content = file.read_text()
    assert "## Ejemplo" in content
    assert concept_full.example in content


# ── 11. ## Ejemplo section is absent when example is empty ───────────────────

def test_ejemplo_section_absent_when_example_empty(
    tmp_path: Path, concept_minimal: Concept
) -> None:
    note = GranularNote(concept_minimal, source="MySource")
    note.write_to(tmp_path)
    (file,) = tmp_path.iterdir()
    content = file.read_text()
    assert "## Ejemplo" not in content
