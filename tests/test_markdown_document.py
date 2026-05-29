from pathlib import Path

import pytest

from src.markdown_document import MarkdownDocument

FRONTMATTER_FILE = """\
---
process_status: Ready
author: Diego
---

Body content here
"""


@pytest.fixture
def existing_file(tmp_path) -> Path:
    path = tmp_path / "note.md"
    path.write_text(FRONTMATTER_FILE)
    return path


class TestLoad:
    def test_returns_none_when_file_does_not_exist(self, tmp_path):
        result = MarkdownDocument.load(tmp_path / "missing.md")

        assert result is None

    def test_parses_frontmatter_fields(self, existing_file):
        doc = MarkdownDocument.load(existing_file)

        assert doc.get_field("process_status") == "Ready"
        assert doc.get_field("author") == "Diego"

    def test_returns_body_excluding_frontmatter(self, existing_file):
        doc = MarkdownDocument.load(existing_file)

        assert "Body content here" in doc.body
        assert "---" not in doc.body
        assert "process_status" not in doc.body


class TestCreate:
    def test_path_matches_given_path(self, tmp_path):
        target = tmp_path / "new_note.md"

        doc = MarkdownDocument.create(target)

        assert doc.path == target

    def test_path_is_pathlib_path(self, tmp_path):
        doc = MarkdownDocument.create(tmp_path / "new_note.md")

        assert isinstance(doc.path, Path)


class TestGetField:
    def test_returns_value_for_known_key(self, existing_file):
        doc = MarkdownDocument.load(existing_file)

        assert doc.get_field("process_status") == "Ready"

    def test_returns_none_for_unknown_key(self, existing_file):
        doc = MarkdownDocument.load(existing_file)

        assert doc.get_field("nonexistent_field") is None


class TestSetField:
    def test_adds_new_field_persisted_after_save(self, tmp_path):
        path = tmp_path / "note.md"
        path.write_text(FRONTMATTER_FILE)
        doc = MarkdownDocument.load(path)
        doc.set_field("priority", "high")
        doc.save()

        reloaded = MarkdownDocument.load(path)

        assert reloaded.get_field("priority") == "high"

    def test_updates_existing_field_persisted_after_save(self, tmp_path):
        path = tmp_path / "note.md"
        path.write_text(FRONTMATTER_FILE)
        doc = MarkdownDocument.load(path)
        doc.set_field("process_status", "Done")
        doc.save()

        reloaded = MarkdownDocument.load(path)

        assert reloaded.get_field("process_status") == "Done"


class TestBody:
    def test_body_property_returns_body_content(self, existing_file):
        doc = MarkdownDocument.load(existing_file)

        assert "Body content here" in doc.body

    def test_set_body_replaces_body_persisted_after_save(self, tmp_path):
        path = tmp_path / "note.md"
        path.write_text(FRONTMATTER_FILE)
        doc = MarkdownDocument.load(path)
        doc.set_body("Completely new content")
        doc.save()

        reloaded = MarkdownDocument.load(path)

        assert "Completely new content" in reloaded.body
        assert "Body content here" not in reloaded.body

    def test_append_section_adds_to_body_persisted_after_save(self, tmp_path):
        path = tmp_path / "note.md"
        path.write_text(FRONTMATTER_FILE)
        doc = MarkdownDocument.load(path)
        doc.append_section("## New Section\n\nAdded text")
        doc.save()

        reloaded = MarkdownDocument.load(path)

        assert "Body content here" in reloaded.body
        assert "## New Section" in reloaded.body
        assert "Added text" in reloaded.body


class TestPath:
    def test_path_property_returns_pathlib_path(self, existing_file):
        doc = MarkdownDocument.load(existing_file)

        assert isinstance(doc.path, Path)

    def test_path_property_matches_loaded_file(self, existing_file):
        doc = MarkdownDocument.load(existing_file)

        assert doc.path == existing_file


class TestParse:
    def test_content_without_frontmatter_delimiter_treated_as_body(self, tmp_path):
        path = tmp_path / "plain.md"
        path.write_text("Just plain body text\n")

        doc = MarkdownDocument.load(path)

        assert doc.get_field("any") is None
        assert "Just plain body text" in doc.body

    def test_opening_delimiter_with_no_newline_treated_as_body(self, tmp_path):
        path = tmp_path / "no_newline.md"
        path.write_text("---")

        doc = MarkdownDocument.load(path)

        assert doc.get_field("any") is None
        assert doc.body == "---"

    def test_unclosed_frontmatter_treated_as_body(self, tmp_path):
        path = tmp_path / "unclosed.md"
        path.write_text("---\ntitle: Missing close\nstill body\n")

        doc = MarkdownDocument.load(path)

        assert doc.get_field("title") is None
        assert "Missing close" in doc.body


class TestSave:
    def test_save_without_frontmatter_writes_body_only(self, tmp_path):
        path = tmp_path / "note.md"
        doc = MarkdownDocument.create(path)
        doc.set_body("Body only content\n")
        doc.save()

        reloaded = MarkdownDocument.load(path)

        assert reloaded.get_field("any") is None
        assert "Body only content" in reloaded.body
