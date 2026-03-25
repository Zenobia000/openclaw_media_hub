"""Executor Protocol — Transport Layer 核心介面 (ADR-004).

定義統一的操作介面，讓上層模組不需要知道操作發生在本機或遠端。
LocalExecutor 封裝 subprocess/pathlib/shutil，
RemoteExecutor 封裝 paramiko SSH/SFTP。
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class CommandResult:
    """外部指令執行結果。"""

    exit_code: int
    stdout: str
    stderr: str

    @property
    def success(self) -> bool:
        return self.exit_code == 0


@runtime_checkable
class Executor(Protocol):
    """統一操作介面 — 所有後端模組透過此 Protocol 執行系統操作。

    本機模式使用 LocalExecutor，遠端模式使用 RemoteExecutor，
    上層模組無需感知執行位置。
    """

    async def run_command(
        self,
        args: list[str],
        *,
        timeout: int = 300,
        on_output: Callable[[str], None] | None = None,
    ) -> CommandResult:
        """執行外部指令。

        Args:
            args: 指令與引數列表（禁止 shell=True）。
            timeout: 逾時秒數，預設 300 秒。
            on_output: 即時輸出回呼（每行呼叫一次），用於長時間操作的進度回饋。

        Returns:
            CommandResult 包含 exit_code, stdout, stderr。
        """
        ...

    async def read_file(self, path: str) -> bytes:
        """讀取檔案內容（二進位）。"""
        ...

    async def write_file(self, path: str, data: bytes) -> None:
        """寫入檔案內容（二進位）。目標目錄必須已存在。"""
        ...

    async def mkdir(self, path: str, *, parents: bool = True) -> None:
        """建立目錄。parents=True 時遞迴建立父目錄。"""
        ...

    async def copy_tree(self, src: str, dst: str) -> None:
        """遞迴複製目錄樹。"""
        ...

    async def remove_tree(self, path: str) -> None:
        """遞迴刪除目錄樹。"""
        ...

    async def file_exists(self, path: str) -> bool:
        """檢查檔案或目錄是否存在。"""
        ...

    async def list_dir(self, path: str) -> list[str]:
        """列出目錄內容（僅名稱，不含路徑前綴）。"""
        ...

    async def which(self, name: str) -> str | None:
        """查找可執行檔路徑。找不到時回傳 None。"""
        ...
