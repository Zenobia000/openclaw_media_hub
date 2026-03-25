"""Initializer — 初始化邏輯 (目錄建立、config 產生、docker compose)。

依序執行 11 步初始化流程：驗證環境、建立目錄結構、產生設定檔、
Build/Pull Docker Image、執行 Onboarding、啟動 Gateway、Health Check。
"""

from __future__ import annotations

from collections.abc import Callable

from src.executor import Executor


class Initializer:
    """系統初始化執行器。"""

    def __init__(self, executor: Executor) -> None:
        self._executor = executor

    async def run_all(
        self,
        on_step: Callable[[int, str, str], None] | None = None,
    ) -> dict:
        """執行完整初始化流程。

        Args:
            on_step: 進度回呼 (step_number, status, message)

        Returns:
            {"success": bool, "steps": [...], "error": str|None}
        """
        raise NotImplementedError
