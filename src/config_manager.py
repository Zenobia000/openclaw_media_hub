"""Config Manager — 設定與金鑰管理 (keyring 整合)。

管理 gui-settings.json（GUI 自身設定）、openclaw.json（主設定檔）、
.env 環境變數檔案，以及透過 keyring 安全儲存金鑰。
"""

from __future__ import annotations

from pathlib import Path


class ConfigManager:
    """統一設定與金鑰管理。"""

    def __init__(self, config_dir: Path | None = None) -> None:
        self._config_dir = config_dir

    def get_secret(self, key: str) -> str | None:
        """從 keyring 安全儲存讀取金鑰。"""
        raise NotImplementedError

    def set_secret(self, key: str, value: str) -> None:
        """將金鑰寫入 keyring 安全儲存。"""
        raise NotImplementedError

    def read_config(self) -> dict:
        """讀取 openclaw.json 設定檔。"""
        raise NotImplementedError

    def write_config(self, data: dict) -> None:
        """寫入 openclaw.json 設定檔（deep merge 策略）。"""
        raise NotImplementedError

    def read_env(self) -> dict[str, str]:
        """讀取 .env 檔案，回傳鍵值對。"""
        raise NotImplementedError

    def write_env(self, values: dict[str, str]) -> None:
        """Upsert .env 檔案中的環境變數。"""
        raise NotImplementedError
