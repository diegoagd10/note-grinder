from pathlib import Path

import pytest

from src.concept import Concept
from src.granular_note import GranularNote


@pytest.fixture()
def concept_full() -> Concept:
    return Concept(
        filename="⏰🧠¿Cuándo debemos refactorizar?",
        body="Debemos refactorizar cuando el diseño actual dificulta añadir nueva funcionalidad.",
        tags=["Software_Design", "Refactoring"],
        example="Antes de agregar una feature, mejorar la estructura para que sea más fácil.",
    )


@pytest.fixture()
def concept_minimal() -> Concept:
    return Concept(
        filename="🏗️¿Qué es un módulo profundo?",
        body="Un módulo con una interfaz simple que oculta una implementación compleja.",
    )


# ── 1. write_to() creates a file in output_dir ──────────────────────────────

def test_write_to_creates_file(tmp_path: Path, concept_minimal: Concept) -> None:
    note = GranularNote(concept_minimal, parent="A Philosophy of Software Design")
    note.write_to(tmp_path)
    files = list(tmp_path.iterdir())
    assert len(files) == 1


# ── 2. Filename matches concept.filename + .md ───────────────────────────────

def test_filename_is_concept_filename(tmp_path: Path, concept_minimal: Concept) -> None:
    note = GranularNote(concept_minimal, parent="A Philosophy of Software Design")
    note.write_to(tmp_path)
    (file,) = tmp_path.iterdir()
    assert file.name == f"{concept_minimal.filename}.md"


# ── 3. write_to() returns the stem ───────────────────────────────────────────

def test_write_to_returns_stem(tmp_path: Path, concept_minimal: Concept) -> None:
    note = GranularNote(concept_minimal, parent="A Philosophy of Software Design")
    stem = note.write_to(tmp_path)
    (file,) = tmp_path.iterdir()
    assert stem == file.stem


# ── 4. Frontmatter contains parent with quoted wikilink ──────────────────────

def test_frontmatter_parent_with_wikilink(tmp_path: Path, concept_minimal: Concept) -> None:
    note = GranularNote(concept_minimal, parent="A Philosophy of Software Design")
    note.write_to(tmp_path)
    (file,) = tmp_path.iterdir()
    content = file.read_text()
    assert 'parent: "[[A Philosophy of Software Design]]"' in content


# ── 5. Frontmatter contains tags as YAML list ────────────────────────────────

def test_frontmatter_tags_as_yaml_list(tmp_path: Path, concept_full: Concept) -> None:
    note = GranularNote(concept_full, parent="Book")
    note.write_to(tmp_path)
    (file,) = tmp_path.iterdir()
    content = file.read_text()
    assert "tags:" in content
    assert "  - Software_Design" in content
    assert "  - Refactoring" in content


# ── 6. Frontmatter omits tags block when tags is empty ───────────────────────

def test_frontmatter_omits_tags_when_empty(tmp_path: Path, concept_minimal: Concept) -> None:
    note = GranularNote(concept_minimal, parent="Book")
    note.write_to(tmp_path)
    (file,) = tmp_path.iterdir()
    content = file.read_text()
    assert "tags:" not in content


# ── 7. Frontmatter contains chapter when provided ────────────────────────────

def test_frontmatter_chapter_when_provided(tmp_path: Path, concept_minimal: Concept) -> None:
    note = GranularNote(concept_minimal, parent="Book", chapter="7")
    note.write_to(tmp_path)
    (file,) = tmp_path.iterdir()
    content = file.read_text()
    assert "chapter: 7" in content


# ── 8. Frontmatter omits chapter when not provided ───────────────────────────

def test_frontmatter_omits_chapter_when_none(tmp_path: Path, concept_minimal: Concept) -> None:
    note = GranularNote(concept_minimal, parent="Book")
    note.write_to(tmp_path)
    (file,) = tmp_path.iterdir()
    content = file.read_text()
    assert "chapter:" not in content


# ── 9. Frontmatter always has review_result: 0 ───────────────────────────────

def test_frontmatter_review_result_is_zero(tmp_path: Path, concept_minimal: Concept) -> None:
    note = GranularNote(concept_minimal, parent="Book")
    note.write_to(tmp_path)
    (file,) = tmp_path.iterdir()
    content = file.read_text()
    assert "review_result: 0" in content


# ── 10. Body contains prose without a markdown heading ───────────────────────

def test_body_contains_prose_without_heading(tmp_path: Path, concept_minimal: Concept) -> None:
    note = GranularNote(concept_minimal, parent="Book")
    note.write_to(tmp_path)
    (file,) = tmp_path.iterdir()
    content = file.read_text()
    assert concept_minimal.body in content
    assert f"# {concept_minimal.filename}" not in content


# ── 11. **Examples:** section present when example is non-empty ──────────────

def test_examples_section_present_when_non_empty(tmp_path: Path, concept_full: Concept) -> None:
    note = GranularNote(concept_full, parent="Book")
    note.write_to(tmp_path)
    (file,) = tmp_path.iterdir()
    content = file.read_text()
    assert "**Examples:**" in content
    assert concept_full.example in content


# ── 12. **Examples:** section absent when example is empty ───────────────────

def test_examples_section_absent_when_empty(tmp_path: Path, concept_minimal: Concept) -> None:
    note = GranularNote(concept_minimal, parent="Book")
    note.write_to(tmp_path)
    (file,) = tmp_path.iterdir()
    content = file.read_text()
    assert "**Examples:**" not in content
