"""RemoteExecutor — 遠端操作實作 (ADR-004).

封裝 paramiko SSHClient + SFTPClient，透過 SSH 在遠端伺服器執行操作。
所有 paramiko 同步呼叫透過 asyncio.to_thread 包裝。
"""

from __future__ import annotations

import asyncio
import stat
from collections.abc import Callable
from pathlib import PurePosixPath

from src.executor import CommandResult
from src.ssh_connection import SSHConnection


def _shell_quote(s: str) -> str:
    """用單引號包裝 shell 引數，防止注入。"""
    return "'" + s.replace("'", "'\"'\"'") + "'"


class RemoteExecutor:
    """遠端 Executor 實作 — paramiko SSH + SFTP。"""

    def __init__(self, connection: SSHConnection) -> None:
        self._conn = connection

    async def run_command(
        self,
        args: list[str],
        *,
        timeout: int = 300,
        on_output: Callable[[str], None] | None = None,
    ) -> CommandResult:
        def _exec() -> CommandResult:
            client = self._conn.get_client()
            cmd = " ".join(_shell_quote(a) for a in args)

            _, stdout_ch, stderr_ch = client.exec_command(cmd, timeout=timeout)

            stdout_lines: list[str] = []
            stderr_lines: list[str] = []

            # 串流讀取 stdout
            for line_bytes in stdout_ch:
                line = line_bytes.rstrip("\n")
                stdout_lines.append(line + "\n")
                if on_output:
                    on_output(line)

            stderr_lines = stderr_ch.readlines()
            exit_code = stdout_ch.channel.recv_exit_status()

            return CommandResult(
                exit_code=exit_code,
                stdout="".join(stdout_lines),
                stderr="".join(stderr_lines),
            )

        return await asyncio.to_thread(_exec)

    async def read_file(self, path: str) -> bytes:
        def _read() -> bytes:
            sftp = self._conn.get_sftp()
            with sftp.open(path, "rb") as f:
                return f.read()

        return await asyncio.to_thread(_read)

    async def write_file(self, path: str, data: bytes) -> None:
        def _write() -> None:
            sftp = self._conn.get_sftp()
            with sftp.open(path, "wb") as f:
                f.write(data)

        await asyncio.to_thread(_write)

    async def mkdir(self, path: str, *, parents: bool = True) -> None:
        def _mkdir() -> None:
            sftp = self._conn.get_sftp()
            if parents:
                self._sftp_makedirs(sftp, path)
            else:
                try:
                    sftp.mkdir(path)
                except OSError:
                    if not self._sftp_isdir(sftp, path):
                        raise

        await asyncio.to_thread(_mkdir)

    async def copy_tree(self, src: str, dst: str) -> None:
        """遞迴複製遠端目錄（SFTP 無原生 copytree）。

        src 與 dst 皆為遠端路徑。若需跨機器傳輸請用 TransferService。
        """
        def _copy() -> None:
            sftp = self._conn.get_sftp()
            self._sftp_copytree(sftp, src, dst)

        await asyncio.to_thread(_copy)

    async def remove_tree(self, path: str) -> None:
        def _remove() -> None:
            sftp = self._conn.get_sftp()
            self._sftp_rmtree(sftp, path)

        await asyncio.to_thread(_remove)

    async def file_exists(self, path: str) -> bool:
        def _exists() -> bool:
            sftp = self._conn.get_sftp()
            try:
                sftp.stat(path)
                return True
            except FileNotFoundError:
                return False

        return await asyncio.to_thread(_exists)

    async def list_dir(self, path: str) -> list[str]:
        def _list() -> list[str]:
            sftp = self._conn.get_sftp()
            return sorted(sftp.listdir(path))

        return await asyncio.to_thread(_list)

    async def which(self, name: str) -> str | None:
        result = await self.run_command(["command", "-v", name], timeout=10)
        if result.success:
            return result.stdout.strip()
        return None

    # ── SFTP 輔助操作 ────────────────────────────────────

    @staticmethod
    def _sftp_isdir(sftp, path: str) -> bool:
        """判斷遠端路徑是否為目錄。"""
        try:
            return stat.S_ISDIR(sftp.stat(path).st_mode)
        except (FileNotFoundError, OSError):
            return False

    @staticmethod
    def _sftp_makedirs(sftp, path: str) -> None:
        """遞迴建立遠端目錄（模擬 mkdir -p）。"""
        parts: list[str] = []
        current = path
        while current and current != "/":
            parts.append(current)
            parent = str(PurePosixPath(current).parent)
            if parent == current:
                break
            current = parent

        for dir_path in reversed(parts):
            try:
                sftp.stat(dir_path)
            except FileNotFoundError:
                sftp.mkdir(dir_path)

    @staticmethod
    def _sftp_copytree(sftp, src: str, dst: str) -> None:
        """遞迴複製遠端目錄。"""
        RemoteExecutor._sftp_makedirs(sftp, dst)
        for item in sftp.listdir_attr(src):
            src_path = str(PurePosixPath(src) / item.filename)
            dst_path = str(PurePosixPath(dst) / item.filename)
            if stat.S_ISDIR(item.st_mode):
                RemoteExecutor._sftp_copytree(sftp, src_path, dst_path)
            else:
                # 分塊串流複製，避免大檔案撐爆記憶體
                with sftp.open(src_path, "rb") as sf, sftp.open(dst_path, "wb") as df:
                    while True:
                        chunk = sf.read(65536)  # 64 KB
                        if not chunk:
                            break
                        df.write(chunk)

    @staticmethod
    def _sftp_rmtree(sftp, path: str) -> None:
        """遞迴刪除遠端目錄（深度優先）。"""
        for item in sftp.listdir_attr(path):
            item_path = str(PurePosixPath(path) / item.filename)
            if stat.S_ISDIR(item.st_mode):
                RemoteExecutor._sftp_rmtree(sftp, item_path)
            else:
                sftp.remove(item_path)
        sftp.rmdir(path)
