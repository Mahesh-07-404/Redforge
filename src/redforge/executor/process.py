import subprocess
import os
from typing import Optional

class ProcessManager:
    def __init__(self, command: list[str]):
        self.command = command
        self.process: Optional[subprocess.Popen] = None

    def spawn(self) -> subprocess.Popen:
        import sys
        creationflags = 0
        if sys.platform == "win32":
            creationflags = subprocess.CREATE_NO_WINDOW
            
        self.process = subprocess.Popen(
            self.command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=creationflags
        )
        return self.process

    def terminate(self):
        if self.process:
            self.process.terminate()

    def kill(self):
        if self.process:
            self.process.kill()

    def wait(self, timeout: Optional[float] = None) -> tuple[str, str, int]:
        if not self.process:
            raise ValueError("Process not spawned.")
        try:
            stdout, stderr = self.process.communicate(timeout=timeout)
            return stdout, stderr, self.process.returncode
        except subprocess.TimeoutExpired:
            self.kill()
            stdout, stderr = self.process.communicate()
            raise TimeoutError("Process timed out.")
