"""Skill Manager — 技能部署邏輯 (掃描、解析 SKILL.md、複製/移除)。

掃描 module_pack/（自訂業務模組）與 openclaw/skills/（社群技能），
解析 SKILL.md YAML frontmatter，執行 copytree/rmtree 部署至工作空間。
"""

from __future__ import annotations

from src.executor import Executor


class SkillManager:
    """技能模組管理器。"""

    def __init__(self, executor: Executor) -> None:
        self._executor = executor

    async def list_skills(self) -> list[dict]:
        """掃描可用技能，回傳清單。

        Returns:
            [{"name": str, "emoji": str, "description": str,
              "installed": bool, "source": str}]
        """
        raise NotImplementedError

    async def deploy_skills(self, names: list[str]) -> dict:
        """部署指定技能至工作空間。"""
        raise NotImplementedError

    async def remove_skills(self, names: list[str]) -> dict:
        """從工作空間移除指定技能。"""
        raise NotImplementedError
