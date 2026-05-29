from src.mmx import MmxClient

_PROMPT_TEMPLATE = (
    "Corrige solo los errores tipográficos y gramaticales del siguiente texto. "
    "Preserva el idioma español y el significado original. "
    "No añadas ni elimines contenido.\n\n{content}"
)


class GrammarReviewer:
    def __init__(self, mmx: MmxClient) -> None:
        self._mmx = mmx

    def correct(self, content: str) -> str:
        prompt = _PROMPT_TEMPLATE.format(content=content)
        return self._mmx.chat(prompt)
