"""Bridge API Step 2 單元測試 (WBS 3.7)。

測試 registries 資料完整性、Bridge get_available_* 回傳格式、save_keys 整合。
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.registries import CHANNEL_REGISTRY, PROVIDER_REGISTRY, TOOL_REGISTRY


# ── Registry 結構驗證 ────────────────────────────────────


class TestProviderRegistry:
    def test_required_fields(self):
        for p in PROVIDER_REGISTRY:
            assert "name" in p, f"Missing 'name': {p}"
            assert "label" in p, f"Missing 'label': {p}"
            assert "env_var" in p, f"Missing 'env_var': {p}"
            assert "placeholder" in p, f"Missing 'placeholder': {p}"
            assert "primary" in p, f"Missing 'primary': {p}"

    def test_no_duplicate_names(self):
        names = [p["name"] for p in PROVIDER_REGISTRY]
        assert len(names) == len(set(names))

    def test_no_duplicate_env_vars(self):
        env_vars = [p["env_var"] for p in PROVIDER_REGISTRY if p["env_var"]]
        assert len(env_vars) == len(set(env_vars))

    def test_primary_count(self):
        primary = [p for p in PROVIDER_REGISTRY if p["primary"]]
        assert len(primary) == 6

    def test_ollama_no_key(self):
        ollama = next(p for p in PROVIDER_REGISTRY if p["name"] == "ollama")
        assert ollama["env_var"] is None


class TestChannelRegistry:
    def test_required_fields(self):
        for c in CHANNEL_REGISTRY:
            assert "name" in c, f"Missing 'name': {c}"
            assert "label" in c, f"Missing 'label': {c}"
            assert "icon" in c, f"Missing 'icon': {c}"
            assert "icon_color" in c, f"Missing 'icon_color': {c}"
            assert "fields" in c, f"Missing 'fields': {c}"
            assert "primary" in c, f"Missing 'primary': {c}"

    def test_field_structure(self):
        for c in CHANNEL_REGISTRY:
            for f in c["fields"]:
                assert "key" in f, f"Missing 'key' in field of {c['name']}"
                assert "label" in f, f"Missing 'label' in field of {c['name']}"

    def test_no_duplicate_names(self):
        names = [c["name"] for c in CHANNEL_REGISTRY]
        assert len(names) == len(set(names))

    def test_primary_count(self):
        primary = [c for c in CHANNEL_REGISTRY if c["primary"]]
        assert len(primary) == 5

    def test_line_has_two_fields(self):
        line = next(c for c in CHANNEL_REGISTRY if c["name"] == "line")
        assert len(line["fields"]) == 2

    def test_whatsapp_has_info_note(self):
        wa = next(c for c in CHANNEL_REGISTRY if c["name"] == "whatsapp")
        assert wa["info_note"]
        assert len(wa["fields"]) == 0


class TestToolRegistry:
    def test_required_fields(self):
        for t in TOOL_REGISTRY:
            assert "name" in t, f"Missing 'name': {t}"
            assert "label" in t, f"Missing 'label': {t}"
            assert "env_var" in t, f"Missing 'env_var': {t}"
            assert "placeholder" in t, f"Missing 'placeholder': {t}"

    def test_no_duplicate_env_vars(self):
        env_vars = [t["env_var"] for t in TOOL_REGISTRY]
        assert len(env_vars) == len(set(env_vars))

    def test_count(self):
        assert len(TOOL_REGISTRY) == 5


# ── Bridge API 回傳格式 ─────────────────────────────────


class TestBridgeRegistryAPIs:
    @pytest.fixture()
    def bridge(self):
        with (
            patch("src.bridge.LocalExecutor"),
            patch("src.bridge.ConfigManager"),
            patch("src.bridge.ProcessManager"),
        ):
            from src.bridge import Bridge

            b = Bridge()
            return b

    def test_get_available_providers(self, bridge):
        result = bridge.get_available_providers()
        assert result["success"] is True
        data = result["data"]
        assert isinstance(data, list)
        assert len(data) == len(PROVIDER_REGISTRY)
        assert data[0]["name"] == "openai"

    def test_get_available_channels(self, bridge):
        result = bridge.get_available_channels()
        assert result["success"] is True
        data = result["data"]
        assert isinstance(data, list)
        assert len(data) == len(CHANNEL_REGISTRY)
        assert data[0]["name"] == "line"

    def test_get_available_tools(self, bridge):
        result = bridge.get_available_tools()
        assert result["success"] is True
        data = result["data"]
        assert isinstance(data, list)
        assert len(data) == 5


# ── save_keys 整合 ───────────────────────────────────────


class TestSaveKeys:
    @pytest.fixture()
    def bridge(self):
        with (
            patch("src.bridge.LocalExecutor"),
            patch("src.bridge.ProcessManager"),
        ):
            from src.bridge import Bridge

            b = Bridge()
            b._config_manager = MagicMock()
            b._config_manager.set_secrets_batch.return_value = 3
            return b

    def test_save_keys_flattens_categories(self, bridge):
        keys = {
            "providers": {"openai_api_key": "sk-test"},
            "channels": {"discord_bot_token": "disc-test"},
            "tools": {"brave_api_key": "bsa-test"},
        }
        result = bridge.save_keys(keys)
        assert result["success"] is True
        assert result["data"]["saved_count"] == 3

        call_args = bridge._config_manager.set_secrets_batch.call_args[0][0]
        assert call_args == {
            "openai_api_key": "sk-test",
            "discord_bot_token": "disc-test",
            "brave_api_key": "bsa-test",
        }

    def test_save_keys_empty(self, bridge):
        bridge._config_manager.set_secrets_batch.return_value = 0
        result = bridge.save_keys({})
        assert result["success"] is True
        assert result["data"]["saved_count"] == 0
