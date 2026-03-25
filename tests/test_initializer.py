"""Initializer 單元測試 (WBS 3.8)。

以 Mock Executor + Mock ConfigManager 驗證 11 步初始化流程。
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.executor import CommandResult
from src.initializer import InitParams, Initializer, _step_result


# ── Fixtures ─────────────────────────────────────────────


def _ok_result(stdout: str = "") -> CommandResult:
    return CommandResult(exit_code=0, stdout=stdout, stderr="")


def _fail_result(stderr: str = "error") -> CommandResult:
    return CommandResult(exit_code=1, stdout="", stderr=stderr)


def _make_params(**overrides) -> InitParams:
    defaults = {
        "mode": "docker-windows",
        "config_dir": "/home/test/.openclaw",
        "workspace_dir": "/home/test/.openclaw/workspace",
        "gateway_bind": "lan",
        "gateway_mode": "local",
        "gateway_port": 18789,
        "bridge_port": 18790,
        "timezone": "Asia/Taipei",
        "docker_image": "openclaw:local",
    }
    defaults.update(overrides)
    return InitParams(**defaults)


@pytest.fixture()
def mock_executor():
    executor = MagicMock()
    executor.which = AsyncMock(return_value="/usr/bin/docker")
    executor.run_command = AsyncMock(return_value=_ok_result("Docker version 24.0.0"))
    executor.mkdir = AsyncMock()
    executor.read_file = AsyncMock(return_value=b"")
    executor.write_file = AsyncMock()
    executor.file_exists = AsyncMock(return_value=False)
    return executor


@pytest.fixture()
def mock_config_manager():
    cm = MagicMock()
    cm.read_openclaw_config.return_value = {}
    cm.read_env.return_value = {}
    cm.read_gui_settings.return_value = {}
    cm.write_env = MagicMock()
    cm.write_openclaw_config = MagicMock()
    return cm


@pytest.fixture()
def initializer(mock_executor, mock_config_manager):
    return Initializer(mock_executor, mock_config_manager)


# ── InitParams ───────────────────────────────────────────


class TestInitParams:
    def test_is_docker_modes(self):
        for mode in ("docker-windows", "docker-linux", "remote-ssh"):
            p = _make_params(mode=mode)
            assert p.is_docker is True
            assert p.is_native is False

    def test_is_native(self):
        p = _make_params(mode="native-linux")
        assert p.is_native is True
        assert p.is_docker is False


# ── Individual Steps ─────────────────────────────────────


class TestValidateDocker:
    @pytest.mark.asyncio
    async def test_docker_found(self, initializer, mock_executor):
        mock_executor.which.return_value = "/usr/bin/docker"
        mock_executor.run_command.return_value = _ok_result("Docker version 24.0.0")
        result = await initializer._step_validate_docker(_make_params())
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_docker_missing(self, initializer, mock_executor):
        mock_executor.which.return_value = None
        result = await initializer._step_validate_docker(_make_params())
        assert result["success"] is False
        assert "Docker not found" in result["message"]

    @pytest.mark.asyncio
    async def test_compose_missing(self, initializer, mock_executor):
        # docker found, compose fails
        async def side_effect(args, **kwargs):
            if "compose" in args:
                return _fail_result("compose not found")
            return _ok_result("Docker version 24.0.0")

        mock_executor.run_command = AsyncMock(side_effect=side_effect)
        result = await initializer._step_validate_docker(_make_params())
        assert result["success"] is False
        assert "Docker Compose" in result["message"]

    @pytest.mark.asyncio
    async def test_daemon_not_running(self, initializer, mock_executor):
        call_count = 0

        async def side_effect(args, **kwargs):
            nonlocal call_count
            call_count += 1
            if "info" in args:
                return _fail_result("Cannot connect to Docker daemon")
            return _ok_result("OK")

        mock_executor.run_command = AsyncMock(side_effect=side_effect)
        result = await initializer._step_validate_docker(_make_params())
        assert result["success"] is False
        assert "daemon" in result["message"].lower()


class TestValidateNative:
    @pytest.mark.asyncio
    async def test_all_found(self, initializer, mock_executor):
        result = await initializer._step_validate_native(_make_params(mode="native-linux"))
        assert result["success"] is True
        assert mock_executor.which.call_count == 3  # node, openclaw, systemctl

    @pytest.mark.asyncio
    async def test_node_missing(self, initializer, mock_executor):
        mock_executor.which.return_value = None
        result = await initializer._step_validate_native(_make_params(mode="native-linux"))
        assert result["success"] is False
        assert "Node.js" in result["message"]


class TestValidateEnv:
    @pytest.mark.asyncio
    async def test_valid_params(self, initializer):
        result = await initializer._step_validate_env(_make_params())
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_missing_config_dir(self, initializer):
        result = await initializer._step_validate_env(_make_params(config_dir=""))
        assert result["success"] is False


class TestCreateDirs:
    @pytest.mark.asyncio
    async def test_creates_five_dirs(self, initializer, mock_executor):
        result = await initializer._step_create_dirs(_make_params())
        assert result["success"] is True
        assert mock_executor.mkdir.call_count == 5


class TestGatewayToken:
    @pytest.mark.asyncio
    async def test_from_openclaw_json(self, initializer, mock_config_manager):
        mock_config_manager.read_openclaw_config.return_value = {"token": "existing-token-123"}
        result = await initializer._step_gateway_token(_make_params())
        assert result["success"] is True
        assert initializer._gateway_token == "existing-token-123"

    @pytest.mark.asyncio
    async def test_from_env(self, initializer, mock_config_manager):
        mock_config_manager.read_openclaw_config.return_value = {}
        mock_config_manager.read_env.return_value = {"OPENCLAW_GATEWAY_TOKEN": "env-token-456"}
        result = await initializer._step_gateway_token(_make_params())
        assert result["success"] is True
        assert initializer._gateway_token == "env-token-456"

    @pytest.mark.asyncio
    async def test_generate_new(self, initializer, mock_config_manager):
        mock_config_manager.read_openclaw_config.return_value = {}
        mock_config_manager.read_env.return_value = {}
        result = await initializer._step_gateway_token(_make_params())
        assert result["success"] is True
        assert initializer._gateway_token is not None
        assert len(initializer._gateway_token) == 64  # hex(32) = 64 chars


class TestWriteEnv:
    @pytest.mark.asyncio
    async def test_writes_env_file(self, initializer, mock_config_manager):
        initializer._gateway_token = "test-token"
        result = await initializer._step_write_env(_make_params())
        assert result["success"] is True
        mock_config_manager.write_env.assert_called_once()
        call_args = mock_config_manager.write_env.call_args
        env_path = call_args[0][0]
        env_vars = call_args[0][1]
        assert "/home/test/.openclaw/.env" in env_path
        assert env_vars["OPENCLAW_GATEWAY_TOKEN"] == "test-token"
        assert env_vars["OPENCLAW_GATEWAY_PORT"] == "18789"
        assert len(env_vars) >= 10


class TestDockerImage:
    @pytest.mark.asyncio
    async def test_build_local(self, initializer, mock_executor):
        result = await initializer._step_docker_image(_make_params(docker_image="openclaw:local"))
        assert result["success"] is True
        call_args = mock_executor.run_command.call_args[0][0]
        assert "build" in call_args

    @pytest.mark.asyncio
    async def test_pull_remote(self, initializer, mock_executor):
        result = await initializer._step_docker_image(_make_params(docker_image="ghcr.io/openclaw:latest"))
        assert result["success"] is True
        call_args = mock_executor.run_command.call_args[0][0]
        assert "pull" in call_args

    @pytest.mark.asyncio
    async def test_build_failure(self, initializer, mock_executor):
        mock_executor.run_command.return_value = _fail_result("build error")
        result = await initializer._step_docker_image(_make_params())
        assert result["success"] is False


class TestSyncGateway:
    @pytest.mark.asyncio
    async def test_writes_gateway_config(self, initializer, mock_config_manager):
        result = await initializer._step_sync_gateway(_make_params())
        assert result["success"] is True
        mock_config_manager.write_openclaw_config.assert_called_once()
        call_args = mock_config_manager.write_openclaw_config.call_args
        assert call_args[1]["section"] == "gateway"
        data = call_args[0][1]
        assert data["mode"] == "local"
        assert data["bind"] == "lan"


class TestHealthCheck:
    @pytest.mark.asyncio
    async def test_success(self, initializer):
        mock_resp = MagicMock()
        mock_resp.status = 200
        with patch("src.initializer.urllib.request.urlopen", return_value=mock_resp):
            result = await initializer._step_health_check(_make_params())
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_failure_after_retries(self, initializer):
        with patch("src.initializer.urllib.request.urlopen", side_effect=Exception("Connection refused")):
            with patch("src.initializer.asyncio.sleep", new_callable=AsyncMock):
                result = await initializer._step_health_check(_make_params())
        assert result["success"] is False
        assert "6 attempts" in result["message"]


# ── run_all Orchestration ────────────────────────────────


class TestRunAll:
    @pytest.mark.asyncio
    async def test_docker_success(self, initializer, mock_executor, mock_config_manager):
        """Full Docker run — all steps succeed."""
        mock_resp = MagicMock()
        mock_resp.status = 200
        with patch("src.initializer.urllib.request.urlopen", return_value=mock_resp):
            result = await initializer.run_all(_make_params())
        assert result["success"] is True
        assert len(result["steps"]) == 10
        assert result["gateway_token"] is not None

    @pytest.mark.asyncio
    async def test_docker_failure_stops(self, initializer, mock_executor):
        """If step 1 fails, stop immediately."""
        mock_executor.which.return_value = None  # Docker not found
        on_step = MagicMock()
        result = await initializer.run_all(_make_params(), on_step=on_step)
        assert result["success"] is False
        assert result["failed_step"] == 1
        assert len(result["steps"]) == 1

    @pytest.mark.asyncio
    async def test_native_fewer_steps(self, initializer, mock_executor, mock_config_manager):
        """Native mode has fewer steps (no Docker image, no permissions)."""
        mock_resp = MagicMock()
        mock_resp.status = 200
        with patch("src.initializer.urllib.request.urlopen", return_value=mock_resp):
            result = await initializer.run_all(_make_params(mode="native-linux"))
        assert result["success"] is True
        assert len(result["steps"]) == 8  # 8 steps for native

    @pytest.mark.asyncio
    async def test_on_step_callbacks(self, initializer, mock_executor, mock_config_manager):
        """Verify on_step is called with correct arguments."""
        mock_resp = MagicMock()
        mock_resp.status = 200
        on_step = MagicMock()
        with patch("src.initializer.urllib.request.urlopen", return_value=mock_resp):
            await initializer.run_all(_make_params(), on_step=on_step)
        # Each step calls on_step twice: "running" + "done"
        assert on_step.call_count == 20  # 10 steps × 2
        # First call: step 1, running
        first_call = on_step.call_args_list[0]
        assert first_call[0] == ("1", "running", "Validate environment")

    @pytest.mark.asyncio
    async def test_step_exception_caught(self, initializer, mock_executor):
        """If a step raises an exception, it should be caught."""
        mock_executor.which.side_effect = RuntimeError("Unexpected error")
        result = await initializer.run_all(_make_params())
        assert result["success"] is False
        assert "Unexpected error" in result["error"]


# ── Step List by Mode ────────────────────────────────────


class TestStepList:
    def test_docker_has_10_steps(self, initializer):
        steps = initializer._get_steps("docker-windows")
        assert len(steps) == 10

    def test_native_has_8_steps(self, initializer):
        steps = initializer._get_steps("native-linux")
        assert len(steps) == 8

    def test_remote_ssh_uses_docker_steps(self, initializer):
        steps = initializer._get_steps("remote-ssh")
        assert len(steps) == 10

    def test_docker_linux_uses_docker_steps(self, initializer):
        steps = initializer._get_steps("docker-linux")
        assert len(steps) == 10
