"""Bridge API — PyWebView 前端 Bridge 類別。

所有 public method 自動暴露為 window.pywebview.api.* 供前端呼叫。
回傳格式統一: {"success": True/False, "data": ..., "error": ...}

設計依據: 208_frontend_specification.md §5.1~5.3
"""

from __future__ import annotations

import asyncio
import enum
import logging
import socket
from collections.abc import Callable
from typing import Any

import paramiko
import webview

from src.config_manager import ConfigManager
from src.executor import Executor
from src.local_executor import LocalExecutor
from src.process_manager import ProcessManager
from src.remote_executor import RemoteExecutor
from src.ssh_connection import ConnectionState, SSHConnection, SSHConnectionConfig

logger = logging.getLogger(__name__)


class ErrorType(enum.Enum):
    """Bridge API 錯誤類型 — 對應前端錯誤處理策略 (208 §5.3)。"""

    TIMEOUT = "TIMEOUT"
    PERMISSION = "PERMISSION"
    NOT_FOUND = "NOT_FOUND"
    INTERNAL = "INTERNAL"
    CONNECTION_LOST = "CONNECTION_LOST"
    AUTH_FAILED = "AUTH_FAILED"
    SFTP_TIMEOUT = "SFTP_TIMEOUT"


def _ok(data: Any = None) -> dict:
    """統一成功回傳格式。"""
    return {"success": True, "data": data, "error": None}


def _err(error_type: ErrorType, message: str) -> dict:
    """統一失敗回傳格式。"""
    return {
        "success": False,
        "data": None,
        "error": {"type": error_type.value, "message": message},
    }


def _map_exception(exc: Exception) -> dict:
    """將 Python exception 映射為結構化錯誤回傳。"""
    if isinstance(exc, TimeoutError | asyncio.TimeoutError):
        return _err(ErrorType.TIMEOUT, str(exc) or "Operation timed out")
    if isinstance(exc, PermissionError):
        return _err(ErrorType.PERMISSION, str(exc) or "Permission denied")
    if isinstance(exc, FileNotFoundError):
        return _err(ErrorType.NOT_FOUND, str(exc) or "File or resource not found")
    if isinstance(exc, socket.gaierror):
        return _err(ErrorType.CONNECTION_LOST, f"DNS resolution failed — check hostname: {exc}")
    if isinstance(exc, (ConnectionError, OSError)) and not isinstance(exc, (PermissionError, FileNotFoundError)):
        return _err(ErrorType.CONNECTION_LOST, str(exc) or "Connection lost")
    if isinstance(exc, paramiko.AuthenticationException):
        return _err(ErrorType.AUTH_FAILED, str(exc) or "Authentication failed")
    # 預設 INTERNAL
    return _err(ErrorType.INTERNAL, str(exc) or "Internal error")


