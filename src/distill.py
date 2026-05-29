import json

from src.concept import Concept
from src.mmx import MmxClient

_PROMPT = """\
You are a study-note distiller. Convert raw reading notes into final study notes
for active recall. For each distinct argument or idea, produce one JSON object:

1. filename – Emojis representing the answer + a Spanish active-recall question.
   Example: "⏰🧠¿Cómo podemos mantener la calma cuando enfrentamos un obstáculo?"
2. body – A concise Spanish paragraph answering the question. No markdown heading.
3. tags – Array of 1–3 PascalCase topic strings (e.g. ["Software_Design"]).
4. example – A concrete analogy or snippet that illustrates the idea. "" if none.

Respond with ONLY a JSON array — no prose, no markdown fences.

Raw notes:
{content}"""


class DistillError(Exception):
    pass


class Distiller:
    def __init__(self, mmx: MmxClient) -> None:
        self._mmx = mmx

    def distill(self, content: str) -> list[Concept]:
        """Distills content into concepts by calling mmx and parsing the JSON response."""
        response = self._mmx.chat(_PROMPT.format(content=content))
        return self._parse(response)

    def _parse(self, response: str) -> list[Concept]:
        # Tolerates prose and markdown fences by finding the outermost [...] span.
        start = response.find("[")
        end = response.rfind("]")
        if start == -1 or end == -1:
            raise DistillError("No JSON array found in mmx response")
        try:
            items = json.loads(response[start : end + 1])
            return [
                Concept(
                    filename=item["filename"],
                    body=item["body"],
                    tags=item.get("tags", []),
                    example=item.get("example", ""),
                )
                for item in items
            ]
        except (json.JSONDecodeError, KeyError) as exc:
            raise DistillError(f"Malformed mmx response: {exc}") from exc
