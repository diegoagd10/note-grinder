from src.notes import RawNote, Status

NOTE_WITH_STATUS = """\
---
process_status: Ready
---

Some body content here
"""

NOTE_WITHOUT_STATUS = """\
---
author: Diego
---

Body without status
"""

NOTE_PLAIN = "Plain body with no frontmatter\n"


class TestLoad:
    def test_returns_none_for_missing_file(self, tmp_path):
        result = RawNote.load(tmp_path / "missing.md")

        assert result is None

    def test_returns_raw_note_for_existing_file(self, tmp_path):
        path = tmp_path / "note.md"
        path.write_text(NOTE_WITH_STATUS)

        result = RawNote.load(path)

        assert isinstance(result, RawNote)


class TestStatus:
    def test_returns_correct_status_enum_when_field_is_present(self, tmp_path):
        path = tmp_path / "note.md"
        path.write_text(NOTE_WITH_STATUS)
        note = RawNote.load(path)

        assert note.status == Status.READY

    def test_returns_none_when_field_is_missing(self, tmp_path):
        path = tmp_path / "note.md"
        path.write_text(NOTE_WITHOUT_STATUS)
        note = RawNote.load(path)

        assert note.status is None


class TestContent:
    def test_returns_body_text(self, tmp_path):
        path = tmp_path / "note.md"
        path.write_text(NOTE_WITH_STATUS)
        note = RawNote.load(path)

        assert "Some body content here" in note.content


class TestUpdateContent:
    def test_replaces_body_persisted_after_reload(self, tmp_path):
        path = tmp_path / "note.md"
        path.write_text(NOTE_WITH_STATUS)
        note = RawNote.load(path)

        note.update_content("Replaced body text\n")

        reloaded = RawNote.load(path)
        assert "Replaced body text" in reloaded.content
        assert "Some body content here" not in reloaded.content


class TestMark:
    def test_sets_frontmatter_field_and_saves(self, tmp_path):
        path = tmp_path / "note.md"
        path.write_text(NOTE_WITH_STATUS)
        note = RawNote.load(path)

        note.mark(Status.DONE)

        reloaded = RawNote.load(path)
        assert reloaded.status == Status.DONE


class TestAddCreatedNotes:
    def test_appends_created_notes_section_with_wikilinks(self, tmp_path):
        path = tmp_path / "note.md"
        path.write_text(NOTE_WITH_STATUS)
        note = RawNote.load(path)

        note.add_created_notes(["alpha", "beta"])

        reloaded = RawNote.load(path)
        assert "## Created Notes" in reloaded.content
        assert "[[alpha]]" in reloaded.content
        assert "[[beta]]" in reloaded.content

    def test_original_body_preserved_after_appending(self, tmp_path):
        path = tmp_path / "note.md"
        path.write_text(NOTE_WITH_STATUS)
        note = RawNote.load(path)

        note.add_created_notes(["gamma"])

        reloaded = RawNote.load(path)
        assert "Some body content here" in reloaded.content


class TestName:
    def test_returns_file_stem_without_extension(self, tmp_path):
        path = tmp_path / "my-note-title.md"
        path.write_text(NOTE_PLAIN)
        note = RawNote.load(path)

        assert note.name == "my-note-title"
