from __future__ import annotations

import enum
from pathlib import Path

from src.markdown_document import MarkdownDocument


class Status(enum.Enum):
    CREATING = "Creating"
    READY = "Ready"
    GRAMMAR_REVIEWED = "Grammar Reviewed"
    DONE = "Done"


class RawNote:
    def __init__(self, doc: MarkdownDocument) -> None:
        self._doc = doc

    @classmethod
    def load(cls, path: Path) -> RawNote | None:
        doc = MarkdownDocument.load(path)
        if doc is None:
            return None
        return cls(doc)

    @property
    def status(self) -> Status | None:
        value = self._doc.get_field("process_status")
        if value is None:
            return None
        return next((s for s in Status if s.value == value), None)

    @property
    def content(self) -> str:
        return self._doc.body

    def update_content(self, text: str) -> None:
        self._doc.set_body(text)
        self._doc.save()

    def mark(self, status: Status) -> None:
        self._doc.set_field("process_status", status.value)
        self._doc.save()

    def add_created_notes(self, filenames: list[str]) -> None:
        links = "\n".join(f"[[{name}]]" for name in filenames)
        self._doc.append_section(f"\n## Created Notes\n\n{links}\n")
        self._doc.save()

    @property
    def name(self) -> str:
        return self._doc.path.stem