class Bridge:
    """PyWebView Bridge API。

    每個 public method 都會成為前端可呼叫的 JavaScript API。
    回傳值由 PyWebView 自動序列化為 JSON。

    Executor 注入點：
    - 預設使用 LocalExecutor（本機模式）
    - SSH 連線成功後切換為 RemoteExecutor（遠端模式）
    - 上層模組透過 self._executor / self._process_manager 操作
    """

    def __init__(self) -> None:
        self._local_executor = LocalExecutor()
        self._executor: Executor = self._local_executor
        self._process_manager = ProcessManager(self._executor)
        self._config_manager = ConfigManager()
        self._window: webview.Window | None = None
        self._ssh_connection: SSHConnection | None = None
        self._remote_executor: RemoteExecutor | None = None

    def set_window(self, window: webview.Window) -> None:
        """註冊 PyWebView 視窗實例（由 main.py 呼叫）。"""
        self._window = window

    @property
    def executor(self) -> Executor:
        return self._executor

    def _switch_executor(self, executor: Executor) -> None:
        """切換 Executor（Local ↔ Remote）。"""
        self._executor = executor
        self._process_manager.executor = executor

    # ── 進度回呼機制 (208 §5.2) ──────────────────────────

    def _evaluate_js(self, js_code: str) -> None:
        """透過 PyWebView 反向呼叫前端 JavaScript。

        用於耗時操作的即時進度更新。
        """
        if self._window:
            self._window.evaluate_js(js_code)

    def _notify_progress(self, callback_name: str, *args: str) -> None:
        """呼叫前端全域進度回呼函式。

        Args:
            callback_name: 前端函式名（如 updateInitProgress）
            *args: 傳遞給前端的參數（字串）
        """
        escaped_args = ", ".join(f"'{_js_escape(a)}'" for a in args)
        self._evaluate_js(f"window.{callback_name}({escaped_args})")

    def _notify_init_progress(self, step: str, status: str, message: str) -> None:
        self._notify_progress("updateInitProgress", step, status, message)

    def _notify_deploy_progress(self, name: str, status: str, message: str) -> None:
        self._notify_progress("updateDeployProgress", name, status, message)

    def _notify_plugin_progress(self, name: str, status: str, message: str) -> None:
        self._notify_progress("updatePluginProgress", name, status, message)

    def _notify_fix_progress(self, name: str, status: str, message: str) -> None:
        self._notify_progress("updateFixProgress", name, status, message)

    def _notify_connection_status(self, status: str, message: str) -> None:
        self._notify_progress("updateConnectionStatus", status, message)

    # ── 安全的 async 執行包裝 ────────────────────────────

    def _run_async(self, coro: Any) -> Any:
        """在新的事件迴圈中執行 async 協程（PyWebView 的 Bridge 方法是同步的）。"""
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    def _safe_call(self, fn: Callable[[], Any]) -> dict:
        """包裝 API 呼叫，統一 exception → 錯誤回傳。"""
        try:
            return fn()
        except Exception as exc:
            logger.exception("Bridge API error")
            return _map_exception(exc)

    # ── Public API ───────────────────────────────────────

    def ping(self) -> dict:
        """連線測試，前端用來確認 Bridge 可用。"""
        return _ok({"message": "pong"})

    # ── 環境檢查 API (3.4, US-001) ────────────────────────

    def check_env(self) -> dict:
        """環境檢查 — 依部署模式檢查系統依賴。

        Returns:
            {checks: [{name, installed, version, message}], env_file: {exists, message}}
        """
        def _do() -> dict:
            from src.env_checker import EnvChecker
            from src.platform_utils import detect_platform as _detect

            mode = _detect().deployment_mode
            checker = EnvChecker(self._executor)
            checks = self._run_async(checker.check_all(mode))
            env_file = self._run_async(checker.check_env_file(".env"))
            return _ok({"checks": checks, "env_file": env_file})

        return self._safe_call(_do)

    def detect_platform(self) -> dict:
        """偵測平台資訊供前端 Sidebar 顯示。

        Returns:
            {os, env_type, suggested_mode, current_mode}
        """
        def _do() -> dict:
            from src.platform_utils import detect_platform as _detect

            info = _detect()
            return _ok({
                "os": info.os_name,
                "env_type": "docker" if info.is_docker else "native",
                "suggested_mode": info.deployment_mode,
                "current_mode": self._config_manager.get_deployment_mode(),
            })

        return self._safe_call(_do)

    # ── Registry API (3.7, Config Step 2) ─────────────────

    def get_available_providers(self) -> dict:
        """回傳可選的 Model Provider 清單（含 env_var / placeholder）。"""
        from src.registries import PROVIDER_REGISTRY

        return _ok(PROVIDER_REGISTRY)

    def get_available_channels(self) -> dict:
        """回傳可選的 Channel 清單（含 fields / icon / icon_color）。"""
        from src.registries import CHANNEL_REGISTRY

        return _ok(CHANNEL_REGISTRY)

    def get_available_tools(self) -> dict:
        """回傳可選的 Tool API Key 清單。"""
        from src.registries import TOOL_REGISTRY

        return _ok(TOOL_REGISTRY)

    # ── 設定管理 API (3.5, US-002) ────────────────────────

    def load_config(self) -> dict:
        """讀取 gui-settings.json 已儲存的設定。

        Returns:
            {config_dir?, workspace_dir?, gateway_bind?, gateway_mode?,
             gateway_port?, bridge_port?, timezone?, docker_image?,
             deployment_mode?, sandbox?, ssh_host?, ssh_port?, ...}
        """
        def _do() -> dict:
            return _ok(self._config_manager.read_gui_settings())

        return self._safe_call(_do)

    def save_config(self, config: dict) -> dict:
        """持久化 GUI 設定至 gui-settings.json。

        Args:
            config: {deployment_mode, ssh_host?, ssh_port?, ssh_username?, ssh_key_path?}
        """
        def _do() -> dict:
            self._config_manager.write_gui_settings(config)
            return _ok({"message": "Configuration saved"})

        return self._safe_call(_do)

    def save_keys(self, keys: dict) -> dict:
        """儲存 API 金鑰至系統 keyring（分類式）。

        Args:
            keys: {providers: {key: val}, channels: {key: val}, tools: {key: val}}
        """
        def _do() -> dict:
            flat: dict[str, str] = {}
            for category in ("providers", "channels", "tools"):
                flat.update(keys.get(category, {}))
            count = self._config_manager.set_secrets_batch(flat)
            return _ok({"saved_count": count})

        return self._safe_call(_do)

    def get_openclaw_config(self, config_dir: str, section: str | None = None) -> dict:
        """讀取 openclaw.json 設定檔。

        Args:
            config_dir: OpenClaw 設定目錄路徑（如 ~/.openclaw）
            section: 指定 section 名稱，None 回傳全部
        """
        def _do() -> dict:
            data = self._config_manager.read_openclaw_config(config_dir, section)
            return _ok(data)

        return self._safe_call(_do)

    def save_openclaw_config(self, config_dir: str, section: str, data: dict) -> dict:
        """更新 openclaw.json 指定 section（deep merge 策略）。

        Args:
            config_dir: OpenClaw 設定目錄路徑
            section: section 名稱（meta/agents/channels/gateway/plugins/tools/commands）
            data: 要合併的資料
        """
        def _do() -> dict:
            self._config_manager.write_openclaw_config(config_dir, data, section)
            return _ok({"message": f"Section '{section}' updated"})

        return self._safe_call(_do)

    # ── 初始化 API (3.8, US-003) ──────────────────────────

    def initialize(self, params: dict) -> dict:
        """啟動初始化流程（非同步，透過回呼更新進度）。

        Args:
            params: {mode, config_dir, workspace_dir, gateway_bind,
                     gateway_mode, gateway_port, bridge_port, timezone, docker_image}

        Returns:
            {success, steps, error, gateway_token}
        """
        def _do() -> dict:
            from src.initializer import InitParams, Initializer

            init_params = InitParams(**params)
            initializer = Initializer(self._executor, self._config_manager)
            result = self._run_async(
                initializer.run_all(init_params, on_step=self._notify_init_progress)
            )
            return _ok(result)

        return self._safe_call(_do)

    # ── 檔案選擇 API ────────────────────────────────────

    def browse_file(
        self,
        title: str = "Select File",
        file_types: list[str] | None = None,
    ) -> dict:
        """開啟原生檔案選擇對話框。

        Args:
            title: 對話框標題
            file_types: 檔案類型過濾（如 ["Key Files (*.pem;*.key;*)", "All Files (*.*)"]）
        """
        if not self._window:
            return _err(ErrorType.INTERNAL, "Window not initialized")
        ft = tuple(file_types) if file_types else ("All Files (*.*)",)
        result = self._window.create_file_dialog(
            webview.OPEN_DIALOG, allow_multiple=False, file_types=ft
        )
        path = result[0] if result else None
        return _ok({"path": path})

    # ── SSH 連線管理 API (3.3.4, ADR-004) ────────────────

    def _on_ssh_state_change(self, state: ConnectionState) -> None:
        """SSH 連線狀態變化時通知前端。"""
        self._notify_connection_status(state.value, f"SSH {state.value}")

    def _build_ssh_config(self, params: dict) -> SSHConnectionConfig:
        return SSHConnectionConfig(
            host=params["host"],
            username=params["username"],
            port=params.get("port", 22),
            key_path=params.get("key_path"),
            password=params.get("password"),
        )

    async def _get_server_info(self, executor: Executor) -> dict:
        """透過 Executor 取得遠端伺服器資訊。"""
        os_result = await executor.run_command(["uname", "-s"], timeout=10)
        cpu_result = await executor.run_command(["nproc"], timeout=10)
        mem_result = await executor.run_command(
            ["awk", "/MemTotal/{printf \"%.1f\", $2/1024/1024}", "/proc/meminfo"],
            timeout=10,
        )
        disk_result = await executor.run_command(
            ["df", "-BG", "--output=size", "/"],
            timeout=10,
        )

        def _parse_disk(output: str) -> str:
            lines = output.strip().splitlines()
            return lines[-1].strip().rstrip("G") if len(lines) > 1 else "?"

        return {
            "os": os_result.stdout.strip() if os_result.success else "unknown",
            "cpu_cores": cpu_result.stdout.strip() if cpu_result.success else "?",
            "memory_gb": mem_result.stdout.strip() if mem_result.success else "?",
            "disk_gb": _parse_disk(disk_result.stdout) if disk_result.success else "?",
        }

    def test_connection(self, params: dict) -> dict:
        """測試 SSH 連線（不持久化）。

        Args:
            params: {host, username, port?, key_path?, password?}

        Returns:
            {success, server_info: {os, cpu_cores, memory_gb, disk_gb}}
        """
        def _do() -> dict:
            config = self._build_ssh_config(params)
            conn = SSHConnection(config)
            try:
                self._run_async(conn.connect())
                executor = RemoteExecutor(conn)
                server_info = self._run_async(self._get_server_info(executor))
                return _ok({"server_info": server_info})
            except paramiko.AuthenticationException as exc:
                return _err(ErrorType.AUTH_FAILED, str(exc))
            finally:
                self._run_async(conn.disconnect())

        return self._safe_call(_do)

    def connect_remote(self, params: dict) -> dict:
        """建立 SSH 連線並切換至 RemoteExecutor。

        Args:
            params: {host, username, port?, key_path?, password?}

        Returns:
            {success, server_info: {os, cpu_cores, memory_gb, disk_gb}}
        """
        def _do() -> dict:
            # 若已連線，先斷線
            if self._ssh_connection and self._ssh_connection.state == ConnectionState.CONNECTED:
                self._run_async(self._ssh_connection.disconnect())

            config = self._build_ssh_config(params)
            conn = SSHConnection(config, on_state_change=self._on_ssh_state_change)
            self._run_async(conn.connect())

            executor = RemoteExecutor(conn)
            server_info = self._run_async(self._get_server_info(executor))

            # 持久化連線並切換 executor
            self._ssh_connection = conn
            self._remote_executor = executor
            self._switch_executor(executor)

            return _ok({"server_info": server_info})

        return self._safe_call(_do)

    def disconnect_remote(self) -> dict:
        """中斷 SSH 連線並切回 LocalExecutor。"""
        def _do() -> dict:
            if self._ssh_connection:
                self._run_async(self._ssh_connection.disconnect())
                self._ssh_connection = None
                self._remote_executor = None

            self._switch_executor(self._local_executor)
            return _ok()

        return self._safe_call(_do)

    def get_connection_status(self) -> dict:
        """查詢當前 SSH 連線狀態。

        Returns:
            {connected, status, host, uptime}
        """
        if not self._ssh_connection:
            return _ok({
                "connected": False,
                "status": ConnectionState.DISCONNECTED.value,
                "host": None,
                "uptime": None,
            })

        conn = self._ssh_connection
        return _ok({
            "connected": conn.state == ConnectionState.CONNECTED,
            "status": conn.state.value,
            "host": f"{conn.config.host}:{conn.config.port}",
            "uptime": None,  # TODO: track connect timestamp
        })


def _js_escape(s: str) -> str:
    """轉義字串以安全嵌入 JavaScript 單引號字串。"""
    return s.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n").replace("\r", "\\r")
