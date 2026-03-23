"""Bridge API - exposes Python backend to frontend via PyWebView."""

import json

from src.platform_utils import (
    build_command,
    detect_env_type,
    detect_os,
    get_project_root,
    resolve_script,
)
from src.process_manager import ProcessManager


class Bridge:

    def __init__(self):
        self._window = None
        self._pm = ProcessManager()

    def set_window(self, window):
        self._window = window

    def get_platform_info(self) -> str:
        os_type = detect_os()
        env_type = detect_env_type()
        return json.dumps({"os": os_type.value, "env": env_type.value})

    def check_env(self) -> str:
        os_type = detect_os()
        env_type = detect_env_type()
        try:
            script_path = resolve_script("check-env", os_type, env_type)
        except ValueError as e:
            return json.dumps({"ok": False, "error": str(e)})

        if not script_path.exists():
            return json.dumps({"ok": False, "error": f"Script not found: {script_path.name}"})

        command = build_command(script_path)
        cwd = str(get_project_root())

        def on_log(line: str, level: str):
            if self._window is None:
                return
            escaped = json.dumps(line)
            self._window.evaluate_js(
                f"window.onLogLine({escaped}, '{level}')"
            )

        def on_complete(exit_code: int):
            if self._window is None:
                return
            self._window.evaluate_js(
                f"window.onProcessComplete({exit_code})"
            )

        started = self._pm.run_script(command, cwd, on_log, on_complete)
        if not started:
            return json.dumps({"ok": False, "error": "A process is already running"})
        return json.dumps({"ok": True})

    def cancel_process(self) -> str:
        cancelled = self._pm.cancel()
        return json.dumps({"ok": cancelled})

    def is_process_running(self) -> str:
        return json.dumps({"running": self._pm.is_running()})
