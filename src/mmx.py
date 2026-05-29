import subprocess

_COMMAND = ("mmx", "text", "chat")
_TIMEOUT = 120.0


class MmxError(Exception):
    pass


class MmxClient:
    def chat(self, prompt: str) -> str:
        try:
            result = subprocess.run(
                _COMMAND,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=_TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            raise MmxError
        if result.returncode != 0:
            raise MmxError
        return result.stdout.rstrip()
