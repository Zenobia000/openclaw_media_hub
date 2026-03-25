"""Skill Manager — 技能部署邏輯 (掃描、解析 SKILL.md、複製/移除)。

掃描 module_pack/（自訂業務模組）與 openclaw/skills/（社群技能），
解析 SKILL.md YAML frontmatter，執行 copytree/rmtree 部署至工作空間。
"""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Callable
from typing import TYPE_CHECKING

from src.executor import Executor

if TYPE_CHECKING:
    from src.transfer_service import TransferService

logger = logging.getLogger(__name__)

# ── Frontmatter 解析 ─────────────────────────────────────

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)
_DEFAULT_EMOJI = "📦"


def _parse_frontmatter(content: str) -> dict:
    """解析 SKILL.md YAML frontmatter，回傳 {name, description, emoji}。

    支援三種格式:
    1. Pure YAML:  metadata:\\n  openclaw:\\n    emoji: "📅"
    2. JSON inline: metadata: { "openclaw": { "emoji": "🎮" } }
    3. JSON multi-line: metadata:\\n  {\\n    "openclaw": ...\\n  }
    """
    m = _FRONTMATTER_RE.search(content)
    if not m:
        return {"name": "", "description": "", "emoji": _DEFAULT_EMOJI}

    block = m.group(1)
    name = _extract_simple_value(block, "name")
    description = _extract_description(block)
    emoji = _extract_emoji(block)

    return {"name": name, "description": description, "emoji": emoji}


def _extract_simple_value(block: str, key: str) -> str:
    """擷取頂層 key: value（單行，可帶引號）。"""
    pattern = re.compile(rf"^{key}:\s*(.+)$", re.MULTILINE)
    m = pattern.search(block)
    if not m:
        return ""
    return m.group(1).strip().strip("\"'")


def _extract_description(block: str) -> str:
    """擷取 description（可能為多行引號字串）。"""
    # 嘗試匹配多行引號: description: "...\n  ...\n  ..."
    m = re.search(r'^description:\s*"((?:[^"\\]|\\.)*)"', block, re.MULTILINE | re.DOTALL)
    if m:
        # 合併多行、清理縮排
        raw = m.group(1)
        lines = raw.split("\n")
        cleaned = " ".join(line.strip() for line in lines if line.strip())
        return cleaned

    # 單行無引號
    m = re.search(r"^description:\s*(.+)$", block, re.MULTILINE)
    if m:
        return m.group(1).strip().strip("\"'")
    return ""


def _extract_emoji(block: str) -> str:
    """從 metadata 區塊擷取 openclaw.emoji。"""
    # 找 metadata: 行的位置（[ \t]* 避免 \s 跨行）
    meta_match = re.search(r"^metadata:[ \t]*(.*)$", block, re.MULTILINE)
    if not meta_match:
        return _DEFAULT_EMOJI

    inline_rest = meta_match.group(1).strip()
    meta_start = meta_match.end()
    after_meta = block[meta_start:]

    # Case 1: JSON inline — metadata: { ... }
    if inline_rest.startswith("{"):
        return _emoji_from_json(inline_rest)

    # Case 2: JSON multi-line — metadata:\n  { ... }
    # Collect everything after 'metadata:' to end of frontmatter block
    json_candidate = after_meta.strip()
    if json_candidate.startswith("{"):
        return _emoji_from_json(json_candidate)

    # Case 3: Pure YAML — metadata:\n  openclaw:\n    emoji: "📅"
    m = re.search(r'emoji:\s*["\']?([^"\'\n]+)', after_meta)
    if m:
        return m.group(1).strip().strip("\"'")

    return _DEFAULT_EMOJI


def _emoji_from_json(text: str) -> str:
    """從 JSON 文字擷取 openclaw.emoji。"""
    try:
        data = json.loads(text)
        return data.get("openclaw", {}).get("emoji", _DEFAULT_EMOJI)
    except (json.JSONDecodeError, AttributeError):
        return _DEFAULT_EMOJI


# ── SkillManager ──────────────────────────────────────────


