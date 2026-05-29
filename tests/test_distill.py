import json
from unittest.mock import MagicMock

import pytest

from src.concept import Concept
from src.distill import Distiller, DistillError


def _mmx(response: str) -> MagicMock:
    client = MagicMock()
    client.chat.return_value = response
    return client


_FULL = [{"question": "Q1", "conclusion": "C1", "why": "W1", "example": "E1"}]
_MINIMAL = [{"question": "Q2", "conclusion": "C2"}]


class TestDistillError:
    def test_is_exception_subclass(self):
        assert issubclass(DistillError, Exception)


class TestDistiller:
    def test_clean_json_array_returns_concept_list(self):
        mmx = _mmx(json.dumps(_FULL))
        result = Distiller(mmx).distill("some content")

        assert result == [Concept(question="Q1", conclusion="C1", why="W1", example="E1")]

    def test_prose_before_and_after_array_still_parses(self):
        response = "Here are your concepts:\n" + json.dumps(_FULL) + "\nHope that helps!"
        result = Distiller(_mmx(response)).distill("content")

        assert result == [Concept(question="Q1", conclusion="C1", why="W1", example="E1")]

    def test_markdown_fenced_json_still_parses(self):
        response = "```json\n" + json.dumps(_FULL) + "\n```"
        result = Distiller(_mmx(response)).distill("content")

        assert result == [Concept(question="Q1", conclusion="C1", why="W1", example="E1")]

    def test_missing_why_and_example_default_to_empty_string(self):
        result = Distiller(_mmx(json.dumps(_MINIMAL))).distill("content")

        assert result == [Concept(question="Q2", conclusion="C2", why="", example="")]

    def test_no_brackets_raises_distill_error(self):
        with pytest.raises(DistillError):
            Distiller(_mmx("No JSON here at all.")).distill("content")

    def test_invalid_json_in_span_raises_distill_error(self):
        with pytest.raises(DistillError):
            Distiller(_mmx("[not valid json}")).distill("content")

    def test_missing_required_field_raises_distill_error(self):
        bad = json.dumps([{"question": "Q only"}])
        with pytest.raises(DistillError):
            Distiller(_mmx(bad)).distill("content")

    def test_chat_called_exactly_once(self):
        mmx = _mmx(json.dumps(_FULL))
        Distiller(mmx).distill("content")

        mmx.chat.assert_called_once()

    def test_prompt_contains_original_content(self):
        mmx = _mmx(json.dumps(_FULL))
        Distiller(mmx).distill("my special note content")

        prompt = mmx.chat.call_args[0][0]
        assert "my special note content" in prompt
