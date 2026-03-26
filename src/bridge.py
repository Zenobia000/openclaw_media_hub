"""Bridge API — PyWebView 前端 Bridge 類別。

所有 public method 自動暴露為 window.pywebview.api.* 供前端呼叫。
回傳格式統一: {"success": True/False, "data": ..., "error": ...}
"""

from __future__ import annotations

import asyncio
import enum
import functools
import json
import logging
import socket
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


# ── 回傳格式與錯誤處理 ──────────────────────────────────


class ErrorType(enum.Enum):
    """Bridge API 錯誤類型。"""

    TIMEOUT = "TIMEOUT"
    PERMISSION = "PERMISSION"
    NOT_FOUND = "NOT_FOUND"
    INTERNAL = "INTERNAL"
    CONNECTION_LOST = "CONNECTION_LOST"
    AUTH_FAILED = "AUTH_FAILED"
    SFTP_TIMEOUT = "SFTP_TIMEOUT"


def _ok(data: Any = None) -> dict:
    """統一成功回傳。"""
    return {"success": True, "data": data, "error": None}


def _err(error_type: ErrorType, message: str) -> dict:
    """統一失敗回傳。"""
    return {
        "success": False,
        "data": None,
        "error": {"type": error_type.value, "message": message},
    }


def _map_exception(exc: Exception) -> dict:
    """將例外映射為結構化錯誤回傳。"""
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
    return _err(ErrorType.INTERNAL, str(exc) or "Internal error")


def _bridge_api(method):
    """裝飾器 — Bridge API 統一例外處理。"""
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except Exception as exc:
            logger.exception("Bridge API error")
            return _map_exception(exc)
    return wrapper


def _js_escape(s: str) -> str:
    """轉義字串以安全嵌入 JavaScript 單引號字串。"""
    return s.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n").replace("\r", "\\r")


# ── Bridge 本體 ─────────────────────────────────────────


