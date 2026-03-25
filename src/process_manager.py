"""Process Manager — 非同步 Subprocess 管理 (僅用於 docker/systemctl)。

封裝 Executor 的 run_command，提供逾時控制、graceful shutdown、
以及進度回呼機制。僅在呼叫外部程式時使用。
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable

from src.executor import CommandResult, Executor

logger = logging.getLogger(__name__)

# 預設逾時 300 秒（可透過 run() 參數覆寫）
DEFAULT_TIMEOUT = 300


class ProcessManager:
    """非同步子程序管理器。

    透過 Executor 介面執行外部指令，追蹤執行中的任務，
    支援 graceful shutdown 時取消所有進行中的操作。
    """

    def __init__(self, executor: Executor) -> None:
        self._executor = executor
        self._running_tasks: set[asyncio.Task] = set()

    @property
    def executor(self) -> Executor:
        return self._executor

    @executor.setter
    def executor(self, value: Executor) -> None:
        self._executor = value

    async def run(
        self,
        args: list[str],
        *,
        timeout: int = DEFAULT_TIMEOUT,
        on_output: Callable[[str], None] | None = None,
    ) -> CommandResult:
        """執行外部指令，回傳 CommandResult。

        Args:
            args: 指令與引數列表（list 形式，禁止 shell=True）。
            timeout: 逾時秒數，預設 300 秒。
            on_output: 即時輸出回呼（每行呼叫一次）。

        Returns:
            CommandResult 包含 exit_code, stdout, stderr。
        """
        task = asyncio.current_task()
        if task:
            self._running_tasks.add(task)

        try:
            result = await self._executor.run_command(
                args,
                timeout=timeout,
                on_output=on_output,
            )
            if not result.success:
                logger.warning(
                    "Command failed (exit=%d): %s\nstderr: %s",
                    result.exit_code,
                    " ".join(args),
                    result.stderr.strip(),
                )
            return result
        except asyncio.CancelledError:
            logger.info("Command cancelled: %s", " ".join(args))
            return CommandResult(exit_code=-2, stdout="", stderr="[CANCELLED]")
        except Exception:
            logger.exception("Command error: %s", " ".join(args))
            raise
        finally:
            if task:
                self._running_tasks.discard(task)

    async def shutdown(self) -> None:
        """取消所有執行中的任務（graceful shutdown）。"""
        if not self._running_tasks:
            return

        logger.info("Shutting down %d running task(s)", len(self._running_tasks))
        for task in list(self._running_tasks):
            task.cancel()

        # 等待所有任務結束（已 cancel 的會收到 CancelledError）
        await asyncio.gather(*self._running_tasks, return_exceptions=True)
        self._running_tasks.clear()
