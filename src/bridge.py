"""Bridge API - exposes Python backend to frontend via PyWebView."""

import json
import threading

from src import config_manager
from src.env_checker import run_all_checks
from src.initializer import run_init
from src.platform_utils import (
    EnvType,
    OSType,
    detect_env_type,
    detect_os,
    get_project_root,
)


class Bridge:

    def __init__(self):
        self._window = None
        self._checking = False
        self._initializing = False

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

    # ── Initialize Wizard ──

    def get_init_defaults(self) -> str:
        """Return default init config based on detected OS/environment."""
        os_type = detect_os()
        env_type = detect_env_type()

        if env_type == EnvType.DOCKER:
            if os_type == OSType.WINDOWS:
                deploy_mode = "docker_windows"
            else:
                deploy_mode = "docker_linux"
        else:
            deploy_mode = "native_linux"

        return json.dumps({
            "deployMode": deploy_mode,
            "workingDir": ".openclaw",
            "bindHost": "0.0.0.0",
            "gatewayMode": "local",
            "gatewayPort": 18789,
        })

    def validate_init_config(self, config_json: str) -> str:
        """Validate initialization config synchronously."""
        try:
            config = json.loads(config_json)
        except (json.JSONDecodeError, TypeError):
            return json.dumps({"valid": False, "errors": {"_": "Invalid JSON"}})

        errors = {}

        deploy_mode = config.get("deployMode", "")
        if deploy_mode not in ("docker_windows", "docker_linux", "native_linux"):
            errors["deployMode"] = "請選擇部署模式"

        port = config.get("gatewayPort")
        if port is not None:
            try:
                port_int = int(port)
                if port_int < 1 or port_int > 65535:
                    errors["gatewayPort"] = "Port 需介於 1-65535"
            except (ValueError, TypeError):
                errors["gatewayPort"] = "Port 必須為數字"

        return json.dumps({
            "valid": len(errors) == 0,
            "errors": errors,
        })

    def save_secrets(self, secrets_json: str) -> str:
        """Store secrets in system keyring synchronously."""
        try:
            secrets = json.loads(secrets_json)
        except (json.JSONDecodeError, TypeError):
            return json.dumps({"ok": False, "error": "Invalid JSON"})

        results = config_manager.store_secrets(secrets)
        return json.dumps({"ok": True, "results": results})

    def run_init(self, config_json: str, secrets_json: str) -> str:
        """Run initialization asynchronously.

        Returns immediately with {ok: true}. Progress is pushed via
        window.onInitStepUpdate() and completion via window.onInitComplete().
        """
        if self._initializing:
            return json.dumps({"ok": False, "error": "Initialization already running"})

        try:
            init_config = json.loads(config_json)
            secrets = json.loads(secrets_json)
        except (json.JSONDecodeError, TypeError):
            return json.dumps({"ok": False, "error": "Invalid JSON"})

        self._initializing = True
        project_root = get_project_root()

        def _on_step_update(update: dict):
            if self._window is not None:
                payload = json.dumps(update)
                self._window.evaluate_js(
                    f"window.onInitStepUpdate({payload})"
                )

        def _run():
            try:
                result = run_init(
                    project_root=project_root,
                    init_config=init_config,
                    secrets=secrets,
                    on_step_update=_on_step_update,
                )
                if self._window is not None:
                    payload = json.dumps(result)
                    self._window.evaluate_js(
                        f"window.onInitComplete({payload})"
                    )
            except Exception as e:
                if self._window is not None:
                    error = json.dumps(str(e))
                    self._window.evaluate_js(
                        f"window.onInitError({error})"
                    )
            finally:
                self._initializing = False

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        return json.dumps({"ok": True})