class Bridge:
    """PyWebView Bridge API。

    每個 public method 自動暴露為前端 JavaScript API。
    預設 LocalExecutor（本機），SSH 連線後切換 RemoteExecutor（遠端）。
    """

    # Gateway 預設埠號
    _DEFAULT_GATEWAY_PORT = 18789

    # 認證模式 → (顯示標籤, 預設是否有憑證)
    _AUTH_MODES: dict[str, tuple[str, bool]] = {
        "token": ("Token", False),
        "password": ("Password", False),
        "none": ("None (open)", True),
        "trusted-proxy": ("Trusted Proxy", True),
    }

    # 綁定模式 → 主機位址
    _BIND_HOSTS: dict[str, str] = {
        "loopback": "127.0.0.1",
        "auto": "127.0.0.1",
        "lan": "0.0.0.0",
        "tailnet": "100.x.x.x",
    }

    def __init__(self) -> None:
        self._local_executor = LocalExecutor()
        self._executor: Executor = self._local_executor
        self._process_manager = ProcessManager(self._executor)
        self._config_manager = ConfigManager()
        self._window: webview.Window | None = None
        self._ssh_connection: SSHConnection | None = None
        self._remote_executor: RemoteExecutor | None = None

        # 進度回呼捷徑（functools.partial 取代 lambda，更清晰）
        self._notify_init_progress = functools.partial(self._notify_progress, "updateInitProgress")
        self._notify_deploy_progress = functools.partial(self._notify_progress, "updateDeployProgress")
        self._notify_plugin_progress = functools.partial(self._notify_progress, "updatePluginProgress")
        self._notify_fix_progress = functools.partial(self._notify_progress, "updateFixProgress")
        self._notify_connection_status = functools.partial(self._notify_progress, "updateConnectionStatus")

    # ── 基礎設施 ────────────────────────────────────────

    def set_window(self, window: webview.Window) -> None:
        """註冊 PyWebView 視窗實例（由 main.py 呼叫）。"""
        self._window = window

    @property
    def executor(self) -> Executor:
        return self._executor

    @property
    def _is_remote(self) -> bool:
        """當前是否為 SSH 遠端模式。"""
        return self._remote_executor is not None

    def _get_config_dir(self) -> str:
        """取得目標機器設定目錄路徑。"""
        settings = self._config_manager.read_gui_settings()
        return settings.get("config_dir", "~/.openclaw")

    def _switch_executor(self, executor: Executor) -> None:
        """切換 Executor（Local ↔ Remote）。"""
        self._executor = executor
        self._process_manager.executor = executor

    def _notify_progress(self, callback_name: str, *args: str) -> None:
        """呼叫前端全域進度回呼函式。"""
        if self._window:
            escaped_args = ", ".join(f"'{_js_escape(a)}'" for a in args)
            self._window.evaluate_js(f"window.{callback_name}({escaped_args})")

    def _run_async(self, coro: Any) -> Any:
        """在新事件迴圈中執行 async 協程（Bridge 方法為同步）。"""
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    # ── 連線測試 ────────────────────────────────────────

    def ping(self) -> dict:
        """前端確認 Bridge 可用。"""
        return _ok({"message": "pong"})

    # ── 環境檢查 ────────────────────────────────────────

    @_bridge_api
    def check_env(self) -> dict:
        """依部署模式檢查系統依賴。"""
        from src.env_checker import EnvChecker
        from src.platform_utils import detect_platform as _detect

        mode = _detect().deployment_mode
        checker = EnvChecker(self._executor)
        checks = self._run_async(checker.check_all(mode))
        env_file = self._run_async(checker.check_env_file(".env"))
        return _ok({"checks": checks, "env_file": env_file})

    @_bridge_api
    def detect_platform(self) -> dict:
        """偵測平台資訊供前端 Sidebar 顯示。"""
        from src.platform_utils import detect_platform as _detect

        info = _detect()
        return _ok({
            "os": info.os_name,
            "env_type": "docker" if info.is_docker else "native",
            "suggested_mode": info.deployment_mode,
            "current_mode": self._config_manager.get_deployment_mode(),
        })

    # ── Registry ────────────────────────────────────────

    def get_available_providers(self) -> dict:
        """回傳可選的 Model Provider 清單。"""
        from src.registries import PROVIDER_REGISTRY
        return _ok(PROVIDER_REGISTRY)

    def get_available_channels(self) -> dict:
        """回傳可選的 Channel 清單。"""
        from src.registries import CHANNEL_REGISTRY
        return _ok(CHANNEL_REGISTRY)

    def get_available_tools(self) -> dict:
        """回傳可選的 Tool API Key 清單。"""
        from src.registries import TOOL_REGISTRY
        return _ok(TOOL_REGISTRY)

    # ── 設定管理 ────────────────────────────────────────

    @_bridge_api
    def load_env_keys(self) -> dict:
        """從目標機器 .env 讀取 API 金鑰，依 registry 分類回傳。"""
        from src.config_manager import ConfigManager
        from src.registries import CHANNEL_REGISTRY, PROVIDER_REGISTRY, TOOL_REGISTRY

        env_path = f"{self._get_config_dir()}/.env"

        # 依 Executor 類型讀取 .env
        if isinstance(self._executor, RemoteExecutor):
            try:
                content = self._run_async(self._executor.read_file(env_path))
                env_data = ConfigManager.parse_env_content(
                    content if isinstance(content, str) else content.decode("utf-8")
                )
            except Exception:
                env_data = {}
        else:
            env_data = self._config_manager.read_env(env_path)

        if not env_data:
            return _ok({"providers": {}, "channels": {}, "tools": {}})

        # 建立各分類的已知環境變數集合
        provider_vars = {p["env_var"] for p in PROVIDER_REGISTRY if p.get("env_var")}
        channel_vars = {f["key"] for ch in CHANNEL_REGISTRY for f in ch.get("fields", [])}
        tool_vars = {t["env_var"] for t in TOOL_REGISTRY if t.get("env_var")}

        result: dict[str, dict[str, str]] = {"providers": {}, "channels": {}, "tools": {}}
        for key, value in env_data.items():
            if key in provider_vars:
                result["providers"][key] = value
            elif key in channel_vars:
                result["channels"][key] = value
            elif key in tool_vars:
                result["tools"][key] = value

        return _ok(result)

    @_bridge_api
    def load_config(self) -> dict:
        """讀取 gui-settings.json 已儲存的設定。"""
        return _ok(self._config_manager.read_gui_settings())

    @_bridge_api
    def save_config(self, config: dict) -> dict:
        """持久化 GUI 設定至 gui-settings.json。"""
        self._config_manager.write_gui_settings(config)
        return _ok({"message": "Configuration saved"})

    @_bridge_api
    def save_keys(self, keys: dict) -> dict:
        """儲存 API 金鑰至目標機器 .env。"""
        flat: dict[str, str] = {}
        for category in ("providers", "channels", "tools"):
            for k, v in keys.get(category, {}).items():
                if v:
                    flat[k] = v
        env_path = f"{self._get_config_dir()}/.env"
        self._config_manager.write_env(env_path, flat)
        return _ok({"saved_count": len(flat)})

    @_bridge_api
    def get_openclaw_config(self, config_dir: str, section: str | None = None) -> dict:
        """讀取 openclaw.json 設定檔。"""
        return _ok(self._config_manager.read_openclaw_config(config_dir, section))

    @_bridge_api
    def save_openclaw_config(self, config_dir: str, section: str, data: dict) -> dict:
        """更新 openclaw.json 指定 section（deep merge）。"""
        self._config_manager.write_openclaw_config(config_dir, data, section)
        return _ok({"message": f"Section '{section}' updated"})

    # ── 初始化 ──────────────────────────────────────────

    @_bridge_api
    def initialize(self, params: dict) -> dict:
        """啟動初始化流程，透過回呼更新進度。"""
        from src.initializer import InitParams, Initializer

        init_params = InitParams(**params)
        initializer = Initializer(self._executor, self._config_manager)
        result = self._run_async(
            initializer.run_all(init_params, on_step=self._notify_init_progress)
        )
        return _ok(result)

    # ── 裝置管理 ────────────────────────────────────────

    def _build_openclaw_cmd(self, subcmd: list[str]) -> list[str]:
        """組合 openclaw CLI 指令（自動判斷 Docker/Native 前綴）。"""
        mode = self._config_manager.get_deployment_mode() or "docker-windows"
        if mode in ("docker-windows", "docker-linux", "remote-ssh"):
            return ["docker", "compose", "exec", "openclaw-gateway", "openclaw", *subcmd]
        return ["openclaw", *subcmd]

    def _list_devices_raw(self) -> dict:
        """執行 devices list 指令並解析 JSON。"""
        args = self._build_openclaw_cmd(["devices", "list", "--json"])
        result = self._run_async(self._executor.run_command(args, timeout=30))
        if not result.success:
            return _err(ErrorType.INTERNAL, f"Failed to list devices: {result.stderr[:200]}")
        try:
            return _ok(json.loads(result.stdout))
        except json.JSONDecodeError:
            return _err(ErrorType.INTERNAL, "Failed to parse device list output")

    def _device_action(self, params: dict, *, param_key: str, subcmd: str, label: str) -> dict:
        """執行裝置管理指令（approve/reject/remove 共用邏輯）。"""
        id_val = (params.get(param_key) or "").strip()
        if not id_val:
            return _err(ErrorType.INTERNAL, f"{label} ID is required")
        args = self._build_openclaw_cmd(["devices", subcmd, id_val])
        result = self._run_async(self._executor.run_command(args, timeout=30))
        if not result.success:
            return _err(ErrorType.INTERNAL, f"Failed to {subcmd} device: {result.stderr[:200]}")
        return _ok({"message": f"Device {subcmd}d", "output": result.stdout})

    @_bridge_api
    def list_pending_devices(self) -> dict:
        """列出等待核准的裝置配對請求。"""
        resp = self._list_devices_raw()
        if not resp["success"]:
            return resp
        return _ok({"devices": resp["data"].get("pending", [])})

    @_bridge_api
    def approve_device(self, params: dict) -> dict:
        """核准指定裝置配對請求。"""
        return self._device_action(params, param_key="request_id", subcmd="approve", label="Device request")

    @_bridge_api
    def list_devices(self) -> dict:
        """列出所有裝置（pending + paired）。"""
        resp = self._list_devices_raw()
        if not resp["success"]:
            return resp
        return _ok({
            "pending": resp["data"].get("pending", []),
            "paired": resp["data"].get("paired", []),
        })

    @_bridge_api
    def reject_device(self, params: dict) -> dict:
        """拒絕 pending 裝置配對請求。"""
        return self._device_action(params, param_key="request_id", subcmd="reject", label="Device request")

    @_bridge_api
    def remove_device(self, params: dict) -> dict:
        """移除已配對裝置。"""
        return self._device_action(params, param_key="device_id", subcmd="remove", label="Device")

    # ── Gateway 控制 ────────────────────────────────────

    @_bridge_api
    def get_gateway_info(self) -> dict:
        """讀取 Gateway 連線資訊（URL + Auth + Token）。"""
        config_dir = self._get_config_dir()
        gateway = self._config_manager.read_openclaw_config(config_dir, "gateway")

        port = gateway.get("port", self._DEFAULT_GATEWAY_PORT)
        bind_mode = gateway.get("bind", "loopback")
        tls_enabled = gateway.get("tls", {}).get("enabled", False)
        scheme = "wss" if tls_enabled else "ws"

        # 解析主機位址
        host = (gateway.get("customBindHost", "0.0.0.0")
                if bind_mode == "custom"
                else self._BIND_HOSTS.get(bind_mode, "127.0.0.1"))

        # 解析認證資訊
        auth = gateway.get("auth", {})
        auth_mode = auth.get("mode", "token")
        auth_label, has_credential = self._AUTH_MODES.get(auth_mode, (auth_mode, False))
        if not has_credential and auth_mode in ("token", "password"):
            has_credential = bool(auth.get(auth_mode))

        # 讀取 .env 中的 Gateway Token
        gateway_token = None
        try:
            env_data = self._config_manager.read_env(f"{config_dir}/.env")
            gateway_token = env_data.get("OPENCLAW_GATEWAY_TOKEN") or None
        except Exception:
            pass
        if gateway_token:
            has_credential = True

        return _ok({
            "url": f"{scheme}://{host}:{port}",
            "port": port, "bind": bind_mode, "tls": tls_enabled,
            "auth_mode": auth_mode, "auth_label": auth_label,
            "has_credential": has_credential, "gateway_token": gateway_token,
        })

    @_bridge_api
    def get_allowed_origins(self) -> dict:
        """讀取 Gateway controlUi.allowedOrigins。"""
        config_dir = self._get_config_dir()
        gateway = self._config_manager.read_openclaw_config(config_dir, "gateway")
        origins = gateway.get("controlUi", {}).get("allowedOrigins")
        allow_all = origins is not None and "*" in origins
        return _ok({"origins": origins, "allow_all": allow_all})

    @_bridge_api
    def save_allowed_origins(self, params: dict) -> dict:
        """寫入 Gateway controlUi.allowedOrigins。"""
        allow_all = params.get("allow_all", False)
        origins = ["*"] if allow_all else params.get("origins", [])
        self._config_manager.write_openclaw_config(
            self._get_config_dir(),
            {"controlUi": {"allowedOrigins": origins}},
            "gateway",
        )
        return _ok({"message": "Allowed origins saved"})

    @_bridge_api
    def save_device_note(self, params: dict) -> dict:
        """儲存裝置備註至 gui-settings.json。"""
        device_id = (params.get("device_id") or "").strip()
        note = params.get("note", "").strip()
        if not device_id:
            return _err(ErrorType.INTERNAL, "Device ID is required")

        settings = self._config_manager.read_gui_settings()
        notes = settings.get("device_notes", {})
        if note:
            notes[device_id] = note
        else:
            notes.pop(device_id, None)
        self._config_manager.write_gui_settings({"device_notes": notes})
        return _ok({"message": "Note saved"})

    @_bridge_api
    def get_device_notes(self) -> dict:
        """讀取所有裝置備註。"""
        settings = self._config_manager.read_gui_settings()
        return _ok({"notes": settings.get("device_notes", {})})

    # ── 檔案選擇 ────────────────────────────────────────

    def browse_file(
        self,
        title: str = "Select File",
        file_types: list[str] | None = None,
    ) -> dict:
        """開啟原生檔案選擇對話框。"""
        if not self._window:
            return _err(ErrorType.INTERNAL, "Window not initialized")
        ft = tuple(file_types) if file_types else ("All Files (*.*)",)
        result = self._window.create_file_dialog(
            webview.OPEN_DIALOG, allow_multiple=False, file_types=ft
        )
        path = result[0] if result else None
        return _ok({"path": path})

    # ── SSH 連線管理 ────────────────────────────────────

    def _on_ssh_state_change(self, state: ConnectionState) -> None:
        """SSH 連線狀態變化時通知前端。"""
        self._notify_connection_status(state.value, f"SSH {state.value}")

    def _build_ssh_config(self, params: dict) -> SSHConnectionConfig:
        """從前端參數建構 SSH 連線設定。"""
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
            ["df", "-BG", "--output=size", "/"], timeout=10,
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

    @_bridge_api
    def test_connection(self, params: dict) -> dict:
        """測試 SSH 連線（不持久化）。"""
        config = self._build_ssh_config(params)
        conn = SSHConnection(config)
        try:
            self._run_async(conn.connect())
            executor = RemoteExecutor(conn)
            server_info = self._run_async(self._get_server_info(executor))
            return _ok({"server_info": server_info})
        finally:
            self._run_async(conn.disconnect())

    @_bridge_api
    def connect_remote(self, params: dict) -> dict:
        """建立 SSH 連線並切換至 RemoteExecutor。"""
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

    @_bridge_api
    def disconnect_remote(self) -> dict:
        """中斷 SSH 連線並切回 LocalExecutor。"""
        if self._ssh_connection:
            self._run_async(self._ssh_connection.disconnect())
            self._ssh_connection = None
            self._remote_executor = None
        self._switch_executor(self._local_executor)
        return _ok()

    def get_connection_status(self) -> dict:
        """查詢當前 SSH 連線狀態。"""
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

    # ── 服務控制 ────────────────────────────────────────

    def _build_service_controller(self):
        """建構 ServiceController（根據當前部署模式）。"""
        from src.service_controller import ServiceController

        mode = self._config_manager.get_deployment_mode() or "docker-windows"
        return ServiceController(
            self._executor, deployment_mode=mode, config_dir=self._get_config_dir(),
        )

    def _service_action(self, action: str) -> dict:
        """執行服務控制操作（start/stop/restart/status 共用）。"""
        ctrl = self._build_service_controller()
        return _ok(self._run_async(getattr(ctrl, action)()))

    @_bridge_api
    def get_service_status(self) -> dict:
        """查詢服務狀態。"""
        return self._service_action("status")

    @_bridge_api
    def start_service(self) -> dict:
        """啟動服務。"""
        return self._service_action("start")

    @_bridge_api
    def stop_service(self) -> dict:
        """停止服務。"""
        return self._service_action("stop")

    @_bridge_api
    def restart_service(self) -> dict:
        """重啟服務。"""
        return self._service_action("restart")

    # ── 技能部署 ────────────────────────────────────────

    def _build_skill_manager(self):
        """建構 SkillManager（根據當前 executor 模式）。"""
        from src.skill_manager import SkillManager
        from src.transfer_service import TransferService

        config_dir = self._get_config_dir()
        transfer = TransferService(self._local_executor, self._executor) if self._is_remote else None

        return SkillManager(
            self._executor,
            module_pack_dir="./module_pack",
            community_skills_dir="./openclaw/skills",
            config_dir=config_dir,
            local_executor=self._local_executor if self._is_remote else None,
            transfer_service=transfer,
            on_progress=self._notify_deploy_progress,
        )

    @_bridge_api
    def list_skills(self) -> dict:
        """列出所有可用技能（含部署狀態）。"""
        return _ok(self._run_async(self._build_skill_manager().list_skills()))

    @_bridge_api
    def deploy_skills(self, names: list) -> dict:
        """部署指定技能至工作空間。"""
        return _ok(self._run_async(self._build_skill_manager().deploy_skills(names)))

    @_bridge_api
    def remove_skills(self, names: list) -> dict:
        """從工作空間移除指定技能。"""
        return _ok(self._run_async(self._build_skill_manager().remove_skills(names)))

    # ── 外掛管理 ────────────────────────────────────────

    def _build_plugin_manager(self):
        """建構 PluginManager（根據當前 executor 模式）。"""
        from src.plugin_manager import PluginManager

        return PluginManager(
            self._executor,
            extensions_dir="./openclaw/extensions",
            config_dir=self._get_config_dir(),
            local_executor=self._local_executor if self._is_remote else None,
            on_progress=self._notify_plugin_progress,
        )

    @_bridge_api
    def list_plugins(self) -> dict:
        """列出所有可用外掛（含安裝狀態）。"""
        return _ok(self._run_async(self._build_plugin_manager().list_plugins()))

    @_bridge_api
    def install_plugins(self, ids: list) -> dict:
        """安裝指定外掛。"""
        return _ok(self._run_async(self._build_plugin_manager().install_plugins(ids)))

    @_bridge_api
    def uninstall_plugins(self, ids: list) -> dict:
        """移除指定外掛。"""
        return _ok(self._run_async(self._build_plugin_manager().uninstall_plugins(ids)))

    @_bridge_api
    def diagnose_plugins(self) -> dict:
        """診斷已安裝外掛的健康狀態。"""
        return _ok(self._run_async(self._build_plugin_manager().diagnose_plugins()))

    @_bridge_api
    def fix_plugins(self, ids: list) -> dict:
        """修復指定外掛。"""
        mgr = self._build_plugin_manager()
        mgr._on_progress = self._notify_fix_progress
        return _ok(self._run_async(mgr.fix_plugins(ids)))

    @_bridge_api
    def fix_all_plugins(self) -> dict:
        """修復所有有問題的外掛。"""
        mgr = self._build_plugin_manager()
        mgr._on_progress = self._notify_fix_progress
        return _ok(self._run_async(mgr.fix_all_plugins()))
