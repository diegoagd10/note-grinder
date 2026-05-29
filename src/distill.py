import json

from src.concept import Concept
from src.mmx import MmxClient

_PROMPT = """\
Distill the arguments in the following content into a JSON array.
Each element must have these keys: question, conclusion, why, example.
Respond with ONLY the JSON array — no prose, no markdown fences.

Content:
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
                    question=item["question"],
                    conclusion=item["conclusion"],
                    why=item.get("why", ""),
                    example=item.get("example", ""),
                )
                for item in items
            ]
        except (json.JSONDecodeError, KeyError) as exc:
            raise DistillError(f"Malformed mmx response: {exc}") from exc