class SkillManager:
    """技能模組管理器。"""

    def __init__(
        self,
        executor: Executor,
        *,
        module_pack_dir: str,
        community_skills_dir: str,
        config_dir: str,
        local_executor: Executor | None = None,
        transfer_service: TransferService | None = None,
        on_progress: Callable[[str, str, str], None] | None = None,
    ) -> None:
        self._executor = executor
        self._module_pack_dir = module_pack_dir
        self._community_skills_dir = community_skills_dir
        self._config_dir = config_dir
        self._local_executor = local_executor
        self._transfer_service = transfer_service
        self._on_progress = on_progress
        self._cached_skills: list[dict] | None = None

    @property
    def _skills_dir(self) -> str:
        return f"{self._config_dir}/workspace/skills"

    def _fire_progress(self, name: str, status: str, message: str) -> None:
        if self._on_progress:
            self._on_progress(name, status, message)

    # ── 掃描 ──────────────────────────────────────────────

    async def _scan_source(
        self,
        scan_executor: Executor,
        base_dir: str,
        source_label: str,
        *,
        nested: bool,
    ) -> list[dict]:
        """掃描技能來源目錄，回傳技能元資料清單。

        Args:
            nested: True = module_pack（二層目錄），False = community（一層目錄）
        """
        results: list[dict] = []
        try:
            top_entries = await scan_executor.list_dir(base_dir)
        except (FileNotFoundError, OSError):
            logger.warning("Skill source not found: %s", base_dir)
            return results

        skill_dirs: list[str] = []

        if nested:
            # module_pack/module_XX_*/skill_name/
            for module_dir_name in top_entries:
                if not module_dir_name.startswith("module_"):
                    continue
                module_path = f"{base_dir}/{module_dir_name}"
                try:
                    sub_entries = await scan_executor.list_dir(module_path)
                except (FileNotFoundError, OSError):
                    continue
                for sub in sub_entries:
                    skill_dirs.append(f"{module_path}/{sub}")
        else:
            # openclaw/skills/skill_name/
            for entry in top_entries:
                skill_dirs.append(f"{base_dir}/{entry}")

        for skill_path in skill_dirs:
            skill_md_path = f"{skill_path}/SKILL.md"
            try:
                content_bytes = await scan_executor.read_file(skill_md_path)
                content = content_bytes.decode("utf-8", errors="replace")
            except (FileNotFoundError, OSError):
                continue

            parsed = _parse_frontmatter(content)
            if not parsed["name"]:
                # 用目錄名作為 fallback
                parsed["name"] = skill_path.rsplit("/", 1)[-1]

            results.append({
                "name": parsed["name"],
                "emoji": parsed["emoji"],
                "description": parsed["description"],
                "source": source_label,
                "source_path": skill_path,
            })

        return results

    async def list_skills(self) -> list[dict]:
        """掃描可用技能，回傳清單。

        Returns:
            [{"name": str, "emoji": str, "description": str,
              "installed": bool, "source": str}]
        """
        if self._cached_skills is not None:
            return self._cached_skills

        scan_ex = self._local_executor or self._executor

        module_pack_skills = await self._scan_source(
            scan_ex, self._module_pack_dir, "module_pack", nested=True,
        )
        community_skills = await self._scan_source(
            scan_ex, self._community_skills_dir, "community", nested=False,
        )

        all_skills = module_pack_skills + community_skills

        # 檢查已部署狀態
        for skill in all_skills:
            target = f"{self._skills_dir}/{skill['name']}"
            try:
                skill["installed"] = await self._executor.file_exists(target)
            except (OSError, Exception):
                skill["installed"] = False

        self._cached_skills = all_skills
        return all_skills

    # ── 部署 ──────────────────────────────────────────────

    async def deploy_skills(self, names: list[str]) -> dict:
        """部署指定技能至工作空間。

        Returns:
            {"deployed": [str], "failed": [{"name": str, "error": str}]}
        """
        all_skills = await self.list_skills()
        skill_map = {s["name"]: s for s in all_skills}

        deployed: list[str] = []
        failed: list[dict] = []

        for name in names:
            if name not in skill_map:
                self._fire_progress(name, "failed", f"Skill '{name}' not found")
                failed.append({"name": name, "error": f"Skill '{name}' not found"})
                continue

            skill = skill_map[name]
            src = skill["source_path"]
            dst = f"{self._skills_dir}/{name}"

            self._fire_progress(name, "running", "Deploying...")
            try:
                if self._transfer_service:
                    await self._transfer_service.upload_tree(src, dst)
                else:
                    await self._executor.copy_tree(src, dst)
                self._fire_progress(name, "done", "Deployed")
                deployed.append(name)
            except Exception as exc:
                err_msg = str(exc)[:200]
                self._fire_progress(name, "failed", f"Failed: {err_msg}")
                failed.append({"name": name, "error": err_msg})

        self._cached_skills = None
        return {"deployed": deployed, "failed": failed}

    # ── 移除 ──────────────────────────────────────────────

    async def remove_skills(self, names: list[str]) -> dict:
        """從工作空間移除指定技能。

        Returns:
            {"removed": [str], "failed": [{"name": str, "error": str}]}
        """
        removed: list[str] = []
        failed: list[dict] = []

        for name in names:
            target = f"{self._skills_dir}/{name}"
            self._fire_progress(name, "running", "Removing...")
            try:
                exists = await self._executor.file_exists(target)
                if not exists:
                    self._fire_progress(name, "failed", "Not deployed")
                    failed.append({"name": name, "error": "Not deployed"})
                    continue
                await self._executor.remove_tree(target)
                self._fire_progress(name, "done", "Removed")
                removed.append(name)
            except Exception as exc:
                err_msg = str(exc)[:200]
                self._fire_progress(name, "failed", f"Failed: {err_msg}")
                failed.append({"name": name, "error": err_msg})

        self._cached_skills = None
        return {"removed": removed, "failed": failed}
