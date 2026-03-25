"""Config Manager — 設定與金鑰管理 (keyring 整合)。

管理 gui-settings.json（GUI 自身設定）、openclaw.json（主設定檔）、
.env 環境變數檔案，以及透過 keyring 安全儲存金鑰。
"""

from __future__ import annotations

import json
import os
import platform
from pathlib import Path

import keyring
import keyring.errors

KEYRING_SERVICE = "openclaw-gui"


def _default_app_data_dir() -> Path:
    """取得 GUI 設定目錄的預設路徑。"""
    if platform.system() == "Windows":
        return Path.home() / ".openclaw-gui"
    base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "openclaw-gui"


def _deep_merge(base: dict, override: dict) -> dict:
    """遞迴合併 — override 覆蓋 base，保留 base 中不在 override 的 key。"""
    result = base.copy()
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


class ConfigManager:
    """統一設定與金鑰管理。"""

    def __init__(self, app_data_dir: Path | None = None) -> None:
        self._app_data_dir = (app_data_dir or _default_app_data_dir()).expanduser()
        self._settings_path = self._app_data_dir / "gui-settings.json"

    # ── gui-settings.json (3.5.1 + 3.5.7) ────────────────

    def read_gui_settings(self) -> dict:
        """讀取 gui-settings.json，不存在回傳空 dict。"""
        if not self._settings_path.exists():
            return {}
        return json.loads(self._settings_path.read_text("utf-8"))

    def write_gui_settings(self, settings: dict) -> None:
        """Upsert gui-settings.json（merge 已有值 + 新值）。"""
        existing = self.read_gui_settings()
        merged = _deep_merge(existing, settings)
        self._app_data_dir.mkdir(parents=True, exist_ok=True)
        self._settings_path.write_text(
            json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8",
        )

    def get_deployment_mode(self) -> str | None:
        """讀取 deployment_mode（不存在回 None）。"""
        return self.read_gui_settings().get("deployment_mode")

    def get_ssh_settings(self) -> dict:
        """回傳 SSH 連線設定 {host, port, username, key_path}。"""
        s = self.read_gui_settings()
        return {
            "host": s.get("ssh_host"),
            "port": s.get("ssh_port", 22),
            "username": s.get("ssh_username"),
            "key_path": s.get("ssh_key_path"),
        }

    def save_ssh_settings(
        self, host: str, port: int, username: str, key_path: str | None = None,
    ) -> None:
        """寫入 SSH 設定至 gui-settings.json。"""
        data: dict = {
            "ssh_host": host,
            "ssh_port": port,
            "ssh_username": username,
        }
        if key_path is not None:
            data["ssh_key_path"] = key_path
        self.write_gui_settings(data)

    # ── keyring (3.5.2) ──────────────────────────────────

    def get_secret(self, key: str) -> str | None:
        """從 keyring 安全儲存讀取金鑰。"""
        return keyring.get_password(KEYRING_SERVICE, key)

    def set_secret(self, key: str, value: str) -> None:
        """將金鑰寫入 keyring 安全儲存。"""
        keyring.set_password(KEYRING_SERVICE, key, value)

    def delete_secret(self, key: str) -> None:
        """刪除 keyring 中的金鑰。"""
        try:
            keyring.delete_password(KEYRING_SERVICE, key)
        except keyring.errors.PasswordDeleteError:
            pass

    def set_secrets_batch(self, secrets: dict[str, str]) -> int:
        """批量寫入金鑰，回傳成功數。空值跳過。"""
        count = 0
        for key, value in secrets.items():
            if value:
                self.set_secret(key, value)
                count += 1
        return count

    # ── openclaw.json (3.5.3) ────────────────────────────

    def read_openclaw_config(
        self, config_dir: str, section: str | None = None,
    ) -> dict:
        """讀取 {config_dir}/openclaw.json。section 為 None 回傳全部。"""
        path = Path(config_dir).expanduser() / "openclaw.json"
        if not path.exists():
            return {}
        data = json.loads(path.read_text("utf-8"))
        if section:
            return data.get(section, {})
        return data

    def write_openclaw_config(
        self, config_dir: str, data: dict, section: str | None = None,
    ) -> None:
        """Deep merge 寫入 openclaw.json。寫入前建立 .bak 備份。"""
        path = Path(config_dir).expanduser() / "openclaw.json"
        existing = json.loads(path.read_text("utf-8")) if path.exists() else {}

        # 備份
        if path.exists():
            bak = path.with_name("openclaw.json.bak")
            bak.write_text(path.read_text("utf-8"), encoding="utf-8")

        if section:
            existing[section] = _deep_merge(existing.get(section, {}), data)
        else:
            existing = _deep_merge(existing, data)

        # 原子寫入 (temp → rename)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name("openclaw.json.tmp")
        tmp.write_text(
            json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8",
        )
        tmp.replace(path)

    # ── .env (3.5.4) ────────────────────────────────────

    def read_env(self, env_path: str) -> dict[str, str]:
        """解析 .env，回傳 {KEY: VALUE}。忽略註解和空行。"""
        path = Path(env_path).expanduser()
        if not path.exists():
            return {}
        result: dict[str, str] = {}
        for line in path.read_text("utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" in stripped:
                k, _, v = stripped.partition("=")
                result[k.strip()] = v.strip().strip('"').strip("'")
        return result

    def write_env(self, env_path: str, values: dict[str, str]) -> None:
        """Upsert .env — 更新已有 key，新增不存在的，保留未指定的行。"""
        path = Path(env_path).expanduser()
        lines = path.read_text("utf-8").splitlines() if path.exists() else []

        updated_keys: set[str] = set()
        new_lines: list[str] = []
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and "=" in stripped:
                key = stripped.partition("=")[0].strip()
                if key in values:
                    new_lines.append(f"{key}={values[key]}")
                    updated_keys.add(key)
                    continue
            new_lines.append(line)

        for k, v in values.items():
            if k not in updated_keys:
                new_lines.append(f"{k}={v}")

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
