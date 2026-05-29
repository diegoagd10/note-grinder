from __future__ import annotations

from pathlib import Path


class MarkdownDocument:
    def __init__(self, path: Path, frontmatter: dict[str, str | list[str]], body: str) -> None:
        self._path = path
        self._frontmatter = frontmatter
        self._body = body

    @classmethod
    def load(cls, path: Path) -> MarkdownDocument | None:
        path = Path(path)
        if not path.exists():
            return None
        content = path.read_text()
        frontmatter, body = cls._parse(content)
        return cls(path, frontmatter, body)

    @classmethod
    def create(cls, path: Path) -> MarkdownDocument:
        return cls(Path(path), {}, "")

    @classmethod
    def _parse(cls, content: str) -> tuple[dict[str, str], str]:
        if not content.startswith("---"):
            return {}, content
        rest = content[3:]
        if "\n" not in rest:
            return {}, content
        after_open = rest[rest.index("\n") + 1:]
        close = after_open.find("---")
        if close == -1:
            return {}, content
        fm_block = after_open[:close]
        raw_body = after_open[close + 3:]
        if raw_body.startswith("\n"):
            raw_body = raw_body[1:]
        frontmatter: dict[str, str] = {}
        for line in fm_block.splitlines():
            if ":" in line:
                key, _, value = line.partition(":")
                frontmatter[key.strip()] = value.strip()
        return frontmatter, raw_body

    @property
    def path(self) -> Path:
        return self._path

    @property
    def body(self) -> str:
        return self._body

    def get_field(self, name: str) -> str | None:
        return self._frontmatter.get(name)

    def set_field(self, name: str, value: str | list[str]) -> None:
        self._frontmatter[name] = value

    def set_body(self, text: str) -> None:
        self._body = text

    def append_section(self, markdown: str) -> None:
        self._body = self._body + markdown

    def save(self) -> None:
        parts: list[str] = []
        if self._frontmatter:
            lines = ["---"]
            for key, value in self._frontmatter.items():
                if isinstance(value, list):
                    lines.append(f"{key}:")
                    for item in value:
                        lines.append(f"  - {item}")
                else:
                    lines.append(f"{key}: {value}")
            lines.append("---")
            parts.append("\n".join(lines))
            parts.append("\n" + self._body)
        else:
            parts.append(self._body)
        self._path.write_text("".join(parts))
