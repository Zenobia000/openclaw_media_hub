"""Process Manager — 非同步 Subprocess 管理 (僅用於 docker/systemctl)。

封裝 Executor 的 run_command，提供逾時控制、graceful shutdown、
以及進度回呼機制。僅在呼叫外部程式時使用。
"""

from __future__ import annotations

from collections.abc import Callable

from src.executor import CommandResult, Executor


class ProcessManager:
    """非同步子程序管理器。"""

    def __init__(self, executor: Executor) -> None:
        self._executor = executor

    async def run(
        self,
        args: list[str],
        *,
        timeout: int = 300,
        on_output: Callable[[str], None] | None = None,
    ) -> CommandResult:
        """執行外部指令，回傳 CommandResult。"""
        raise NotImplementedError
