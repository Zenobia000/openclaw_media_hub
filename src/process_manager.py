"""程序管理器 — 非同步子程序執行與日誌串流。"""

import re
import subprocess
import threading
from typing import Callable

ANSI_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")

# 日誌等級關鍵字對應表
_LOG_LEVEL_KEYWORDS = {
    "[OK]": "ok",
    "[FAIL]": "error",
    "[ERROR]": "error",
    "[WARN]": "warn",
    "[INFO]": "info",
}


def strip_ansi(text: str) -> str:
    """移除 ANSI 色彩控制碼。"""
    return ANSI_RE.sub("", text)


def parse_log_level(line: str) -> str:
    """從日誌行偵測等級（ok/error/warn/info/default）。"""
    upper = line.upper()
    for keyword, level in _LOG_LEVEL_KEYWORDS.items():
        if keyword in upper:
            return level
    return "default"


class ProcessManager:
    """非同步子程序管理器 — 執行指令並串流日誌至回呼函式。"""

    def __init__(self):
        self._lock = threading.Lock()
        self._process: subprocess.Popen | None = None

    def is_running(self) -> bool:
        """檢查子程序是否仍在執行。"""
        with self._lock:
            return self._process is not None and self._process.poll() is None

    def run_script(
        self,
        command: list[str],
        cwd: str,
        on_log: Callable[[str, str], None],
        on_complete: Callable[[int], None],
    ) -> bool:
        """在背景執行緒啟動指令。回傳 False 表示已有程序執行中。"""
        if self.is_running():
            return False

        threading.Thread(
            target=self._run,
            args=(command, cwd, on_log, on_complete),
            daemon=True,
        ).start()
        return True

    def _run(
        self,
        command: list[str],
        cwd: str,
        on_log: Callable[[str, str], None],
        on_complete: Callable[[int], None],
    ) -> None:
        """執行緒主體：啟動程序、串流日誌、回報結束碼。"""
        exit_code = -1
        try:
            proc = subprocess.Popen(
                command, cwd=cwd,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1,
            )
            with self._lock:
                self._process = proc

            for raw_line in proc.stdout:
                line = strip_ansi(raw_line.rstrip("\n\r"))
                if line:
                    on_log(line, parse_log_level(line))

            proc.wait()
            exit_code = proc.returncode
        except Exception as e:
            on_log(f"程序錯誤: {e}", "error")
        finally:
            with self._lock:
                self._process = None
            on_complete(exit_code)

    def cancel(self) -> bool:
        """終止執行中的子程序。"""
        with self._lock:
            if self._process is not None and self._process.poll() is None:
                self._process.terminate()
                return True
            return False
