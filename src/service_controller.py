"""Service Controller — 服務啟停控制 (docker compose / systemctl)。

透過 Executor 介面執行服務控制指令，本機模式由 LocalExecutor 呼叫
subprocess，遠端模式由 RemoteExecutor 透過 SSH 執行。
"""

from __future__ import annotations

from src.executor import Executor


class ServiceController:
    """服務啟停控制器。"""

    def __init__(self, executor: Executor) -> None:
        self._executor = executor

    async def start(self) -> dict:
        """啟動服務。

        Returns:
            {"success": bool, "message": str}
        """
        raise NotImplementedError

    async def stop(self) -> dict:
        """停止服務。"""
        raise NotImplementedError

    async def status(self) -> dict:
        """查詢服務狀態。"""
        raise NotImplementedError
