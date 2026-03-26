"""Env Checker — 環境檢查邏輯 (Python 原生實作)。

以 Executor.which() 偵測軟體、Executor.run_command() 取版本號，
回傳結構化檢查結果供前端渲染狀態卡片。
"""

from __future__ import annotations

import re
from collections.abc import Callable

from src.executor import Executor
from src.platform_utils import DEPLOY_DOCKER_LINUX, DEPLOY_DOCKER_WINDOWS

# ── 版本解析註冊表 ───────────────────────────────────────

_VERSION_PATTERNS: dict[str, re.Pattern[str]] = {
    "docker": re.compile(r"Docker version (\S+),?"),
    "compose": re.compile(r"v?(\d+\.\d+\.\d+)"),
    "node": re.compile(r"v(\d+\.\d+\.\d+)"),
    "ngrok": re.compile(r"(\d+\.\d+\.\d+)"),
    "jq": re.compile(r"jq-(\S+)"),
}


def _parse_version(key: str, text: str) -> str | None:
    """通用版本解析 — 以 key 查找對應 regex。"""
    pattern = _VERSION_PATTERNS.get(key)
    if not pattern:
        return None
    m = pattern.search(text)
    return m.group(1).rstrip(",") if m else None


def _parse_first_line(s: str) -> str | None:
    """取輸出的第一行（VS Code 等工具適用）。"""
    lines = s.strip().splitlines()
    return lines[0].strip() if lines else None


# ── EnvChecker ───────────────────────────────────────────


