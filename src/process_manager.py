"""Process Manager - async subprocess execution and log streaming."""

import re
import subprocess
import threading
from typing import Callable, Optional

ANSI_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


def parse_log_level(line: str) -> str:
    upper = line.upper()
    if "[OK]" in upper:
        return "ok"
    if "[FAIL]" in upper or "[ERROR]" in upper:
        return "error"
    if "[WARN]" in upper:
        return "warn"
    if "[INFO]" in upper:
        return "info"
    return "default"


class ProcessManager:

    def __init__(self):
        self._lock = threading.Lock()
        self._process: Optional[subprocess.Popen] = None

    def is_running(self) -> bool:
        with self._lock:
            return self._process is not None and self._process.poll() is None

    def run_script(
        self,
        command: list[str],
        cwd: str,
        on_log: Callable[[str, str], None],
        on_complete: Callable[[int], None],
    ) -> bool:
        with self._lock:
            if self._process is not None and self._process.poll() is None:
                return False

        thread = threading.Thread(
            target=self._run,
            args=(command, cwd, on_log, on_complete),
            daemon=True,
        )
        thread.start()
        return True

    def _run(
        self,
        command: list[str],
        cwd: str,
        on_log: Callable[[str, str], None],
        on_complete: Callable[[int], None],
    ):
        try:
            proc = subprocess.Popen(
                command,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            with self._lock:
                self._process = proc

            for raw_line in proc.stdout:
                line = strip_ansi(raw_line.rstrip("\n\r"))
                if line:
                    level = parse_log_level(line)
                    on_log(line, level)

            proc.wait()
            exit_code = proc.returncode
        except Exception as e:
            on_log(f"Process error: {e}", "error")
            exit_code = -1
        finally:
            with self._lock:
                self._process = None
            on_complete(exit_code)

    def cancel(self) -> bool:
        with self._lock:
            if self._process is not None and self._process.poll() is None:
                self._process.terminate()
                return True
            return False
