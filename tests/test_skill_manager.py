"""SkillManager 單元測試 (WBS 3.10)。

以 Mock Executor 驗證技能掃描、frontmatter 解析、部署與移除邏輯。
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, call

import pytest

from src.skill_manager import SkillManager, _parse_frontmatter


# ── Helpers ───────────────────────────────────────────────


def _make_executor() -> MagicMock:
    executor = MagicMock()
    executor.list_dir = AsyncMock(return_value=[])
    executor.read_file = AsyncMock(return_value=b"")
    executor.file_exists = AsyncMock(return_value=False)
    executor.copy_tree = AsyncMock()
    executor.remove_tree = AsyncMock()
    executor.mkdir = AsyncMock()
    return executor


def _make_manager(
    executor=None,
    *,
    local_executor=None,
    transfer_service=None,
    on_progress=None,
) -> SkillManager:
    return SkillManager(
        executor or _make_executor(),
        module_pack_dir="./module_pack",
        community_skills_dir="./openclaw/skills",
        config_dir="/home/test/.openclaw",
        local_executor=local_executor,
        transfer_service=transfer_service,
        on_progress=on_progress,
    )


# ── SKILL.md 範例 ────────────────────────────────────────

PURE_YAML_SKILL = """\
---
name: calendar-booking
description: "解析使用者訊息中的自然語言日期時間，查詢空檔。
  適用時機：使用者想預約。"
metadata:
  openclaw:
    emoji: "📅"
    requires:
      bins: ["python3"]
---

# Calendar Booking Skill
"""

JSON_INLINE_SKILL = """\
---
name: discord
description: "Discord ops via the message tool (channel=discord)."
metadata: { "openclaw": { "emoji": "🎮", "requires": { "config": ["channels.discord.token"] } } }
allowed-tools: ["message"]
---

# Discord
"""

JSON_MULTILINE_SKILL = """\
---
name: github
description: "GitHub operations via gh CLI."
metadata:
  {
    "openclaw":
      {
        "emoji": "🐙",
        "requires": { "bins": ["gh"] }
      }
  }
---

# GitHub
"""

NO_METADATA_SKILL = """\
---
name: simple-skill
description: "A skill without metadata."
---
"""

NO_FRONTMATTER = """\
# Just a readme

