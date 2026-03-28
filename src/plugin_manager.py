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
_CATEGORY_COLORS = {
    "providers": "#8B5CF6",
    "channels": "#3B82F6",
    "tools": "#F59E0B",
    "infrastructure": "#10B981",
}


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
        self._last_diagnosis: list[dict] | None = None

    # ── 內部工具 ──────────────────────────────────────────

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

    @staticmethod
    def _ensure_plugins_section(config: dict) -> tuple[dict, dict, list[str]]:
        """確保 config 中 plugins 區段完整，回傳 (entries, installs, paths)。"""
        section = config.setdefault("plugins", {})
        section.setdefault("enabled", True)
        entries = section.setdefault("entries", {})
        installs = section.setdefault("installs", {})
        load = section.setdefault("load", {})
        paths: list[str] = load.setdefault("paths", [])
        return entries, installs, paths

    # ── 公開 API ─────────────────────────────────────────────

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
        entries, installs, paths = self._ensure_plugins_section(config)

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
                    "source": "path",
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
        entries, installs, paths = self._ensure_plugins_section(config)

        uninstalled: list[str] = []
        failed: list[dict] = []

        for pid in ids:
            self._fire(pid, "running", "Uninstalling...")
            try:
                # 從 installs 記錄取得實際路徑，避免寫死
                install_info = installs.pop(pid, None)
                entries.pop(pid, None)
                lp = (install_info or {}).get("installPath", f"extensions/{pid}")
                # installPath 可能是絕對路徑，load.paths 用相對路徑
                rel_lp = f"extensions/{pid}"
                for candidate in (lp, rel_lp):
                    if candidate in paths:
                        paths.remove(candidate)
                uninstalled.append(pid)
                self._fire(pid, "done", "Uninstalled")
            except Exception as exc:
                self._fire(pid, "failed", str(exc))
                failed.append({"id": pid, "error": str(exc)})

        await self._write_target_config(config)
        self._cached_plugins = None
        return {"uninstalled": uninstalled, "failed": failed}

    # ── 診斷與修復 (WBS 3.12) ──────────────────────────────

    async def _get_plugin_category(self, plugin_id: str) -> str:
        """從本機 extensions 讀取外掛分類（若無法讀取則回傳 "tools"）。"""
        scan = self._local_executor or self._executor
        try:
            raw = await scan.read_file(
                f"{self._extensions_dir}/{plugin_id}/openclaw.plugin.json",
            )
            pj = json.loads(raw.decode("utf-8"))
            return _categorize(pj)
        except Exception:
            return "tools"

    async def diagnose_plugins(self) -> list[dict]:
        """診斷已安裝外掛的健康狀態。

        Returns:
            [{"name", "status", "issues", "icon", "icon_color"}]
        """
        config = await self._read_target_config()
        installs = config.get("plugins", {}).get("installs", {})
        if not installs:
            self._last_diagnosis = []
            return []

        entries = config.get("plugins", {}).get("entries", {})
        paths = config.get("plugins", {}).get("load", {}).get("paths", [])
        scan = self._local_executor or self._executor

        results: list[dict] = []
        for pid in installs:
            issues: list[str] = []

            # Check 1: entries sync
            entry = entries.get(pid)
            if not entry or not entry.get("enabled"):
                issues.append(
                    "Missing or disabled entry in plugins.entries"
                    " \u2014 plugin may not load",
                )

            # Check 2: source directory exists
            ext_dir = f"{self._extensions_dir}/{pid}"
            try:
                await scan.list_dir(ext_dir)
            except Exception:
                issues.append(
                    f"Extension source directory not found: {ext_dir}",
                )

            # Check 3: manifest valid
            manifest_ok = True
            try:
                raw = await scan.read_file(f"{ext_dir}/openclaw.plugin.json")
                pj = json.loads(raw.decode("utf-8"))
                if not pj.get("id"):
                    issues.append("Plugin manifest missing required 'id' field")
                    manifest_ok = False
            except json.JSONDecodeError:
                issues.append("Plugin manifest contains invalid JSON")
                manifest_ok = False
            except Exception:
                # source dir already flagged above; skip duplicate
                manifest_ok = False

            # Check 4: load path present
            expected_path = f"extensions/{pid}"
            if expected_path not in paths:
                issues.append(
                    f"Missing load path '{expected_path}' in plugins.load.paths",
                )

            category = _categorize(pj) if manifest_ok else await self._get_plugin_category(pid)
            results.append({
                "name": pid,
                "status": "healthy" if not issues else "broken",
                "issues": issues,
                "icon": pid[0].upper(),
                "icon_color": _CATEGORY_COLORS.get(category, "#6B7280"),
            })

        results.sort(key=lambda x: (0 if x["status"] == "broken" else 1, x["name"]))
        self._last_diagnosis = results
        return results

    async def fix_plugins(self, ids: list[str]) -> dict:
        """修復指定外掛（自動修正可修復的問題）。

        Returns:
            {"fixed": [str], "failed": [{"id": str, "error": str}]}
        """
        config = await self._read_target_config()
        entries, installs, paths = self._ensure_plugins_section(config)
        scan = self._local_executor or self._executor

        fixed: list[str] = []
        failed: list[dict] = []

        for pid in ids:
            self._fire(pid, "running", "Diagnosing...")
            repairs: list[str] = []
            unfixable: list[str] = []

            # Check source exists
            ext_dir = f"{self._extensions_dir}/{pid}"
            source_exists = True
            try:
                await scan.list_dir(ext_dir)
            except Exception:
                source_exists = False

            if not source_exists:
                # Orphaned install — clean up
                self._fire(pid, "running", "Removing orphaned install...")
                installs.pop(pid, None)
                entries.pop(pid, None)
                expected = f"extensions/{pid}"
                if expected in paths:
                    paths.remove(expected)
                repairs.append("Removed orphaned install (source not found)")
            else:
                # Validate manifest
                manifest_valid = True
                try:
                    raw = await scan.read_file(f"{ext_dir}/openclaw.plugin.json")
                    pj = json.loads(raw.decode("utf-8"))
                    if not pj.get("id"):
                        unfixable.append("Manifest missing 'id' field — manual fix required")
                        manifest_valid = False
                except json.JSONDecodeError:
                    unfixable.append("Invalid JSON in manifest — manual fix required")
                    manifest_valid = False
                except Exception:
                    unfixable.append("Cannot read manifest — manual fix required")
                    manifest_valid = False

                # Fix missing entries
                entry = entries.get(pid)
                if not entry or not entry.get("enabled"):
                    self._fire(pid, "running", "Restoring plugin entry...")
                    entries[pid] = {"enabled": True}
                    repairs.append("Restored plugins.entries")

                # Fix missing load path
                expected = f"extensions/{pid}"
                if expected not in paths:
                    self._fire(pid, "running", "Restoring load path...")
                    paths.append(expected)
                    repairs.append("Restored load path")

            if unfixable:
                msg = "; ".join(unfixable)
                self._fire(pid, "failed", msg)
                failed.append({"id": pid, "error": msg})
            elif repairs:
                self._fire(pid, "done", "Fixed: " + ", ".join(repairs))
                fixed.append(pid)
            else:
                self._fire(pid, "done", "Already healthy")
                fixed.append(pid)

        await self._write_target_config(config)
        self._cached_plugins = None
        self._last_diagnosis = None
        return {"fixed": fixed, "failed": failed}

    async def fix_all_plugins(self) -> dict:
        """修復所有有問題的外掛。"""
        if self._last_diagnosis is None:
            await self.diagnose_plugins()
        broken_ids = [
            r["name"] for r in (self._last_diagnosis or [])
            if r["status"] == "broken"
        ]
        if not broken_ids:
            return {"fixed": [], "failed": []}
        return await self.fix_plugins(broken_ids)
