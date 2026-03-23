"""Bridge API - exposes Python backend to frontend via PyWebView."""

import json
import threading

from src.env_checker import run_all_checks
from src.platform_utils import detect_env_type, detect_os


class Bridge:

    def __init__(self):
        self._window = None
        self._checking = False

    def set_window(self, window):
        self._window = window

    def get_platform_info(self) -> str:
        os_type = detect_os()
        env_type = detect_env_type()
        return json.dumps({"os": os_type.value, "env": env_type.value})

    def check_env(self) -> str:
        """Run environment checks asynchronously.

        Returns immediately with {ok: true}. Results are pushed to the
        frontend via window.onCheckEnvResults() callback when complete.
        """
        if self._checking:
            return json.dumps({"ok": False, "error": "Check already running"})

        self._checking = True

        def _run():
            try:
                results = run_all_checks()
                if self._window is not None:
                    payload = json.dumps(results)
                    self._window.evaluate_js(
                        f"window.onCheckEnvResults({payload})"
                    )
            except Exception as e:
                if self._window is not None:
                    error = json.dumps(str(e))
                    self._window.evaluate_js(
                        f"window.onCheckEnvError({error})"
                    )
            finally:
                self._checking = False

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        return json.dumps({"ok": True})
