from unittest.mock import MagicMock

from src.grammar import GrammarReviewer


class TestGrammarReviewer:
    def _reviewer(self) -> tuple[GrammarReviewer, MagicMock]:
        mmx = MagicMock()
        return GrammarReviewer(mmx), mmx

    def test_correct_calls_chat_exactly_once(self):
        reviewer, mmx = self._reviewer()

        reviewer.correct("Hola mund")

        mmx.chat.assert_called_once()

    def test_correct_prompt_contains_original_content(self):
        reviewer, mmx = self._reviewer()
        content = "Hola mund"

        reviewer.correct(content)

        prompt = mmx.chat.call_args[0][0]
        assert content in prompt

    def test_correct_returns_chat_result(self):
        reviewer, mmx = self._reviewer()
        mmx.chat.return_value = "Hola mundo"

        result = reviewer.correct("Hola mund")

        assert result == "Hola mundo"
