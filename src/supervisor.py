import subprocess


class ProcessorSupervisor:
    def __init__(self, unit: str):
        self._unit = unit

    def ensure_running(self):
        try:
            subprocess.run(["systemctl", "--user", "start", self._unit])
        except Exception:
            pass
