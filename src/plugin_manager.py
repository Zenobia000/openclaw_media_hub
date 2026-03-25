"""Plugin Manager — 外掛管理邏輯。

掃描 openclaw/extensions/ 目錄，讀取 openclaw.plugin.json，
透過修改 openclaw.json 的 plugins 區段實現安裝/移除/修復。
"""

from __future__ import annotations

from src.executor import Executor


class PluginManager:
    """外掛模組管理器。"""

    def __init__(self, executor: Executor) -> None:
        self._executor = executor

    async def list_plugins(self) -> list[dict]:
        """掃描可用外掛，回傳分類清單。

        Returns:
            [{"id": str, "name": str, "category": str,
              "channels": list, "providers": list, "installed": bool}]
        """
        raise NotImplementedError

    async def install_plugins(self, ids: list[str]) -> dict:
        """安裝指定外掛（修改 openclaw.json plugins 區段）。"""
        raise NotImplementedError

    async def fix_plugin(self, plugin_id: str) -> dict:
        """診斷並修復指定外掛。"""
        raise NotImplementedError
