"""EnvChecker 單元測試 — Mock Executor."""

from __future__ import annotations

import pytest

from src.env_checker import (
    EnvChecker,
    _parse_compose_version,
    _parse_docker_version,
    _parse_first_line,
    _parse_jq_version,
    _parse_ngrok_version,
    _parse_node_version,
)
from src.executor import CommandResult


# ── Mock Executor ─────────────────────────────────────


class MockExecutor:
    """可配置的 Mock Executor，實作 Executor Protocol 所需方法。"""

    def __init__(
        self,
        which_map: dict[str, str | None] | None = None,
        command_map: dict[tuple[str, ...], CommandResult] | None = None,
        file_exists_map: dict[str, bool] | None = None,
    ) -> None:
        self._which = which_map or {}
        self._commands = command_map or {}
        self._files = file_exists_map or {}

    async def which(self, name: str) -> str | None:
        return self._which.get(name)

    async def run_command(
        self, args: list[str], *, timeout: int = 300, on_output=None,
    ) -> CommandResult:
        key = tuple(args)
        if key in self._commands:
            return self._commands[key]
        return CommandResult(exit_code=127, stdout="", stderr="command not found")

    async def file_exists(self, path: str) -> bool:
        return self._files.get(path, False)

    async def read_file(self, path: str) -> bytes:
        return b""

    async def write_file(self, path: str, data: bytes) -> None:
        pass

    async def mkdir(self, path: str, *, parents: bool = True) -> None:
        pass

    async def copy_tree(self, src: str, dst: str) -> None:
        pass

    async def remove_tree(self, path: str) -> None:
        pass

    async def list_dir(self, path: str) -> list[str]:
        return []


# ── Helper ────────────────────────────────────────────

def _ok(stdout: str) -> CommandResult:
    return CommandResult(exit_code=0, stdout=stdout, stderr="")


def _fail(stderr: str = "error") -> CommandResult:
    return CommandResult(exit_code=1, stdout="", stderr=stderr)


# ── Version Parser Tests ──────────────────────────────


class TestVersionParsers:
    def test_parse_docker_version(self):
        assert _parse_docker_version("Docker version 24.0.5, build ced0996") == "24.0.5"
        assert _parse_docker_version("Docker version 27.1.1, build 6312585") == "27.1.1"
        assert _parse_docker_version("garbage") is None

    def test_parse_compose_version(self):
        assert _parse_compose_version("Docker Compose version v2.20.2") == "2.20.2"
        assert _parse_compose_version("v2.5.0") == "2.5.0"
        assert _parse_compose_version("no version") is None

    def test_parse_node_version(self):
        assert _parse_node_version("v20.11.0") == "20.11.0"
        assert _parse_node_version("v16.20.2\n") == "16.20.2"
        assert _parse_node_version("garbage") is None

    def test_parse_first_line(self):
        assert _parse_first_line("1.85.2\nabc123\nx64") == "1.85.2"
        assert _parse_first_line("") is None

    def test_parse_ngrok_version(self):
        assert _parse_ngrok_version("ngrok version 3.5.0") == "3.5.0"
        assert _parse_ngrok_version("no match") is None

    def test_parse_jq_version(self):
        assert _parse_jq_version("jq-1.7.1") == "1.7.1"
        assert _parse_jq_version("jq-1.6") == "1.6"
        assert _parse_jq_version("no match") is None


# ── Docker Mode Tests ─────────────────────────────────


