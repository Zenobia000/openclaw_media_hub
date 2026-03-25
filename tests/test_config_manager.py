"""ConfigManager 單元測試 (WBS 3.5.6)。

測試 gui-settings.json、keyring、openclaw.json、.env 四大功能。
keyring 以 unittest.mock.patch 模擬。
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.config_manager import KEYRING_SERVICE, ConfigManager, _deep_merge


# ── Deep Merge ─────────────────────────────────────────


class TestDeepMerge:
    def test_flat_merge(self):
        assert _deep_merge({"a": 1}, {"b": 2}) == {"a": 1, "b": 2}

    def test_override_value(self):
        assert _deep_merge({"a": 1}, {"a": 2}) == {"a": 2}

    def test_nested_merge(self):
        base = {"x": {"a": 1, "b": 2}}
        override = {"x": {"b": 3, "c": 4}}
        assert _deep_merge(base, override) == {"x": {"a": 1, "b": 3, "c": 4}}

    def test_base_unchanged(self):
        base = {"a": {"nested": 1}}
        _deep_merge(base, {"a": {"other": 2}})
        assert base == {"a": {"nested": 1}}


# ── gui-settings.json ──────────────────────────────────


class TestGuiSettings:
    def test_read_nonexistent(self, tmp_path: Path):
        mgr = ConfigManager(app_data_dir=tmp_path / "no-such-dir")
        assert mgr.read_gui_settings() == {}

    def test_write_then_read(self, tmp_path: Path):
        mgr = ConfigManager(app_data_dir=tmp_path)
        mgr.write_gui_settings({"deployment_mode": "docker-windows"})
        assert mgr.read_gui_settings()["deployment_mode"] == "docker-windows"

    def test_upsert_preserves_existing(self, tmp_path: Path):
        mgr = ConfigManager(app_data_dir=tmp_path)
        mgr.write_gui_settings({"deployment_mode": "docker-windows", "extra": "keep"})
        mgr.write_gui_settings({"deployment_mode": "native-linux"})
        s = mgr.read_gui_settings()
        assert s["deployment_mode"] == "native-linux"
        assert s["extra"] == "keep"

    def test_get_deployment_mode(self, tmp_path: Path):
        mgr = ConfigManager(app_data_dir=tmp_path)
        assert mgr.get_deployment_mode() is None
        mgr.write_gui_settings({"deployment_mode": "remote-ssh"})
        assert mgr.get_deployment_mode() == "remote-ssh"

    def test_ssh_settings_roundtrip(self, tmp_path: Path):
        mgr = ConfigManager(app_data_dir=tmp_path)
        mgr.save_ssh_settings("192.168.1.100", 2222, "ubuntu", "~/.ssh/id_rsa")
        ssh = mgr.get_ssh_settings()
        assert ssh["host"] == "192.168.1.100"
        assert ssh["port"] == 2222
        assert ssh["username"] == "ubuntu"
        assert ssh["key_path"] == "~/.ssh/id_rsa"

    def test_ssh_settings_default_port(self, tmp_path: Path):
        mgr = ConfigManager(app_data_dir=tmp_path)
        ssh = mgr.get_ssh_settings()
        assert ssh["port"] == 22
        assert ssh["host"] is None


# ── Keyring ────────────────────────────────────────────


class TestKeyring:
    @patch("src.config_manager.keyring")
    def test_get_secret(self, mock_kr: MagicMock, tmp_path: Path):
        mock_kr.get_password.return_value = "sk-123"
        mgr = ConfigManager(app_data_dir=tmp_path)
        assert mgr.get_secret("openai_api_key") == "sk-123"
        mock_kr.get_password.assert_called_once_with(KEYRING_SERVICE, "openai_api_key")

    @patch("src.config_manager.keyring")
    def test_set_secret(self, mock_kr: MagicMock, tmp_path: Path):
        mgr = ConfigManager(app_data_dir=tmp_path)
        mgr.set_secret("openai_api_key", "sk-456")
        mock_kr.set_password.assert_called_once_with(KEYRING_SERVICE, "openai_api_key", "sk-456")

    @patch("src.config_manager.keyring")
    def test_delete_secret_exists(self, mock_kr: MagicMock, tmp_path: Path):
        mgr = ConfigManager(app_data_dir=tmp_path)
        mgr.delete_secret("old_key")
        mock_kr.delete_password.assert_called_once_with(KEYRING_SERVICE, "old_key")

    @patch("src.config_manager.keyring")
    def test_delete_secret_not_found(self, mock_kr: MagicMock, tmp_path: Path):
        import keyring.errors
        mock_kr.delete_password.side_effect = keyring.errors.PasswordDeleteError
        mock_kr.errors = keyring.errors
        mgr = ConfigManager(app_data_dir=tmp_path)
        mgr.delete_secret("nonexistent")  # should not raise

    @patch("src.config_manager.keyring")
    def test_set_secrets_batch(self, mock_kr: MagicMock, tmp_path: Path):
        mgr = ConfigManager(app_data_dir=tmp_path)
        count = mgr.set_secrets_batch({
            "key_a": "val_a",
            "key_b": "",       # 空值跳過
            "key_c": "val_c",
        })
        assert count == 2
        assert mock_kr.set_password.call_count == 2


# ── openclaw.json ──────────────────────────────────────


class TestOpenclawConfig:
    def test_read_nonexistent(self, tmp_path: Path):
        mgr = ConfigManager(app_data_dir=tmp_path)
        assert mgr.read_openclaw_config(str(tmp_path)) == {}

    def test_write_creates_file(self, tmp_path: Path):
        mgr = ConfigManager(app_data_dir=tmp_path)
        mgr.write_openclaw_config(str(tmp_path), {"gateway": {"port": 18789}})
        data = json.loads((tmp_path / "openclaw.json").read_text("utf-8"))
        assert data["gateway"]["port"] == 18789

    def test_section_read(self, tmp_path: Path):
        config = {"gateway": {"port": 18789}, "meta": {"version": "1.0"}}
        (tmp_path / "openclaw.json").write_text(json.dumps(config), encoding="utf-8")
        mgr = ConfigManager(app_data_dir=tmp_path)
        assert mgr.read_openclaw_config(str(tmp_path), "gateway") == {"port": 18789}
        assert mgr.read_openclaw_config(str(tmp_path), "nonexistent") == {}

    def test_section_write_deep_merge(self, tmp_path: Path):
        config = {"gateway": {"port": 18789, "bind": "lan"}, "meta": {"v": "1"}}
        (tmp_path / "openclaw.json").write_text(json.dumps(config), encoding="utf-8")
        mgr = ConfigManager(app_data_dir=tmp_path)
        mgr.write_openclaw_config(str(tmp_path), {"mode": "local"}, section="gateway")
        result = json.loads((tmp_path / "openclaw.json").read_text("utf-8"))
        assert result["gateway"] == {"port": 18789, "bind": "lan", "mode": "local"}
        assert result["meta"] == {"v": "1"}

    def test_backup_created(self, tmp_path: Path):
        (tmp_path / "openclaw.json").write_text('{"a": 1}', encoding="utf-8")
        mgr = ConfigManager(app_data_dir=tmp_path)
        mgr.write_openclaw_config(str(tmp_path), {"b": 2})
        bak = tmp_path / "openclaw.json.bak"
        assert bak.exists()
        assert json.loads(bak.read_text("utf-8")) == {"a": 1}


# ── .env ───────────────────────────────────────────────


class TestEnv:
    def test_read_nonexistent(self, tmp_path: Path):
        mgr = ConfigManager(app_data_dir=tmp_path)
        assert mgr.read_env(str(tmp_path / ".env")) == {}

    def test_read_with_comments(self, tmp_path: Path):
        env = tmp_path / ".env"
        env.write_text("# comment\nFOO=bar\n\nBAZ=qux\n", encoding="utf-8")
        mgr = ConfigManager(app_data_dir=tmp_path)
        result = mgr.read_env(str(env))
        assert result == {"FOO": "bar", "BAZ": "qux"}

    def test_read_strips_quotes(self, tmp_path: Path):
        env = tmp_path / ".env"
        env.write_text('KEY="quoted"\nKEY2=\'single\'\n', encoding="utf-8")
        mgr = ConfigManager(app_data_dir=tmp_path)
        result = mgr.read_env(str(env))
        assert result["KEY"] == "quoted"
        assert result["KEY2"] == "single"

    def test_upsert_updates_and_adds(self, tmp_path: Path):
        env = tmp_path / ".env"
        env.write_text("# header\nFOO=old\nBAR=keep\n", encoding="utf-8")
        mgr = ConfigManager(app_data_dir=tmp_path)
        mgr.write_env(str(env), {"FOO": "new", "NEW_KEY": "added"})
        content = env.read_text("utf-8")
        lines = content.strip().splitlines()
        assert "# header" in lines
        assert "FOO=new" in lines
        assert "BAR=keep" in lines
        assert "NEW_KEY=added" in lines

    def test_write_creates_parent_dirs(self, tmp_path: Path):
        env_path = tmp_path / "sub" / "dir" / ".env"
        mgr = ConfigManager(app_data_dir=tmp_path)
        mgr.write_env(str(env_path), {"KEY": "val"})
        assert env_path.exists()
        assert mgr.read_env(str(env_path)) == {"KEY": "val"}
