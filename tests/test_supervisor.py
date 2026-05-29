from unittest.mock import MagicMock, patch

from src.supervisor import ProcessorSupervisor


class TestProcessorSupervisor:
    def test_calls_systemctl_with_correct_command(self):
        supervisor = ProcessorSupervisor("my-processor.service")

        with patch("src.supervisor.subprocess.run") as mock_run:
            supervisor.ensure_running()

        mock_run.assert_called_once_with(
            ["systemctl", "--user", "start", "my-processor.service"]
        )

    def test_unit_name_appears_in_command(self):
        supervisor = ProcessorSupervisor("custom-unit.service")

        with patch("src.supervisor.subprocess.run") as mock_run:
            supervisor.ensure_running()

        args = mock_run.call_args[0][0]
        assert "custom-unit.service" in args

    def test_does_not_raise_on_non_zero_exit_code(self):
        supervisor = ProcessorSupervisor("my-processor.service")
        failed_result = MagicMock()
        failed_result.returncode = 1

        with patch("src.supervisor.subprocess.run", return_value=failed_result):
            supervisor.ensure_running()

    def test_does_not_raise_when_subprocess_raises(self):
        supervisor = ProcessorSupervisor("my-processor.service")

        with patch("src.supervisor.subprocess.run", side_effect=OSError("systemctl not found")):
            supervisor.ensure_running()
