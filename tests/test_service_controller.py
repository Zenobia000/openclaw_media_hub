"""ServiceController 單元測試 (WBS 3.9.4)。

以 Mock Executor 驗證 Docker / Native 模式的服務啟停與狀態查詢。
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.executor import CommandResult
from src.service_controller import (
    ServiceController,
    _parse_docker_uptime,
    _parse_systemd_uptime,
)


# ── Helpers ───────────────────────────────────────────────


def _ok(stdout: str = "") -> CommandResult:
    return CommandResult(exit_code=0, stdout=stdout, stderr="")


def _fail(stderr: str = "error") -> CommandResult:
    return CommandResult(exit_code=1, stdout="", stderr=stderr)


def _make_executor() -> MagicMock:
    executor = MagicMock()
    executor.run_command = AsyncMock(return_value=_ok())
    executor.list_dir = AsyncMock(return_value=[])
    executor.read_file = AsyncMock(return_value=b"{}")
    return executor


def _docker_ctrl(executor=None) -> ServiceController:
    return ServiceController(
        executor or _make_executor(),
        deployment_mode="docker-windows",
        config_dir="/home/test/.openclaw",
    )


def _native_ctrl(executor=None) -> ServiceController:
    return ServiceController(
        executor or _make_executor(),
        deployment_mode="native-linux",
        config_dir="/home/test/.openclaw",
    )


# ── Docker Start/Stop/Restart ─────────────────────────────


class TestDockerStartStopRestart:
    @pytest.mark.asyncio
    async def test_start_success(self):
        ex = _make_executor()
        ctrl = _docker_ctrl(ex)
        result = await ctrl.start()
        assert result["success"] is True
        assert result["message"] == "All services started"
        ex.run_command.assert_called_once()
        args = ex.run_command.call_args[0][0]
        assert args == ["docker", "compose", "up", "-d", "openclaw-gateway"]

    @pytest.mark.asyncio
    async def test_start_failure(self):
        ex = _make_executor()
        ex.run_command = AsyncMock(return_value=_fail("no such service"))
        ctrl = _docker_ctrl(ex)
        result = await ctrl.start()
        assert result["success"] is False
        assert "Start failed" in result["message"]

    @pytest.mark.asyncio
    async def test_stop_success(self):
        ex = _make_executor()
        ctrl = _docker_ctrl(ex)
        result = await ctrl.stop()
        assert result["success"] is True
        args = ex.run_command.call_args[0][0]
        assert args == ["docker", "compose", "down"]

    @pytest.mark.asyncio
    async def test_restart_success(self):
        ex = _make_executor()
        ctrl = _docker_ctrl(ex)
        result = await ctrl.restart()
        assert result["success"] is True
        args = ex.run_command.call_args[0][0]
        assert args == ["docker", "compose", "restart", "openclaw-gateway"]


# ── Native Start/Stop/Restart ─────────────────────────────


class TestNativeStartStopRestart:
    @pytest.mark.asyncio
    async def test_start_success(self):
        ex = _make_executor()
        ctrl = _native_ctrl(ex)
        result = await ctrl.start()
        assert result["success"] is True
        args = ex.run_command.call_args[0][0]
        assert args == ["systemctl", "start", "openclaw-gateway"]

    @pytest.mark.asyncio
    async def test_stop_success(self):
        ex = _make_executor()
        ctrl = _native_ctrl(ex)
        result = await ctrl.stop()
        assert result["success"] is True
        args = ex.run_command.call_args[0][0]
        assert args == ["systemctl", "stop", "openclaw-gateway"]

    @pytest.mark.asyncio
    async def test_restart_success(self):
        ex = _make_executor()
        ctrl = _native_ctrl(ex)
        result = await ctrl.restart()
        assert result["success"] is True
        args = ex.run_command.call_args[0][0]
        assert args == ["systemctl", "restart", "openclaw-gateway"]


# ── Docker Status ─────────────────────────────────────────


class TestDockerStatus:
    @pytest.mark.asyncio
    async def test_running_service(self):
        ps_output = json.dumps({
            "Service": "openclaw-gateway",
            "State": "running",
            "Status": "Up 2 hours",
        })
        ex = _make_executor()
        ex.run_command = AsyncMock(return_value=_ok(ps_output))
        ctrl = _docker_ctrl(ex)
        result = await ctrl.status()
        assert result["running"] is True
        assert result["services"][0]["name"] == "openclaw-gateway"
        assert result["services"][0]["status"] == "running"
        assert result["uptime"] == "2h"

    @pytest.mark.asyncio
    async def test_stopped_service(self):
        ps_output = json.dumps({
            "Service": "openclaw-gateway",
            "State": "exited",
            "Status": "Exited (0) 5 minutes ago",
        })
        ex = _make_executor()
        ex.run_command = AsyncMock(return_value=_ok(ps_output))
        ctrl = _docker_ctrl(ex)
        result = await ctrl.status()
        assert result["running"] is False
        assert result["services"][0]["status"] == "stopped"

    @pytest.mark.asyncio
    async def test_command_failure_returns_error(self):
        ex = _make_executor()
        ex.run_command = AsyncMock(return_value=_fail("docker not found"))
        ctrl = _docker_ctrl(ex)
        result = await ctrl.status()
        assert result["running"] is False
        assert result["services"][0]["status"] == "error"

    @pytest.mark.asyncio
    async def test_empty_output_returns_stopped(self):
        ex = _make_executor()
        ex.run_command = AsyncMock(return_value=_ok(""))
        ctrl = _docker_ctrl(ex)
        result = await ctrl.status()
        assert result["running"] is False
        assert result["services"][0]["name"] == "gateway"
        assert result["services"][0]["status"] == "stopped"


# ── Native Status ─────────────────────────────────────────


class TestNativeStatus:
    @pytest.mark.asyncio
    async def test_active_service(self):
        ex = _make_executor()
        ex.run_command = AsyncMock(
            side_effect=[
                _ok("active"),  # is-active
                _ok("ActiveEnterTimestamp=Tue 2026-03-25 10:00:00 CST"),  # show
            ]
        )
        ctrl = _native_ctrl(ex)
        result = await ctrl.status()
        assert result["running"] is True
        assert result["services"][0]["status"] == "running"

    @pytest.mark.asyncio
    async def test_inactive_service(self):
        ex = _make_executor()
        ex.run_command = AsyncMock(return_value=_fail("inactive"))
        ctrl = _native_ctrl(ex)
        result = await ctrl.status()
        assert result["running"] is False
        assert result["services"][0]["status"] == "stopped"
        assert result["uptime"] == "—"


# ── Skills / Plugins Count ────────────────────────────────


class TestCounts:
    @pytest.mark.asyncio
    async def test_skills_count(self):
        ex = _make_executor()
        ex.run_command = AsyncMock(return_value=_ok(""))
        ex.list_dir = AsyncMock(return_value=["skill-a", "skill-b", "skill-c"])
        ctrl = _docker_ctrl(ex)
        result = await ctrl.status()
        assert result["skills_count"] == 3

    @pytest.mark.asyncio
    async def test_skills_dir_missing(self):
        ex = _make_executor()
        ex.run_command = AsyncMock(return_value=_ok(""))
        ex.list_dir = AsyncMock(side_effect=FileNotFoundError("no dir"))
        ctrl = _docker_ctrl(ex)
        result = await ctrl.status()
        assert result["skills_count"] == 0

    @pytest.mark.asyncio
    async def test_plugins_count(self):
        config = {"plugins": {"installs": {"plugin-a": {}, "plugin-b": {}}}}
        ex = _make_executor()
        ex.run_command = AsyncMock(return_value=_ok(""))
        ex.read_file = AsyncMock(return_value=json.dumps(config).encode())
        ctrl = _docker_ctrl(ex)
        result = await ctrl.status()
        assert result["plugins_count"] == 2

    @pytest.mark.asyncio
    async def test_plugins_config_missing(self):
        ex = _make_executor()
        ex.run_command = AsyncMock(return_value=_ok(""))
        ex.read_file = AsyncMock(side_effect=FileNotFoundError("no file"))
        ctrl = _docker_ctrl(ex)
        result = await ctrl.status()
        assert result["plugins_count"] == 0


# ── Remote SSH Mode ───────────────────────────────────────


class TestRemoteSSH:
    @pytest.mark.asyncio
    async def test_remote_uses_docker(self):
        """remote-ssh 模式應使用 docker compose 指令。"""
        ex = _make_executor()
        ctrl = ServiceController(
            ex, deployment_mode="remote-ssh", config_dir="/home/test/.openclaw",
        )
        await ctrl.start()
        args = ex.run_command.call_args[0][0]
        assert args == ["docker", "compose", "up", "-d", "openclaw-gateway"]


# ── Uptime Parsing ────────────────────────────────────────


class TestParseDockerUptime:
    def test_hours(self):
        assert _parse_docker_uptime("Up 2 hours") == "2h"

    def test_hours_and_minutes(self):
        assert _parse_docker_uptime("Up 1 hours 30 minutes") == "1h 30m"

    def test_minutes(self):
        assert _parse_docker_uptime("Up 35 minutes") == "35m"

    def test_about_an_hour(self):
        assert _parse_docker_uptime("Up About an hour") == "1h"

    def test_seconds(self):
        assert _parse_docker_uptime("Up 5 seconds") == "< 1m"

    def test_days(self):
        assert _parse_docker_uptime("Up 3 days") == "72h"

    def test_empty(self):
        assert _parse_docker_uptime("") == "—"

    def test_exited(self):
        assert _parse_docker_uptime("Exited (0) 5 minutes ago") == "—"


class TestParseSystemdUptime:
    def test_empty_value(self):
        assert _parse_systemd_uptime("ActiveEnterTimestamp=") == "—"

    def test_no_equals(self):
        assert _parse_systemd_uptime("invalid") == "—"
