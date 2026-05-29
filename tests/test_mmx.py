import subprocess
from unittest.mock import MagicMock, patch

from src.mmx import _COMMAND, _TIMEOUT, MmxClient, MmxError


class TestConstants:
    def test_command_targets_mmx_text_chat(self):
        assert _COMMAND == ("mmx", "text", "chat")

    def test_timeout_is_120_seconds(self):
        assert _TIMEOUT == 120.0


class TestMmxError:
    def test_is_exception_subclass(self):
        assert issubclass(MmxError, Exception)


class TestChat:
    def _completed(self, stdout: str = "", returncode: int = 0) -> MagicMock:
        result = MagicMock()
        result.stdout = stdout
        result.returncode = returncode
        return result

    def test_sends_prompt_to_command_via_stdin_with_timeout(self):
        client = MmxClient()
        with patch("src.mmx.subprocess.run", return_value=self._completed()) as mock_run:
            client.chat("hello")

        mock_run.assert_called_once_with(
            _COMMAND,
            input="hello",
            capture_output=True,
            text=True,
            timeout=_TIMEOUT,
        )

    def test_returns_stdout_stripped_of_trailing_whitespace(self):
        client = MmxClient()
        with patch("src.mmx.subprocess.run", return_value=self._completed("  answer  \n")):
            result = client.chat("hello")

        assert result == "  answer"

    def test_raises_mmx_error_on_non_zero_exit_code(self):
        client = MmxClient()
        with patch("src.mmx.subprocess.run", return_value=self._completed(returncode=1)):
            try:
                client.chat("hello")
                assert False, "MmxError was not raised"
            except MmxError:
                pass

    def test_raises_mmx_error_on_timeout(self):
        client = MmxClient()
        timeout_error = subprocess.TimeoutExpired(_COMMAND, _TIMEOUT)
        with patch("src.mmx.subprocess.run", side_effect=timeout_error):
            try:
                client.chat("hello")
                assert False, "MmxError was not raised"
            except MmxError:
                pass
