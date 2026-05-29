from dataclasses import dataclass, field


@dataclass
class Concept:
    filename: str
    body: str
    tags: list[str] = field(default_factory=list)
    example: str = ""
