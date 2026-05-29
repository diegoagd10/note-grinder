from pathlib import Path

from src.concept import Concept
from src.markdown_document import MarkdownDocument


def _to_filename(name: str) -> str:
    sanitized = name.replace("/", "-").replace("\\", "-")
    return f"{sanitized}.md"


class GranularNote:
    def __init__(self, concept: Concept, parent: str, chapter: str | None = None) -> None:
        self._concept = concept
        self._parent = parent
        self._chapter = chapter

    def write_to(self, output_dir: Path) -> str:
        filename = _to_filename(self._concept.filename)
        doc = MarkdownDocument.create(output_dir / filename)
        doc.set_field("parent", f'"[[{self._parent}]]"')
        if self._concept.tags:
            doc.set_field("tags", self._concept.tags)
        if self._chapter:
            doc.set_field("chapter", self._chapter)
        doc.set_field("review_result", "0")
        doc.set_body(self._concept.body)
        if self._concept.example:
            doc.append_section(f"\n\n**Examples:**\n{self._concept.example}")
        doc.save()
        return doc.path.stem
