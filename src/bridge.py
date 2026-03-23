"""Bridge API — 透過 PyWebView 將 Python 後端暴露給前端。"""

import json
import threading

from src import config_manager
from src.env_checker import run_all_checks
from src.initializer import run_init
from src.platform_utils import EnvType, OSType, detect_env_type, detect_os, get_project_root

# 有效的部署模式
_VALID_DEPLOY_MODES = {"docker_windows", "docker_linux", "native_linux"}


class Bridge:
    """PyWebView Bridge — 前端透過此類別呼叫所有後端操作。"""

    def __init__(self):
        self._window = None
        self._checking = False
        self._initializing = False

    def set_window(self, window) -> None:
        self._window = window

    # ── 內部輔助 ──

    def _push_js(self, callback: str, payload) -> None:
        """將資料推送至前端 JavaScript 回呼函式。"""
        if self._window is not None:
            self._window.evaluate_js(f"window.{callback}({json.dumps(payload)})")

    def _run_in_thread(self, fn, lock_attr: str) -> str:
        """在背景執行緒執行 fn，透過 lock_attr 防止重複執行。

        fn 接收 push_js 輔助函式作為參數，負責推送結果。
        執行完畢後自動釋放鎖定。
        """
        if getattr(self, lock_attr):
            return json.dumps({"ok": False, "error": "操作執行中"})

        setattr(self, lock_attr, True)

        def _worker():
            try:
                fn()
            finally:
                setattr(self, lock_attr, False)

        threading.Thread(target=_worker, daemon=True).start()
        return json.dumps({"ok": True})

    # ── 平台資訊 ──

    def get_platform_info(self) -> str:
        """回傳作業系統與環境類型。"""
        return json.dumps({
            "os": detect_os().value,
            "env": detect_env_type().value,
        })

    # ── 環境檢查 ──

    def check_env(self) -> str:
        """非同步執行環境檢查，結果透過 onCheckEnvResults() 推送至前端。"""
        def _do_check():
            try:
                self._push_js("onCheckEnvResults", run_all_checks())
            except Exception as e:
                self._push_js("onCheckEnvError", str(e))

        return self._run_in_thread(_do_check, "_checking")

    # ── 初始化精靈 ──

    def get_init_defaults(self) -> str:
        """依偵測的 OS/環境回傳預設初始化設定。"""
        os_type = detect_os()
        env_type = detect_env_type()

        if env_type == EnvType.DOCKER:
            deploy_mode = "docker_windows" if os_type == OSType.WINDOWS else "docker_linux"
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
        """同步驗證初始化設定。"""
        try:
            config = json.loads(config_json)
        except (json.JSONDecodeError, TypeError):
            return json.dumps({"valid": False, "errors": {"_": "無效的 JSON"}})

        errors = {}

        if config.get("deployMode", "") not in _VALID_DEPLOY_MODES:
            errors["deployMode"] = "請選擇部署模式"

        port = config.get("gatewayPort")
        if port is not None:
            try:
                port_int = int(port)
                if not 1 <= port_int <= 65535:
                    errors["gatewayPort"] = "Port 需介於 1-65535"
            except (ValueError, TypeError):
                errors["gatewayPort"] = "Port 必須為數字"

        return json.dumps({"valid": not errors, "errors": errors})

    def save_secrets(self, secrets_json: str) -> str:
        """將金鑰同步儲存至系統 keyring。"""
        try:
            secrets = json.loads(secrets_json)
        except (json.JSONDecodeError, TypeError):
            return json.dumps({"ok": False, "error": "無效的 JSON"})

        results = config_manager.store_secrets(secrets)
        return json.dumps({"ok": True, "results": results})

    def run_init(self, config_json: str, secrets_json: str) -> str:
        """非同步執行初始化，進度透過 onInitStepUpdate() 推送，完成透過 onInitComplete()。"""
        try:
            init_config = json.loads(config_json)
            secrets = json.loads(secrets_json)
        except (json.JSONDecodeError, TypeError):
            return json.dumps({"ok": False, "error": "無效的 JSON"})

        project_root = get_project_root()

        def _do_init():
            try:
                result = run_init(
                    project_root=project_root,
                    init_config=init_config,
                    secrets=secrets,
                    on_step_update=lambda u: self._push_js("onInitStepUpdate", u),
                )
                self._push_js("onInitComplete", result)
            except Exception as e:
                self._push_js("onInitError", str(e))

        return self._run_in_thread(_do_init, "_initializing")