class EnvChecker:
    """環境依賴檢查器。"""

    def __init__(self, executor: Executor) -> None:
        self._executor = executor

    # ── 公開 API ─────────────────────────────────────

    async def check_all(self, mode: str) -> list[dict]:
        """依部署模式執行對應的環境檢查。

        Args:
            mode: 部署模式 (docker-windows / docker-linux / native-linux / remote-ssh)

        Returns:
            [{"name": str, "installed": bool, "version": str|None, "message": str}]
        """
        if mode in (DEPLOY_DOCKER_WINDOWS, DEPLOY_DOCKER_LINUX):
            return await self._check_docker_mode(mode)
        # native-linux 與 remote-ssh 都跑 native 檢查
        return await self._check_native_mode()

    async def check_env_file(self, env_path: str) -> dict:
        """檢查 .env 檔案是否存在。

        Returns:
            {"exists": bool, "message": str}
        """
        exists = await self._executor.file_exists(env_path)
        if exists:
            return {"exists": True, "message": "Copied from .env.example — ready for configuration"}
        return {"exists": False, "message": "Missing — copy from .env.example"}

    # ── Docker 模式（5 項檢查）────────────────────────

    async def _check_docker_mode(self, mode: str) -> list[dict]:
        docker = await self._check_binary(
            "Docker", "docker", ["docker", "--version"],
            lambda s: _parse_version("docker", s),
            "Docker not found — install Docker Desktop",
        )
        compose = await self._check_command(
            "Docker Compose", ["docker", "compose", "version"],
            lambda s: _parse_version("compose", s),
            "Docker Compose not available — update Docker Desktop",
        )
        daemon_name = "Docker Desktop" if mode == DEPLOY_DOCKER_WINDOWS else "Docker Running"
        daemon = await self._check_daemon(daemon_name)
        vscode = await self._check_binary(
            "VS Code", "code", ["code", "--version"], _parse_first_line,
            "VS Code not found — optional but recommended",
        )
        ngrok = await self._check_binary(
            "ngrok", "ngrok", ["ngrok", "version"],
            lambda s: _parse_version("ngrok", s),
            "ngrok not found — optional, needed for tunnels",
        )
        return [docker, compose, daemon, vscode, ngrok]

    # ── Native Linux 模式（6 項檢查）─────────────────

    async def _check_native_mode(self) -> list[dict]:
        node = await self._check_node()
        openclaw = await self._check_binary(
            "OpenClaw CLI", "openclaw", [], None,
            "OpenClaw CLI not found — install via official guide",
        )
        jq = await self._check_binary(
            "jq", "jq", ["jq", "--version"],
            lambda s: _parse_version("jq", s),
            "jq not found — install via package manager",
        )
        vscode = await self._check_binary(
            "VS Code", "code", ["code", "--version"], _parse_first_line,
            "VS Code not found — optional but recommended",
        )
        ngrok = await self._check_binary(
            "ngrok", "ngrok", ["ngrok", "version"],
            lambda s: _parse_version("ngrok", s),
            "ngrok not found — optional, needed for tunnels",
        )
        systemd = await self._check_systemd()
        return [node, openclaw, jq, vscode, ngrok, systemd]

    # ── 可重用檢查工具 ─────────────────────────────────

    async def _check_binary(
        self,
        name: str,
        cmd_name: str,
        version_args: list[str],
        version_parser: Callable[[str], str | None] | None,
        message_if_missing: str,
    ) -> dict:
        """檢查一個二進位工具：which + 取版本。"""
        path = await self._executor.which(cmd_name)
        if path is None:
            return {"name": name, "installed": False, "version": None, "message": message_if_missing}

        version = None
        if version_args and version_parser:
            result = await self._executor.run_command(version_args, timeout=15)
            if result.success:
                version = version_parser(result.stdout)

        return {"name": name, "installed": True, "version": version, "message": f"{name} is available"}

    async def _check_command(
        self,
        name: str,
        args: list[str],
        version_parser: Callable[[str], str | None] | None,
        message_if_missing: str,
    ) -> dict:
        """檢查一個子命令（不需 which，直接執行）。"""
        result = await self._executor.run_command(args, timeout=15)
        if not result.success:
            return {"name": name, "installed": False, "version": None, "message": message_if_missing}

        version = version_parser(result.stdout) if version_parser else None
        return {"name": name, "installed": True, "version": version, "message": f"{name} is available"}

    async def _check_daemon(self, name: str) -> dict:
        """檢查 Docker daemon 是否在運行。"""
        result = await self._executor.run_command(["docker", "info"], timeout=10)
        if result.success:
            return {"name": name, "installed": True, "version": "Running", "message": f"{name} is running"}
        return {"name": name, "installed": False, "version": None, "message": f"{name} is not running — start Docker"}

    async def _check_node(self) -> dict:
        """檢查 Node.js 且版本 >= 18。"""
        path = await self._executor.which("node")
        if not path:
            return {"name": "Node.js", "installed": False, "version": None,
                    "message": "Node.js not found — install v18 or later"}

        result = await self._executor.run_command(["node", "--version"], timeout=15)
        if not result.success:
            return {"name": "Node.js", "installed": True, "version": None,
                    "message": "Could not determine Node.js version"}

        version_str = _parse_version("node", result.stdout)
        if not version_str:
            return {"name": "Node.js", "installed": True, "version": None,
                    "message": "Could not parse Node.js version"}

        major = int(version_str.split(".")[0])
        if major < 18:
            return {"name": "Node.js", "installed": False, "version": f"v{version_str}",
                    "message": f"Node.js v{version_str} found — requires >= v18"}

        return {"name": "Node.js", "installed": True, "version": f"v{version_str}",
                "message": "Node.js is available"}

    async def _check_systemd(self) -> dict:
        """檢查 openclaw systemd service 是否已啟用。"""
        result = await self._executor.run_command(["systemctl", "is-enabled", "openclaw"], timeout=10)
        if result.success:
            status = result.stdout.strip()
            return {"name": "systemd Service", "installed": True, "version": status,
                    "message": "OpenClaw systemd service is enabled"}
        return {"name": "systemd Service", "installed": False, "version": None,
                "message": "OpenClaw systemd service not found or disabled"}
