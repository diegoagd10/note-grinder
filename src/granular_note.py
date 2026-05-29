from pathlib import Path

from src.concept import Concept
from src.markdown_document import MarkdownDocument


def _to_filename(question: str) -> str:
    sanitized = question.replace("/", "-").replace("\\", "-").replace(" ", "_")
    return f"💡_{sanitized}.md"


class GranularNote:
    def __init__(self, concept: Concept, source: str) -> None:
        self._concept = concept
        self._source = source

    def write_to(self, output_dir: Path) -> str:
        filename = _to_filename(self._concept.question)
        doc = MarkdownDocument.create(output_dir / filename)
        doc.set_field("parent", f"[[{self._source}]]")
        doc.set_body(f"# {self._concept.question}\n{self._concept.conclusion}")
        if self._concept.why:
            doc.append_section(f"\n\n## Por qué\n{self._concept.why}")
        if self._concept.example:
            doc.append_section(f"\n\n## Ejemplo\n{self._concept.example}")
        doc.save()
        return doc.path.stem
