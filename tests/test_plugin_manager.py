"""PluginManager 單元測試 (WBS 3.11)。

以 Mock Executor 驗證外掛掃描、分類、安裝與移除邏輯。
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, call

import pytest

from src.plugin_manager import PluginManager, _categorize


# ── Helpers ───────────────────────────────────────────────


def _make_executor() -> MagicMock:
    executor = MagicMock()
    executor.list_dir = AsyncMock(return_value=[])
    executor.read_file = AsyncMock(return_value=b"{}")
    executor.write_file = AsyncMock()
    executor.file_exists = AsyncMock(return_value=False)
    return executor


def _make_manager(
    executor=None,
    *,
    local_executor=None,
    on_progress=None,
) -> PluginManager:
    return PluginManager(
        executor or _make_executor(),
        extensions_dir="./openclaw/extensions",
        config_dir="/home/test/.openclaw",
        local_executor=local_executor,
        on_progress=on_progress,
    )


# ── Sample data ──────────────────────────────────────────

PLUGIN_OPENAI = json.dumps({
    "id": "openai",
    "providers": ["openai", "openai-codex"],
    "configSchema": {},
}).encode()

PLUGIN_LINE = json.dumps({
    "id": "line",
    "channels": ["line"],
    "configSchema": {},
}).encode()

PLUGIN_MEMORY = json.dumps({
    "id": "memory-core",
    "kind": "memory",
    "configSchema": {},
}).encode()

PLUGIN_BRAVE = json.dumps({
    "id": "brave",
    "configSchema": {},
}).encode()

PKG_OPENAI = json.dumps({
    "name": "@openclaw/openai",
    "description": "OpenClaw OpenAI provider plugin",
}).encode()

PKG_LINE = json.dumps({
    "name": "@openclaw/line",
    "description": "OpenClaw LINE channel plugin",
    "openclaw": {
        "channel": {"label": "LINE", "blurb": "LINE Messaging API bot"},
        "install": {"localPath": "extensions/line"},
    },
}).encode()

PKG_MEMORY = json.dumps({
    "name": "@openclaw/memory-core",
    "description": "OpenClaw core memory search plugin",
}).encode()

PKG_BRAVE = json.dumps({
    "name": "@openclaw/brave-plugin",
    "description": "OpenClaw Brave plugin",
}).encode()

OPENCLAW_CONFIG_EMPTY = json.dumps({}).encode()

OPENCLAW_CONFIG_WITH_INSTALLS = json.dumps({
    "plugins": {
        "enabled": True,
        "entries": {"openai": {"enabled": True}},
        "installs": {
            "openai": {
                "installedAt": "2026-03-20T00:00:00+00:00",
                "installPath": "~/.openclaw/extensions/openai",
            },
        },
        "load": {"paths": ["extensions/openai"]},
    },
}).encode()


def _setup_scan(executor, plugins_and_pkgs: dict[str, tuple[bytes, bytes]]):
    """Set up executor mocks for scanning multiple plugins."""
    dirs = list(plugins_and_pkgs.keys())
    executor.list_dir = AsyncMock(return_value=dirs)

    async def _read(path: str) -> bytes:
        for name, (pj, pkg) in plugins_and_pkgs.items():
            if path.endswith(f"/{name}/openclaw.plugin.json"):
                return pj
            if path.endswith(f"/{name}/package.json"):
                return pkg
        if path.endswith("openclaw.json"):
            return OPENCLAW_CONFIG_EMPTY
        raise FileNotFoundError(path)

    executor.read_file = AsyncMock(side_effect=_read)


# ── TestCategorize ───────────────────────────────────────


class TestCategorize:
    def test_provider(self):
        assert _categorize({"providers": ["openai"]}) == "providers"

    def test_channel(self):
        assert _categorize({"channels": ["line"]}) == "channels"

    def test_infrastructure(self):
        assert _categorize({"kind": "memory"}) == "infrastructure"

    def test_tools_default(self):
        assert _categorize({"configSchema": {}}) == "tools"


# ── TestListPlugins ──────────────────────────────────────


class TestListPlugins:
    @pytest.mark.asyncio
    async def test_scans_and_categorizes(self):
        ex = _make_executor()
        _setup_scan(ex, {
            "openai": (PLUGIN_OPENAI, PKG_OPENAI),
            "line": (PLUGIN_LINE, PKG_LINE),
            "memory-core": (PLUGIN_MEMORY, PKG_MEMORY),
            "brave": (PLUGIN_BRAVE, PKG_BRAVE),
        })
        mgr = _make_manager(ex)
        result = await mgr.list_plugins()

        assert len(result) == 4
        ids = [p["id"] for p in result]
        assert ids == ["openai", "line", "brave", "memory-core"]
        assert result[0]["category"] == "providers"
        assert result[1]["category"] == "channels"
        assert result[2]["category"] == "tools"
        assert result[3]["category"] == "infrastructure"

    @pytest.mark.asyncio
    async def test_installed_detection(self):
        ex = _make_executor()
        _setup_scan(ex, {"openai": (PLUGIN_OPENAI, PKG_OPENAI)})
        # Override openclaw.json read for config
        original_side_effect = ex.read_file.side_effect

        async def _read_with_install(path: str) -> bytes:
            if path.endswith("openclaw.json"):
                return OPENCLAW_CONFIG_WITH_INSTALLS
            return await original_side_effect(path)

        ex.read_file = AsyncMock(side_effect=_read_with_install)
        mgr = _make_manager(ex)
        result = await mgr.list_plugins()

        assert result[0]["id"] == "openai"
        assert result[0]["installed"] is True

    @pytest.mark.asyncio
    async def test_empty_dir(self):
        ex = _make_executor()
        ex.list_dir = AsyncMock(return_value=[])
        mgr = _make_manager(ex)
        result = await mgr.list_plugins()
        assert result == []

    @pytest.mark.asyncio
    async def test_bad_plugin_json_skipped(self):
        ex = _make_executor()
        ex.list_dir = AsyncMock(return_value=["good", "bad"])

        async def _read(path: str) -> bytes:
            if "bad/openclaw.plugin.json" in path:
                raise FileNotFoundError(path)
            if "good/openclaw.plugin.json" in path:
                return PLUGIN_BRAVE
            if "good/package.json" in path:
                return PKG_BRAVE
            if path.endswith("openclaw.json"):
                return OPENCLAW_CONFIG_EMPTY
            raise FileNotFoundError(path)

        ex.read_file = AsyncMock(side_effect=_read)
        mgr = _make_manager(ex)
        result = await mgr.list_plugins()
        assert len(result) == 1
        assert result[0]["id"] == "brave"

    @pytest.mark.asyncio
    async def test_caches_result(self):
        ex = _make_executor()
        _setup_scan(ex, {"brave": (PLUGIN_BRAVE, PKG_BRAVE)})
        mgr = _make_manager(ex)

        r1 = await mgr.list_plugins()
        r2 = await mgr.list_plugins()
        assert r1 is r2  # same object from cache

    @pytest.mark.asyncio
    async def test_channel_metadata(self):
        ex = _make_executor()
        _setup_scan(ex, {"line": (PLUGIN_LINE, PKG_LINE)})
        mgr = _make_manager(ex)
        result = await mgr.list_plugins()

        assert result[0]["channel_label"] == "LINE"
        assert result[0]["channel_blurb"] == "LINE Messaging API bot"


# ── TestInstallPlugins ───────────────────────────────────


class TestInstallPlugins:
    @pytest.mark.asyncio
    async def test_install_writes_config(self):
        ex = _make_executor()
        _setup_scan(ex, {"openai": (PLUGIN_OPENAI, PKG_OPENAI)})
        mgr = _make_manager(ex)

        result = await mgr.install_plugins(["openai"])

        assert result["installed"] == ["openai"]
        assert result["failed"] == []
        # verify write_file called
        ex.write_file.assert_called_once()
        written = json.loads(ex.write_file.call_args[0][1].decode())
        assert "openai" in written["plugins"]["entries"]
        assert written["plugins"]["entries"]["openai"]["enabled"] is True
        assert "openai" in written["plugins"]["installs"]
        assert "extensions/openai" in written["plugins"]["load"]["paths"]

    @pytest.mark.asyncio
    async def test_install_nonexistent_fails(self):
        ex = _make_executor()
        _setup_scan(ex, {"openai": (PLUGIN_OPENAI, PKG_OPENAI)})
        mgr = _make_manager(ex)

        result = await mgr.install_plugins(["nonexistent"])

        assert result["installed"] == []
        assert len(result["failed"]) == 1
        assert result["failed"][0]["id"] == "nonexistent"

    @pytest.mark.asyncio
    async def test_install_progress_callback(self):
        ex = _make_executor()
        _setup_scan(ex, {"brave": (PLUGIN_BRAVE, PKG_BRAVE)})
        progress = MagicMock()
        mgr = _make_manager(ex, on_progress=progress)

        await mgr.install_plugins(["brave"])

        progress.assert_any_call("brave", "running", "Installing...")
        progress.assert_any_call("brave", "done", "Installed")

    @pytest.mark.asyncio
    async def test_install_clears_cache(self):
        ex = _make_executor()
        _setup_scan(ex, {"brave": (PLUGIN_BRAVE, PKG_BRAVE)})
        mgr = _make_manager(ex)

        await mgr.list_plugins()
        assert mgr._cached_plugins is not None
        await mgr.install_plugins(["brave"])
        assert mgr._cached_plugins is None

    @pytest.mark.asyncio
    async def test_partial_failure(self):
        ex = _make_executor()
        _setup_scan(ex, {"brave": (PLUGIN_BRAVE, PKG_BRAVE)})
        mgr = _make_manager(ex)

        result = await mgr.install_plugins(["brave", "nonexistent"])

        assert result["installed"] == ["brave"]
        assert len(result["failed"]) == 1
        assert result["failed"][0]["id"] == "nonexistent"


# ── TestUninstallPlugins ─────────────────────────────────


class TestUninstallPlugins:
    @pytest.mark.asyncio
    async def test_uninstall_removes_from_config(self):
        ex = _make_executor()
        ex.read_file = AsyncMock(return_value=OPENCLAW_CONFIG_WITH_INSTALLS)
        mgr = _make_manager(ex)

        result = await mgr.uninstall_plugins(["openai"])

        assert result["uninstalled"] == ["openai"]
        written = json.loads(ex.write_file.call_args[0][1].decode())
        assert "openai" not in written["plugins"]["entries"]
        assert "openai" not in written["plugins"]["installs"]
        assert "extensions/openai" not in written["plugins"]["load"]["paths"]

    @pytest.mark.asyncio
    async def test_uninstall_progress_callback(self):
        ex = _make_executor()
        ex.read_file = AsyncMock(return_value=OPENCLAW_CONFIG_WITH_INSTALLS)
        progress = MagicMock()
        mgr = _make_manager(ex, on_progress=progress)

        await mgr.uninstall_plugins(["openai"])

        progress.assert_any_call("openai", "running", "Uninstalling...")
        progress.assert_any_call("openai", "done", "Uninstalled")

    @pytest.mark.asyncio
    async def test_uninstall_clears_cache(self):
        ex = _make_executor()
        _setup_scan(ex, {"brave": (PLUGIN_BRAVE, PKG_BRAVE)})
        mgr = _make_manager(ex)

        await mgr.list_plugins()
        assert mgr._cached_plugins is not None
        # Override for uninstall
        ex.read_file = AsyncMock(return_value=OPENCLAW_CONFIG_EMPTY)
        await mgr.uninstall_plugins(["brave"])
        assert mgr._cached_plugins is None

    @pytest.mark.asyncio
    async def test_uninstall_nonexistent_graceful(self):
        ex = _make_executor()
        ex.read_file = AsyncMock(return_value=OPENCLAW_CONFIG_EMPTY)
        mgr = _make_manager(ex)

        result = await mgr.uninstall_plugins(["nonexistent"])

        assert result["uninstalled"] == ["nonexistent"]
        assert result["failed"] == []


# ── TestRemoteMode ───────────────────────────────────────


class TestRemoteMode:
    @pytest.mark.asyncio
    async def test_scan_uses_local_executor(self):
        main_ex = _make_executor()
        local_ex = _make_executor()
        _setup_scan(local_ex, {"brave": (PLUGIN_BRAVE, PKG_BRAVE)})
        # main executor returns config for openclaw.json
        main_ex.read_file = AsyncMock(return_value=OPENCLAW_CONFIG_EMPTY)

        mgr = _make_manager(main_ex, local_executor=local_ex)
        result = await mgr.list_plugins()

        assert len(result) == 1
        local_ex.list_dir.assert_called_once()
        # main executor used for openclaw.json
        main_ex.read_file.assert_called_once()

    @pytest.mark.asyncio
    async def test_install_writes_via_main_executor(self):
        main_ex = _make_executor()
        local_ex = _make_executor()
        _setup_scan(local_ex, {"brave": (PLUGIN_BRAVE, PKG_BRAVE)})
        main_ex.read_file = AsyncMock(return_value=OPENCLAW_CONFIG_EMPTY)

        mgr = _make_manager(main_ex, local_executor=local_ex)
        await mgr.install_plugins(["brave"])

        main_ex.write_file.assert_called_once()
        local_ex.write_file.assert_not_called()
