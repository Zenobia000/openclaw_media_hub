"""LocalExecutor — 本機操作實作 (ADR-004).

封裝 subprocess, pathlib, shutil，用於本機模式。
所有阻塞操作透過 asyncio.to_thread 避免阻塞事件迴圈。
"""

from __future__ import annotations

import asyncio
import shutil
from collections.abc import Callable
from pathlib import Path

from src.executor import CommandResult


class LocalExecutor:
    """本機 Executor 實作 — subprocess + pathlib + shutil。"""

    @staticmethod
    def _resolve(path: str) -> Path:
        """展開 ~ 並正規化路徑。"""
        return Path(path).expanduser()

    async def run_command(
        self,
        args: list[str],
        *,
        timeout: int = 300,
        on_output: Callable[[str], None] | None = None,
    ) -> CommandResult:
        # Windows: create_subprocess_exec 不搜尋 .cmd/.bat，需先解析完整路徑
        resolved = await asyncio.to_thread(shutil.which, args[0])
        cmd = [resolved or args[0]] + args[1:]

        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError:
            return CommandResult(exit_code=-1, stdout="", stderr=f"Command not found: {args[0]}")

        stdout_lines: list[str] = []
        stderr_lines: list[str] = []

        try:
            await asyncio.wait_for(
                asyncio.gather(
                    self._read_stream(proc.stdout, stdout_lines, on_output),  # type: ignore[arg-type]
                    self._read_stream(proc.stderr, stderr_lines, None),
                ),
                timeout=timeout,
            )
            await proc.wait()
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return CommandResult(
                exit_code=-1,
                stdout="".join(stdout_lines),
                stderr="".join(stderr_lines) + "\n[TIMEOUT]",
            )

        return CommandResult(
            # wait() 後 returncode 不應為 None，防禦性處理
            exit_code=proc.returncode if proc.returncode is not None else -1,
            stdout="".join(stdout_lines),
            stderr="".join(stderr_lines),
        )

    @staticmethod
    async def _read_stream(
        stream: asyncio.StreamReader,
        buf: list[str],
        callback: Callable[[str], None] | None,
    ) -> None:
        """逐行讀取 subprocess 輸出串流。"""
        while True:
            line_bytes = await stream.readline()
            if not line_bytes:
                break
            line = line_bytes.decode("utf-8", errors="replace")
            buf.append(line)
            if callback:
                callback(line.rstrip("\n"))

    async def read_file(self, path: str) -> bytes:
        return await asyncio.to_thread(self._resolve(path).read_bytes)

    async def write_file(self, path: str, data: bytes) -> None:
        await asyncio.to_thread(self._resolve(path).write_bytes, data)

    async def mkdir(self, path: str, *, parents: bool = True) -> None:
        await asyncio.to_thread(self._resolve(path).mkdir, parents=parents, exist_ok=True)

    async def copy_tree(self, src: str, dst: str) -> None:
        await asyncio.to_thread(shutil.copytree, self._resolve(src), self._resolve(dst), dirs_exist_ok=True)

    async def remove_tree(self, path: str) -> None:
        await asyncio.to_thread(shutil.rmtree, self._resolve(path))

    async def file_exists(self, path: str) -> bool:
        return await asyncio.to_thread(self._resolve(path).exists)

    async def list_dir(self, path: str) -> list[str]:
        def _list() -> list[str]:
            return sorted(item.name for item in self._resolve(path).iterdir())

        return await asyncio.to_thread(_list)

    async def which(self, name: str) -> str | None:
        return await asyncio.to_thread(shutil.which, name)
