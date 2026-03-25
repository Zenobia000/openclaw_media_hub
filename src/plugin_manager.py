"""Plugin Manager — 外掛管理邏輯。

掃描 openclaw/extensions/ 目錄，讀取 openclaw.plugin.json + package.json，
透過修改 openclaw.json 的 plugins 區段實現安裝/移除。
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from datetime import datetime, timezone

from src.executor import Executor

logger = logging.getLogger(__name__)

_CATEGORY_PRIORITY = {"providers": 0, "channels": 1, "tools": 2, "infrastructure": 3}


def _categorize(plugin_json: dict) -> str:
    """依據 openclaw.plugin.json 欄位推導分類。"""
    if plugin_json.get("providers"):
        return "providers"
    if plugin_json.get("channels"):
        return "channels"
    if plugin_json.get("kind"):
        return "infrastructure"
    return "tools"


class PluginManager:
    """外掛模組管理器（config-driven 安裝/移除）。"""

    def __init__(
        self,
        executor: Executor,
        *,
        extensions_dir: str,
        config_dir: str,
        local_executor: Executor | None = None,
        on_progress: Callable[[str, str, str], None] | None = None,
    ) -> None:
        self._executor = executor
        self._extensions_dir = extensions_dir
        self._config_dir = config_dir
        self._local_executor = local_executor
        self._on_progress = on_progress
        self._cached_plugins: list[dict] | None = None

    # ── private helpers ──────────────────────────────────────

    def _fire(self, name: str, status: str, message: str) -> None:
        if self._on_progress:
            self._on_progress(name, status, message)

    async def _read_target_config(self) -> dict:
        path = f"{self._config_dir}/openclaw.json"
        try:
            raw = await self._executor.read_file(path)
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return {}

    async def _write_target_config(self, data: dict) -> None:
        path = f"{self._config_dir}/openclaw.json"
        raw = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
        await self._executor.write_file(path, raw)

    async def _scan_extensions(self) -> list[dict]:
        """掃描本機 extensions 目錄，回傳外掛元資料清單。"""
        scan = self._local_executor or self._executor
        try:
            entries = await scan.list_dir(self._extensions_dir)
        except Exception:
            logger.warning("Cannot list extensions dir: %s", self._extensions_dir)
            return []

        plugins: list[dict] = []
        for name in entries:
            base = f"{self._extensions_dir}/{name}"
            # read openclaw.plugin.json
            try:
                raw = await scan.read_file(f"{base}/openclaw.plugin.json")
                pj = json.loads(raw.decode("utf-8"))
            except Exception:
                continue  # skip dirs without valid plugin manifest

            plugin_id = pj.get("id", name)
            category = _categorize(pj)

            # read package.json for description / channel metadata
            description = pj.get("description", "")
            channel_label: str | None = None
            channel_blurb: str | None = None
            local_path = f"extensions/{plugin_id}"
            try:
                pkg_raw = await scan.read_file(f"{base}/package.json")
                pkg = json.loads(pkg_raw.decode("utf-8"))
                if not description:
                    description = pkg.get("description", "")
                oc = pkg.get("openclaw", {})
                ch = oc.get("channel", {})
                channel_label = ch.get("label")
                channel_blurb = ch.get("blurb")
                inst = oc.get("install", {})
                if inst.get("localPath"):
                    local_path = inst["localPath"]
            except Exception:
                pass

            plugins.append({
                "id": plugin_id,
                "description": description,
                "category": category,
                "source_path": base,
                "channel_label": channel_label,
                "channel_blurb": channel_blurb,
                "local_path": local_path,
            })

        return plugins

    # ── public API ───────────────────────────────────────────

    async def list_plugins(self) -> list[dict]:
        """掃描可用外掛，回傳分類清單（含已安裝狀態）。

        Returns:
            [{"id", "description", "category", "installed",
              "channel_label", "channel_blurb"}]
        """
        if self._cached_plugins is not None:
            return self._cached_plugins

        scanned = await self._scan_extensions()
        config = await self._read_target_config()
        installed_ids = set(config.get("plugins", {}).get("installs", {}).keys())

        result = []
        for p in scanned:
            result.append({
                "id": p["id"],
                "description": p["description"],
                "category": p["category"],
                "installed": p["id"] in installed_ids,
                "channel_label": p["channel_label"],
                "channel_blurb": p["channel_blurb"],
            })

        result.sort(key=lambda x: (_CATEGORY_PRIORITY.get(x["category"], 99), x["id"]))
        self._cached_plugins = result
        return result

    async def install_plugins(self, ids: list[str]) -> dict:
        """安裝指定外掛（修改目標端 openclaw.json）。

        Returns:
            {"installed": [str], "failed": [{"id": str, "error": str}]}
        """
        all_plugins = await self.list_plugins()
        plugin_map = {p["id"]: p for p in all_plugins}
        # 取得 local_path 資訊（list_plugins 回傳不含此欄位）
        scanned = await self._scan_extensions()
        scan_map = {p["id"]: p for p in scanned}

        config = await self._read_target_config()
        plugins_section = config.setdefault("plugins", {})
        plugins_section.setdefault("enabled", True)
        entries = plugins_section.setdefault("entries", {})
        installs = plugins_section.setdefault("installs", {})
        load = plugins_section.setdefault("load", {})
        paths: list[str] = load.setdefault("paths", [])

        installed: list[str] = []
        failed: list[dict] = []

        for pid in ids:
            self._fire(pid, "running", "Installing...")
            if pid not in plugin_map:
                self._fire(pid, "failed", f"Plugin '{pid}' not found")
                failed.append({"id": pid, "error": f"Plugin '{pid}' not found"})
                continue
            try:
                entries[pid] = {"enabled": True}
                installs[pid] = {
                    "installedAt": datetime.now(timezone.utc).isoformat(),
                    "installPath": f"~/.openclaw/extensions/{pid}",
                }
                lp = scan_map.get(pid, {}).get("local_path", f"extensions/{pid}")
                if lp not in paths:
                    paths.append(lp)
                installed.append(pid)
                self._fire(pid, "done", "Installed")
            except Exception as exc:
                self._fire(pid, "failed", str(exc))
                failed.append({"id": pid, "error": str(exc)})

        await self._write_target_config(config)
        self._cached_plugins = None
        return {"installed": installed, "failed": failed}

    async def uninstall_plugins(self, ids: list[str]) -> dict:
        """移除指定外掛（從目標端 openclaw.json 移除）。

        Returns:
            {"uninstalled": [str], "failed": [{"id": str, "error": str}]}
        """
        config = await self._read_target_config()
        plugins_section = config.get("plugins", {})
        entries = plugins_section.get("entries", {})
        installs = plugins_section.get("installs", {})
        paths: list[str] = plugins_section.get("load", {}).get("paths", [])

        uninstalled: list[str] = []
        failed: list[dict] = []

        for pid in ids:
            self._fire(pid, "running", "Uninstalling...")
            try:
                entries.pop(pid, None)
                installs.pop(pid, None)
                lp = f"extensions/{pid}"
                if lp in paths:
                    paths.remove(lp)
                uninstalled.append(pid)
                self._fire(pid, "done", "Uninstalled")
            except Exception as exc:
                self._fire(pid, "failed", str(exc))
                failed.append({"id": pid, "error": str(exc)})

        await self._write_target_config(config)
        self._cached_plugins = None
        return {"uninstalled": uninstalled, "failed": failed}

    async def fix_plugin(self, plugin_id: str) -> dict:
        """診斷並修復指定外掛（WBS 3.12）。"""
        raise NotImplementedError
