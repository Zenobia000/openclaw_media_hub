"""Env Checker — 環境檢查邏輯 (Python 原生實作)。

以 Executor.which() 偵測軟體、Executor.run_command() 取版本號，
回傳結構化檢查結果供前端渲染狀態卡片。
"""

from __future__ import annotations

from src.executor import Executor


class EnvChecker:
    """環境依賴檢查器。"""

    def __init__(self, executor: Executor) -> None:
        self._executor = executor

    async def check_all(self) -> list[dict]:
        """執行所有環境檢查，回傳結構化結果。

        Returns:
            [{"name": str, "installed": bool, "version": str|None, "message": str}]
        """
        raise NotImplementedError