class TestDockerMode:
    @pytest.mark.asyncio
    async def test_all_found(self):
        executor = MockExecutor(
            which_map={"docker": "/usr/bin/docker", "code": "/usr/bin/code", "ngrok": "/usr/bin/ngrok"},
            command_map={
                ("docker", "--version"): _ok("Docker version 24.0.5, build ced0996"),
                ("docker", "compose", "version"): _ok("Docker Compose version v2.20.2"),
                ("docker", "info"): _ok("Server: Docker Desktop"),
                ("code", "--version"): _ok("1.85.2\nabc123\nx64"),
                ("ngrok", "version"): _ok("ngrok version 3.5.0"),
            },
        )
        checker = EnvChecker(executor)
        checks = await checker.check_all("docker-windows")

        assert len(checks) == 5
        assert all(c["installed"] for c in checks)
        assert checks[0]["name"] == "Docker"
        assert checks[0]["version"] == "24.0.5"
        assert checks[1]["name"] == "Docker Compose"
        assert checks[1]["version"] == "2.20.2"
        assert checks[2]["name"] == "Docker Desktop"
        assert checks[2]["version"] == "Running"
        assert checks[3]["name"] == "VS Code"
        assert checks[3]["version"] == "1.85.2"
        assert checks[4]["name"] == "ngrok"
        assert checks[4]["version"] == "3.5.0"

    @pytest.mark.asyncio
    async def test_docker_missing(self):
        executor = MockExecutor(
            which_map={"code": "/usr/bin/code", "ngrok": "/usr/bin/ngrok"},
            command_map={
                ("docker", "compose", "version"): _fail(),
                ("docker", "info"): _fail(),
                ("code", "--version"): _ok("1.85.2\nabc\nx64"),
                ("ngrok", "version"): _ok("ngrok version 3.5.0"),
            },
        )
        checker = EnvChecker(executor)
        checks = await checker.check_all("docker-windows")

        assert checks[0]["installed"] is False
        assert checks[0]["name"] == "Docker"

    @pytest.mark.asyncio
    async def test_daemon_not_running(self):
        executor = MockExecutor(
            which_map={"docker": "/usr/bin/docker", "code": "/usr/bin/code", "ngrok": "/usr/bin/ngrok"},
            command_map={
                ("docker", "--version"): _ok("Docker version 24.0.5, build ced0996"),
                ("docker", "compose", "version"): _ok("Docker Compose version v2.20.2"),
                ("docker", "info"): _fail("Cannot connect to the Docker daemon"),
                ("code", "--version"): _ok("1.85.2\nabc\nx64"),
                ("ngrok", "version"): _ok("ngrok version 3.5.0"),
            },
        )
        checker = EnvChecker(executor)
        checks = await checker.check_all("docker-linux")

        assert checks[2]["name"] == "Docker Running"
        assert checks[2]["installed"] is False

    @pytest.mark.asyncio
    async def test_docker_windows_vs_linux_name(self):
        executor = MockExecutor(
            which_map={"docker": "/usr/bin/docker"},
            command_map={
                ("docker", "--version"): _ok("Docker version 24.0.5, build x"),
                ("docker", "compose", "version"): _ok("v2.20.2"),
                ("docker", "info"): _ok("ok"),
            },
        )
        checker = EnvChecker(executor)

        win_checks = await checker.check_all("docker-windows")
        assert win_checks[2]["name"] == "Docker Desktop"

        linux_checks = await checker.check_all("docker-linux")
        assert linux_checks[2]["name"] == "Docker Running"


# ── Native Mode Tests ─────────────────────────────────


class TestNativeMode:
    @pytest.mark.asyncio
    async def test_all_found(self):
        executor = MockExecutor(
            which_map={
                "node": "/usr/bin/node",
                "openclaw": "/usr/bin/openclaw",
                "jq": "/usr/bin/jq",
                "code": "/usr/bin/code",
                "ngrok": "/usr/bin/ngrok",
            },
            command_map={
                ("node", "--version"): _ok("v20.11.0"),
                ("jq", "--version"): _ok("jq-1.7.1"),
                ("code", "--version"): _ok("1.85.2\nabc\nx64"),
                ("ngrok", "version"): _ok("ngrok version 3.5.0"),
                ("systemctl", "is-enabled", "openclaw"): _ok("enabled"),
            },
        )
        checker = EnvChecker(executor)
        checks = await checker.check_all("native-linux")

        assert len(checks) == 6
        assert all(c["installed"] for c in checks)
        assert checks[0]["name"] == "Node.js"
        assert checks[0]["version"] == "v20.11.0"

    @pytest.mark.asyncio
    async def test_node_version_too_low(self):
        executor = MockExecutor(
            which_map={"node": "/usr/bin/node"},
            command_map={("node", "--version"): _ok("v16.20.2")},
        )
        checker = EnvChecker(executor)
        checks = await checker.check_all("native-linux")

        node = checks[0]
        assert node["name"] == "Node.js"
        assert node["installed"] is False
        assert node["version"] == "v16.20.2"
        assert ">= v18" in node["message"]

    @pytest.mark.asyncio
    async def test_systemd_not_enabled(self):
        executor = MockExecutor(
            which_map={"node": "/usr/bin/node"},
            command_map={
                ("node", "--version"): _ok("v20.11.0"),
                ("systemctl", "is-enabled", "openclaw"): _fail("disabled"),
            },
        )
        checker = EnvChecker(executor)
        checks = await checker.check_all("native-linux")

        systemd = checks[5]
        assert systemd["name"] == "systemd Service"
        assert systemd["installed"] is False

    @pytest.mark.asyncio
    async def test_remote_ssh_uses_native_checks(self):
        executor = MockExecutor(
            which_map={"node": "/usr/bin/node"},
            command_map={("node", "--version"): _ok("v20.11.0")},
        )
        checker = EnvChecker(executor)
        checks = await checker.check_all("remote-ssh")

        assert len(checks) == 6
        assert checks[0]["name"] == "Node.js"


# ── .env File Check Tests ─────────────────────────────


class TestEnvFileCheck:
    @pytest.mark.asyncio
    async def test_env_exists(self):
        executor = MockExecutor(file_exists_map={".env": True})
        checker = EnvChecker(executor)
        result = await checker.check_env_file(".env")

        assert result["exists"] is True
        assert "ready" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_env_missing(self):
        executor = MockExecutor(file_exists_map={".env": False})
        checker = EnvChecker(executor)
        result = await checker.check_env_file(".env")

        assert result["exists"] is False
        assert "missing" in result["message"].lower()
