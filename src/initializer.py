"""Initializer — 初始化邏輯 (目錄建立、config 產生、docker compose)。

依序執行初始化流程（Docker 11 步 / Native 8 步）：
驗證環境、建立目錄結構、產生設定檔、Build/Pull Docker Image、
Onboarding、同步 Gateway 設定、啟動 Gateway、Health Check。

所有操作透過 Executor 介面，自然支援本機 / SSH 遠端模式 (ADR-004)。
"""

from __future__ import annotations

import asyncio
import json
import logging
import secrets
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import PurePosixPath

from src.config_manager import ConfigManager
from src.executor import Executor

logger = logging.getLogger(__name__)


@dataclass
class InitParams:
    """初始化參數（由前端 Step 1 + Step 2 收集）。"""

    mode: str  # "docker-windows" | "docker-linux" | "native-linux" | "remote-ssh"
    config_dir: str  # e.g. "~/.openclaw"
    workspace_dir: str  # e.g. "~/.openclaw/workspace"
    gateway_bind: str  # "loopback" | "lan"
    gateway_port: int  # 18789
    bridge_port: int  # 18790
    timezone: str  # "Asia/Taipei"
    docker_image: str  # "openclaw:local"

    @property
    def is_docker(self) -> bool:
        return self.mode in ("docker-windows", "docker-linux", "remote-ssh")

    @property
    def is_native(self) -> bool:
        return self.mode == "native-linux"


StepFn = Callable[["Initializer", InitParams], "asyncio.coroutine"]


def _step_result(success: bool, message: str) -> dict:
    return {"success": success, "message": message}


