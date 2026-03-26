"""Service Controller — 服務啟停控制 (docker compose / systemctl)。

透過 Executor 介面執行服務控制指令，本機模式由 LocalExecutor 呼叫
subprocess，遠端模式由 RemoteExecutor 透過 SSH 執行。
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from pathlib import PurePosixPath

from src.executor import Executor

logger = logging.getLogger(__name__)

# ── 服務指令註冊表 ────────────────────────────────────────

_SERVICE_COMMANDS: dict[str, dict] = {
    "start": {
        "docker": (["docker", "compose", "up", "-d", "openclaw-gateway"], 60),
        "native": (["systemctl", "start", "openclaw-gateway"], 30),
        "msg": "All services started",
    },
    "stop": {
        "docker": (["docker", "compose", "down"], 60),
        "native": (["systemctl", "stop", "openclaw-gateway"], 30),
        "msg": "All services stopped",
    },
    "restart": {
        "docker": (["docker", "compose", "restart", "openclaw-gateway"], 60),
        "native": (["systemctl", "restart", "openclaw-gateway"], 30),
        "msg": "All services restarted",
    },
}


class ServiceController:
    """服務啟停控制器。

    根據 deployment_mode 自動選擇 docker compose 或 systemctl 指令。
    """

    def __init__(
        self,
        executor: Executor,
        *,
        deployment_mode: str,
        config_dir: str,
    ) -> None:
        self._executor = executor
        self._mode = deployment_mode
        self._config_dir = config_dir
        self._is_docker = deployment_mode in (
            "docker-windows", "docker-linux", "remote-ssh",
        )

    # ── 服務啟停（統一實作）──────────────────────────────

    async def _run_service_action(self, action: str) -> dict:
        """執行服務控制指令，回傳 {success, message}。"""
        spec = _SERVICE_COMMANDS[action]
        key = "docker" if self._is_docker else "native"
        args, timeout = spec[key]
        result = await self._executor.run_command(args, timeout=timeout)
        if not result.success:
            return {"success": False, "message": f"{action.title()} failed: {result.stderr[:200]}"}
        return {"success": True, "message": spec["msg"]}

    async def start(self) -> dict:
        """啟動服務。"""
        return await self._run_service_action("start")

    async def stop(self) -> dict:
        """停止服務。"""
        return await self._run_service_action("stop")

    async def restart(self) -> dict:
        """重啟服務。"""
        return await self._run_service_action("restart")

    # ── 狀態查詢 ──────────────────────────────────────────

    async def status(self) -> dict:
        """查詢服務狀態。

        Returns:
            {running, services, uptime, skills_count, plugins_count}
        """
        if self._is_docker:
            services, uptime = await self._docker_status()
        else:
            services, uptime = await self._native_status()

        running = any(s["status"] == "running" for s in services)
        skills_count = await self._count_skills()
        plugins_count = await self._count_plugins()

        return {
            "running": running,
            "services": services,
            "uptime": uptime,
            "skills_count": skills_count,
            "plugins_count": plugins_count,
        }

    # ── Docker 狀態 ───────────────────────────────────────

    async def _docker_status(self) -> tuple[list[dict], str]:
        """透過 docker compose ps 查詢服務狀態。"""
        result = await self._executor.run_command(
            ["docker", "compose", "ps", "--format", "json"],
            timeout=30,
        )
        if not result.success:
            return [{"name": "gateway", "status": "error"}], "—"

        services = []
        uptime = "—"
        for line in result.stdout.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            name = entry.get("Service") or entry.get("Name", "unknown")
            state = (entry.get("State") or "").lower()
            status = "running" if state == "running" else "stopped"
            services.append({"name": name, "status": status})

            if status == "running":
                uptime = _parse_docker_uptime(entry.get("Status", ""))

        if not services:
            services = [{"name": "gateway", "status": "stopped"}]

        return services, uptime

    # ── Native 狀態 ───────────────────────────────────────

    async def _native_status(self) -> tuple[list[dict], str]:
        """透過 systemctl 查詢服務狀態。"""
        result = await self._executor.run_command(
            ["systemctl", "is-active", "openclaw-gateway"],
            timeout=10,
        )
        is_active = result.success and result.stdout.strip() == "active"
        status = "running" if is_active else "stopped"

        uptime = "—"
        if is_active:
            ts_result = await self._executor.run_command(
                ["systemctl", "show", "openclaw-gateway",
                 "--property=ActiveEnterTimestamp"],
                timeout=10,
            )
            if ts_result.success:
                uptime = _parse_systemd_uptime(ts_result.stdout.strip())

        return [{"name": "gateway", "status": status}], uptime

    # ── 技能/外掛計數 ─────────────────────────────────────

    async def _count_skills(self) -> int:
        """計算已部署技能數量。"""
        skills_dir = str(PurePosixPath(self._config_dir) / "workspace" / "skills")
        try:
            entries = await self._executor.list_dir(skills_dir)
            return len(entries)
        except (FileNotFoundError, OSError):
            return 0

    async def _count_plugins(self) -> int:
        """計算已安裝外掛數量。"""
        config_path = str(PurePosixPath(self._config_dir) / "openclaw.json")
        try:
            data = await self._executor.read_file(config_path)
            config = json.loads(data)
            installs = config.get("plugins", {}).get("installs", {})
            return len(installs)
        except (FileNotFoundError, OSError, json.JSONDecodeError):
            return 0


# ── 輔助函式 ─────────────────────────────────────────────


def _parse_docker_uptime(status_str: str) -> str:
    """解析 docker compose ps 的 Status 欄位為人類可讀 uptime。

    範例輸入: "Up 2 hours", "Up About an hour", "Up 35 minutes"
    """
    if not status_str:
        return "—"

    s = status_str.lower()
    if "up" not in s:
        return "—"

    hours = 0
    minutes = 0

    h_match = re.search(r"(\d+)\s*hour", s)
    if h_match:
        hours = int(h_match.group(1))

    m_match = re.search(r"(\d+)\s*minute", s)
    if m_match:
        minutes = int(m_match.group(1))

    d_match = re.search(r"(\d+)\s*day", s)
    if d_match:
        hours += int(d_match.group(1)) * 24

    if "about an hour" in s:
        hours = 1

    if "about a minute" in s or "less than a second" in s:
        minutes = max(minutes, 1)

    if hours == 0 and minutes == 0:
        return "< 1m"

    parts = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    return " ".join(parts) if parts else "< 1m"


def _parse_systemd_uptime(prop_line: str) -> str:
    """解析 systemctl show 的 ActiveEnterTimestamp。

    範例輸入: "ActiveEnterTimestamp=Tue 2026-03-25 10:00:00 CST"
    """
    if "=" not in prop_line:
        return "—"

    ts_str = prop_line.split("=", 1)[1].strip()
    if not ts_str:
        return "—"

    try:
        # systemd 格式: "Day YYYY-MM-DD HH:MM:SS TZ"
        parts = ts_str.split()
        if len(parts) >= 3:
            dt_str = f"{parts[1]} {parts[2]}"
            dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
            now = datetime.now()
            delta = now - dt
            total_minutes = int(delta.total_seconds() / 60)
            hours = total_minutes // 60
            minutes = total_minutes % 60
            if hours:
                return f"{hours}h {minutes}m"
            return f"{minutes}m" if minutes else "< 1m"
    except (ValueError, IndexError):
        pass

    return "—"