No frontmatter at all.
"""


# ── TestParseFrontmatter ─────────────────────────────────


class TestParseFrontmatter:
    def test_pure_yaml_format(self):
        result = _parse_frontmatter(PURE_YAML_SKILL)
        assert result["name"] == "calendar-booking"
        assert "自然語言" in result["description"]
        assert result["emoji"] == "📅"

    def test_json_inline_format(self):
        result = _parse_frontmatter(JSON_INLINE_SKILL)
        assert result["name"] == "discord"
        assert result["emoji"] == "🎮"

    def test_json_multiline_format(self):
        result = _parse_frontmatter(JSON_MULTILINE_SKILL)
        assert result["name"] == "github"
        assert result["emoji"] == "🐙"

    def test_missing_metadata_returns_default_emoji(self):
        result = _parse_frontmatter(NO_METADATA_SKILL)
        assert result["name"] == "simple-skill"
        assert result["emoji"] == "📦"
        assert result["description"] == "A skill without metadata."

    def test_no_frontmatter_returns_empty(self):
        result = _parse_frontmatter(NO_FRONTMATTER)
        assert result["name"] == ""
        assert result["emoji"] == "📦"

    def test_multiline_description_joined(self):
        result = _parse_frontmatter(PURE_YAML_SKILL)
        # 多行描述應被合併為單行
        assert "\n" not in result["description"]
        assert "適用時機" in result["description"]


# ── TestListSkills ────────────────────────────────────────


class TestListSkills:
    @pytest.mark.asyncio
    async def test_scans_both_sources(self):
        ex = _make_executor()
        # module_pack: one module dir → one skill
        ex.list_dir = AsyncMock(side_effect=[
            # module_pack top-level
            ["module_01_booking", "config", "troubleshooting"],
            # module_01_booking children
            ["calendar-booking"],
            # community top-level
            ["discord", "github"],
        ])
        ex.read_file = AsyncMock(side_effect=[
            PURE_YAML_SKILL.encode(),
            JSON_INLINE_SKILL.encode(),
            JSON_MULTILINE_SKILL.encode(),
        ])
        ex.file_exists = AsyncMock(return_value=False)

        mgr = _make_manager(ex)
        skills = await mgr.list_skills()

        assert len(skills) == 3
        names = {s["name"] for s in skills}
        assert names == {"calendar-booking", "discord", "github"}
        sources = {s["source"] for s in skills}
        assert sources == {"module_pack", "community"}

    @pytest.mark.asyncio
    async def test_installed_detection(self):
        ex = _make_executor()
        ex.list_dir = AsyncMock(side_effect=[
            [],  # module_pack: empty
            ["discord"],  # community
        ])
        ex.read_file = AsyncMock(return_value=JSON_INLINE_SKILL.encode())
        ex.file_exists = AsyncMock(return_value=True)  # installed

        mgr = _make_manager(ex)
        skills = await mgr.list_skills()

        assert len(skills) == 1
        assert skills[0]["installed"] is True

    @pytest.mark.asyncio
    async def test_empty_sources(self):
        ex = _make_executor()
        ex.list_dir = AsyncMock(side_effect=[
            FileNotFoundError("no dir"),
            FileNotFoundError("no dir"),
        ])

        mgr = _make_manager(ex)
        skills = await mgr.list_skills()
        assert skills == []

    @pytest.mark.asyncio
    async def test_malformed_skill_md_skipped(self):
        ex = _make_executor()
        ex.list_dir = AsyncMock(side_effect=[
            [],  # module_pack: empty
            ["broken-skill"],  # community
        ])
        # SKILL.md exists but is garbage
        ex.read_file = AsyncMock(return_value=b"not a valid skill file")
        ex.file_exists = AsyncMock(return_value=False)

        mgr = _make_manager(ex)
        skills = await mgr.list_skills()

        # Should not crash; uses dir name as fallback name
        assert len(skills) == 1
        assert skills[0]["name"] == "broken-skill"

    @pytest.mark.asyncio
    async def test_caches_result(self):
        ex = _make_executor()
        ex.list_dir = AsyncMock(side_effect=[
            [],  # module_pack
            ["discord"],  # community
        ])
        ex.read_file = AsyncMock(return_value=JSON_INLINE_SKILL.encode())
        ex.file_exists = AsyncMock(return_value=False)

        mgr = _make_manager(ex)
        first = await mgr.list_skills()
        second = await mgr.list_skills()
        assert first is second  # Same cached list
        # list_dir called only once per source (2 total)
        assert ex.list_dir.call_count == 2


# ── TestDeploySkills ──────────────────────────────────────


class TestDeploySkills:
    @pytest.mark.asyncio
    async def test_local_deploy_uses_copy_tree(self):
        ex = _make_executor()
        ex.list_dir = AsyncMock(side_effect=[
            [],
            ["discord"],
        ])
        ex.read_file = AsyncMock(return_value=JSON_INLINE_SKILL.encode())
        ex.file_exists = AsyncMock(return_value=False)

        mgr = _make_manager(ex)
        result = await mgr.deploy_skills(["discord"])

        assert result["deployed"] == ["discord"]
        assert result["failed"] == []
        ex.copy_tree.assert_called_once()
        dst = ex.copy_tree.call_args[0][1]
        assert dst == "/home/test/.openclaw/workspace/skills/discord"

    @pytest.mark.asyncio
    async def test_remote_deploy_uses_transfer_service(self):
        ex = _make_executor()
        local_ex = _make_executor()
        transfer = MagicMock()
        transfer.upload_tree = AsyncMock(return_value=5)

        # Scanning uses local_executor
        local_ex.list_dir = AsyncMock(side_effect=[
            [],
            ["discord"],
        ])
        local_ex.read_file = AsyncMock(return_value=JSON_INLINE_SKILL.encode())
        ex.file_exists = AsyncMock(return_value=False)

        mgr = _make_manager(
            ex,
            local_executor=local_ex,
            transfer_service=transfer,
        )
        result = await mgr.deploy_skills(["discord"])

        assert result["deployed"] == ["discord"]
        transfer.upload_tree.assert_called_once()
        ex.copy_tree.assert_not_called()

    @pytest.mark.asyncio
    async def test_deploy_nonexistent_skill_fails(self):
        ex = _make_executor()
        ex.list_dir = AsyncMock(side_effect=[[], []])  # empty sources

        mgr = _make_manager(ex)
        result = await mgr.deploy_skills(["ghost-skill"])

        assert result["deployed"] == []
        assert len(result["failed"]) == 1
        assert result["failed"][0]["name"] == "ghost-skill"

    @pytest.mark.asyncio
    async def test_progress_callback_fired(self):
        ex = _make_executor()
        ex.list_dir = AsyncMock(side_effect=[
            [],
            ["discord"],
        ])
        ex.read_file = AsyncMock(return_value=JSON_INLINE_SKILL.encode())
        ex.file_exists = AsyncMock(return_value=False)

        progress_calls: list[tuple] = []

        def on_progress(name, status, message):
            progress_calls.append((name, status, message))

        mgr = _make_manager(ex, on_progress=on_progress)
        await mgr.deploy_skills(["discord"])

        assert len(progress_calls) == 2
        assert progress_calls[0] == ("discord", "running", "Deploying...")
        assert progress_calls[1] == ("discord", "done", "Deployed")

    @pytest.mark.asyncio
    async def test_partial_failure(self):
        ex = _make_executor()
        ex.list_dir = AsyncMock(side_effect=[
            [],
            ["discord", "github"],
        ])
        ex.read_file = AsyncMock(side_effect=[
            JSON_INLINE_SKILL.encode(),
            JSON_MULTILINE_SKILL.encode(),
        ])
        ex.file_exists = AsyncMock(return_value=False)
        # First copy succeeds, second fails
        ex.copy_tree = AsyncMock(side_effect=[None, OSError("disk full")])

        mgr = _make_manager(ex)
        result = await mgr.deploy_skills(["discord", "github"])

        assert result["deployed"] == ["discord"]
        assert len(result["failed"]) == 1
        assert result["failed"][0]["name"] == "github"

    @pytest.mark.asyncio
    async def test_deploy_clears_cache(self):
        ex = _make_executor()
        ex.list_dir = AsyncMock(side_effect=[
            [],
            ["discord"],
            # Second scan after cache clear
            [],
            ["discord"],
        ])
        ex.read_file = AsyncMock(return_value=JSON_INLINE_SKILL.encode())
        ex.file_exists = AsyncMock(return_value=False)

        mgr = _make_manager(ex)
        await mgr.list_skills()
        assert mgr._cached_skills is not None
        await mgr.deploy_skills(["discord"])
        assert mgr._cached_skills is None


# ── TestRemoveSkills ──────────────────────────────────────


class TestRemoveSkills:
    @pytest.mark.asyncio
    async def test_remove_success(self):
        ex = _make_executor()
        ex.file_exists = AsyncMock(return_value=True)

        mgr = _make_manager(ex)
        result = await mgr.remove_skills(["discord"])

        assert result["removed"] == ["discord"]
        assert result["failed"] == []
        ex.remove_tree.assert_called_once_with(
            "/home/test/.openclaw/workspace/skills/discord"
        )

    @pytest.mark.asyncio
    async def test_remove_not_deployed(self):
        ex = _make_executor()
        ex.file_exists = AsyncMock(return_value=False)

        mgr = _make_manager(ex)
        result = await mgr.remove_skills(["ghost"])

        assert result["removed"] == []
        assert len(result["failed"]) == 1
        assert result["failed"][0]["name"] == "ghost"
        ex.remove_tree.assert_not_called()

    @pytest.mark.asyncio
    async def test_remove_progress_callback(self):
        ex = _make_executor()
        ex.file_exists = AsyncMock(return_value=True)

        progress_calls: list[tuple] = []

        def on_progress(name, status, message):
            progress_calls.append((name, status, message))

        mgr = _make_manager(ex, on_progress=on_progress)
        await mgr.remove_skills(["discord"])

        assert len(progress_calls) == 2
        assert progress_calls[0] == ("discord", "running", "Removing...")
        assert progress_calls[1] == ("discord", "done", "Removed")

    @pytest.mark.asyncio
    async def test_remove_clears_cache(self):
        ex = _make_executor()
        ex.list_dir = AsyncMock(side_effect=[[], []])
        ex.file_exists = AsyncMock(return_value=True)

        mgr = _make_manager(ex)
        await mgr.list_skills()
        assert mgr._cached_skills is not None
        await mgr.remove_skills(["discord"])
        assert mgr._cached_skills is None