class Initializer:
    """系統初始化執行器。"""

    def __init__(self, executor: Executor, config_manager: ConfigManager) -> None:
        self._executor = executor
        self._config_manager = config_manager
        self._gateway_token: str | None = None

    # ── Step Methods ─────────────────────────────────────

    async def _step_validate_docker(self, params: InitParams) -> dict:
        """Step 1 (Docker): 驗證 Docker + Docker Compose 可用性。"""
        docker_path = await self._executor.which("docker")
        if not docker_path:
            return _step_result(False, "Docker not found — please install Docker Desktop")

        # Check Docker version
        result = await self._executor.run_command(["docker", "--version"], timeout=10)
        if not result.success:
            return _step_result(False, f"Docker version check failed: {result.stderr}")

        # Check Docker Compose
        compose_result = await self._executor.run_command(
            ["docker", "compose", "version"], timeout=10
        )
        if not compose_result.success:
            return _step_result(False, "Docker Compose not found — please install Docker Compose V2")

        # Check daemon running
        ping_result = await self._executor.run_command(["docker", "info"], timeout=15)
        if not ping_result.success:
            return _step_result(False, "Docker daemon is not running — please start Docker Desktop")

        return _step_result(True, f"Docker OK ({result.stdout.strip()})")

    async def _step_validate_native(self, params: InitParams) -> dict:
        """Step 1 (Native): 驗證 Node.js + OpenClaw CLI + systemd。"""
        node_path = await self._executor.which("node")
        if not node_path:
            return _step_result(False, "Node.js not found — please install Node.js 18+")

        cli_path = await self._executor.which("openclaw")
        if not cli_path:
            return _step_result(False, "OpenClaw CLI not found — please install via npm")

        systemctl_path = await self._executor.which("systemctl")
        if not systemctl_path:
            return _step_result(False, "systemctl not found — systemd is required for native mode")

        return _step_result(True, "Node.js, OpenClaw CLI, systemd OK")

    async def _step_validate_env(self, params: InitParams) -> dict:
        """Step 2: 驗證環境參數完整性。"""
        missing = []
        if not params.config_dir:
            missing.append("config_dir")
        if not params.workspace_dir:
            missing.append("workspace_dir")
        if not params.gateway_port:
            missing.append("gateway_port")
        if missing:
            return _step_result(False, f"Missing required parameters: {', '.join(missing)}")
        return _step_result(True, "All parameters validated")

    async def _step_create_dirs(self, params: InitParams) -> dict:
        """Step 3: 建立目錄結構。"""
        dirs = [
            f"{params.config_dir}/identity",
            f"{params.config_dir}/agents/main/agent",
            f"{params.config_dir}/agents/main/sessions",
            params.workspace_dir,
            f"{params.workspace_dir}/skills",
        ]
        for d in dirs:
            await self._executor.mkdir(d, parents=True)
        return _step_result(True, f"Created {len(dirs)} directories")

    async def _step_gateway_token(self, params: InitParams) -> dict:
        """Step 4: 解析/產生 Gateway Token。"""
        token = None

        # 1. Try reading from openclaw.json
        try:
            config = self._config_manager.read_openclaw_config(params.config_dir, "gateway")
            token = config.get("token")
        except Exception:
            pass

        # 2. Try reading from .env
        if not token:
            try:
                env_path = f"{params.config_dir}/.env"
                env_data = self._config_manager.read_env(env_path)
                token = env_data.get("OPENCLAW_GATEWAY_TOKEN")
            except Exception:
                pass

        # 3. Generate new token
        if not token:
            token = secrets.token_hex(32)
            logger.info("Generated new gateway token")

        self._gateway_token = token
        return _step_result(True, f"Gateway token ready ({token[:8]}...)")

    async def _step_write_env(self, params: InitParams) -> dict:
        """Step 5: 寫入 .env 檔案（16+ 環境變數 upsert）。"""
        env_path = f"{params.config_dir}/.env"
        env_vars = {
            "OPENCLAW_IMAGE": params.docker_image,
            "OPENCLAW_CONFIG_DIR": params.config_dir,
            "OPENCLAW_WORKSPACE_DIR": params.workspace_dir,
            "OPENCLAW_GATEWAY_BIND": params.gateway_bind,
            "OPENCLAW_GATEWAY_PORT": str(params.gateway_port),
            "OPENCLAW_BRIDGE_PORT": str(params.bridge_port),
            "OPENCLAW_GATEWAY_TOKEN": self._gateway_token or "",
            "OPENCLAW_TZ": params.timezone,
            "OPENCLAW_ALLOW_INSECURE_PRIVATE_WS": "true",
            "OPENCLAW_DOCKER_SOCKET": "/var/run/docker.sock",
        }
        # Add sandbox if configured
        sandbox = self._config_manager.read_gui_settings().get("sandbox", True)
        if sandbox:
            env_vars["OPENCLAW_SANDBOX"] = "1"

        self._config_manager.write_env(env_path, env_vars)
        return _step_result(True, f"Wrote {len(env_vars)} variables to .env")

    async def _step_docker_image(self, params: InitParams) -> dict:
        """Step 6 (Docker only): Build 或 Pull Docker Image。"""
        if params.docker_image.endswith(":local"):
            result = await self._executor.run_command(
                ["docker", "compose", "build"],
                timeout=600,
            )
        else:
            result = await self._executor.run_command(
                ["docker", "compose", "pull"],
                timeout=600,
            )
        if not result.success:
            return _step_result(False, f"Docker image failed: {result.stderr[:200]}")
        return _step_result(True, f"Docker image ready ({params.docker_image})")

    async def _step_fix_permissions(self, params: InitParams) -> dict:
        """Step 7 (Docker only): 修正資料目錄權限。

        使用 openclaw-gateway service 而非 openclaw-cli，因為 cli 的
        network_mode: service:openclaw-gateway 要求 gateway 容器必須存在。
        """
        result = await self._executor.run_command(
            [
                "docker", "compose", "run", "--rm", "--no-deps",
                "openclaw-gateway", "chown", "-R", "1000:1000", "/home/node/.openclaw",
            ],
            timeout=60,
        )
        if not result.success:
            # Permission fix is best-effort — warn but don't fail
            logger.warning("Permission fix returned non-zero: %s", result.stderr)
            return _step_result(True, "Permission fix completed (with warnings)")
        return _step_result(True, "Directory permissions fixed")

    async def _step_onboarding(self, params: InitParams) -> dict:
        """Step 8 (Docker): 執行 Onboarding（初次設定 agent/session）。"""
        result = await self._executor.run_command(
            [
                "docker", "compose", "run", "--rm",
                "openclaw-cli", "onboard",
                "--mode", "local",
                "--no-install-daemon",
            ],
            timeout=120,
        )
        if not result.success:
            return _step_result(False, f"Onboarding failed: {result.stderr[:200]}")
        return _step_result(True, "Onboarding completed")

    async def _step_sync_gateway(self, params: InitParams) -> dict:
        """Step 9: 同步 Gateway 設定至 openclaw.json。"""
        gateway_data = {
            "mode": "local",
            "bind": params.gateway_bind,
            "controlUi": {
                "allowedOrigins": [
                    f"http://127.0.0.1:{params.gateway_port}",
                    f"http://localhost:{params.gateway_port}",
                    f"http://127.0.0.1:{params.bridge_port}",
                ],
            },
        }
        self._config_manager.write_openclaw_config(
            params.config_dir, gateway_data, section="gateway"
        )
        return _step_result(True, "Gateway configuration synced")

    async def _step_start_gateway_docker(self, params: InitParams) -> dict:
        """Step 10 (Docker): 啟動 Gateway。"""
        result = await self._executor.run_command(
            ["docker", "compose", "up", "-d", "openclaw-gateway"],
            timeout=60,
        )
        if not result.success:
            return _step_result(False, f"Gateway start failed: {result.stderr[:200]}")
        return _step_result(True, "Gateway started (docker compose)")

    async def _step_start_gateway_native(self, params: InitParams) -> dict:
        """Step 10 (Native): 啟動 Gateway。"""
        result = await self._executor.run_command(
            ["systemctl", "start", "openclaw-gateway"],
            timeout=30,
        )
        if not result.success:
            return _step_result(False, f"Gateway start failed: {result.stderr[:200]}")
        return _step_result(True, "Gateway started (systemctl)")

    async def _step_health_check(self, params: InitParams) -> dict:
        """Health Check — GET /healthz（含冷啟動等待）。"""
        url = f"http://127.0.0.1:{params.gateway_port}/healthz"
        max_retries = 6
        last_error = ""

        # 冷啟動：Gateway 容器剛 up -d，等待 process bind port
        await asyncio.sleep(3)

        for attempt in range(max_retries):
            try:
                resp = await asyncio.to_thread(
                    urllib.request.urlopen, url, timeout=10
                )
                if resp.status == 200:
                    return _step_result(True, "Gateway is healthy")
            except Exception as exc:
                last_error = str(exc)
                if attempt < max_retries - 1:
                    await asyncio.sleep(5)
        return _step_result(
            False, f"Health check failed after {max_retries} attempts: {last_error}"
        )

    # ── Step Registration ────────────────────────────────

    def _get_steps(self, mode: str) -> list[tuple[Callable, str]]:
        """回傳該模式的步驟列表 [(method, label), ...]。"""
        if mode == "native-linux":
            return [
                (self._step_validate_native, "Validate environment"),
                (self._step_validate_env, "Validate parameters"),
                (self._step_create_dirs, "Create directory structure"),
                (self._step_gateway_token, "Generate gateway token"),
                (self._step_write_env, "Write environment file"),
                # Steps 6, 7 skipped for native
                (self._step_sync_gateway, "Configure gateway"),
                (self._step_start_gateway_native, "Start gateway"),
                (self._step_health_check, "Verify health"),
            ]
        # Docker modes (docker-windows, docker-linux, remote-ssh)
        return [
            (self._step_validate_docker, "Validate environment"),
            (self._step_validate_env, "Validate parameters"),
            (self._step_create_dirs, "Create directory structure"),
            (self._step_gateway_token, "Generate gateway token"),
            (self._step_write_env, "Write environment file"),
            (self._step_docker_image, "Build/Pull Docker image"),
            (self._step_fix_permissions, "Fix directory permissions"),
            (self._step_onboarding, "Run onboarding"),
            (self._step_sync_gateway, "Configure gateway"),
            (self._step_start_gateway_docker, "Start gateway"),
            (self._step_health_check, "Verify health"),
        ]

    # ── Orchestrator ─────────────────────────────────────

    async def run_all(
        self,
        params: InitParams,
        on_step: Callable[[str, str, str], None] | None = None,
    ) -> dict:
        """執行完整初始化流程。

        Args:
            params: 初始化參數
            on_step: 進度回呼 (step_number_str, status, message)

        Returns:
            {"success": bool, "steps": [...], "error": str|None,
             "gateway_token": str|None}
        """
        steps = self._get_steps(params.mode)
        results: list[dict] = []

        for i, (step_fn, label) in enumerate(steps, 1):
            step_str = str(i)
            if on_step:
                on_step(step_str, "running", label)

            try:
                result = await step_fn(params)
            except Exception as exc:
                logger.exception("Init step %d failed", i)
                result = _step_result(False, str(exc))

            status = "done" if result["success"] else "failed"
            if on_step:
                on_step(step_str, status, result["message"])

            results.append(result)
            if not result["success"]:
                return {
                    "success": False,
                    "steps": results,
                    "failed_step": i,
                    "error": result["message"],
                    "gateway_token": self._gateway_token,
                }

        return {
            "success": True,
            "steps": results,
            "error": None,
            "gateway_token": self._gateway_token,
        }
