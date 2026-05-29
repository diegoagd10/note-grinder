from dataclasses import dataclass


@dataclass
class Concept:
    question: str
    conclusion: str
    why: str = ""
    example: str = ""
