"""RemoteExecutor — 遠端操作實作 (ADR-004).

封裝 paramiko SSHClient + SFTPClient，透過 SSH 在遠端伺服器執行操作。
所有 paramiko 同步呼叫透過 asyncio.to_thread 包裝。
"""

from __future__ import annotations

import asyncio
import stat
from collections.abc import Callable

from src.executor import CommandResult
from src.ssh_connection import SSHConnection


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
            # 將 args list 組成 shell 指令（每個 arg 用單引號包裝避免注入）
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
                _sftp_makedirs(sftp, path)
            else:
                try:
                    sftp.mkdir(path)
                except OSError:
                    # 目錄已存在
                    if not _sftp_isdir(sftp, path):
                        raise

        await asyncio.to_thread(_mkdir)

    async def copy_tree(self, src: str, dst: str) -> None:
        """遞迴上傳目錄（SFTP 無原生 copytree）。

        src 與 dst 皆為遠端路徑。若需跨機器傳輸請用 TransferService。
        """
        def _copy() -> None:
            sftp = self._conn.get_sftp()
            _sftp_copytree(sftp, src, dst)

        await asyncio.to_thread(_copy)

    async def remove_tree(self, path: str) -> None:
        def _remove() -> None:
            sftp = self._conn.get_sftp()
            _sftp_rmtree(sftp, path)

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


def _shell_quote(s: str) -> str:
    """用單引號包裝 shell 引數，防止注入。"""
    return "'" + s.replace("'", "'\"'\"'") + "'"


def _sftp_isdir(sftp, path: str) -> bool:
    try:
        return stat.S_ISDIR(sftp.stat(path).st_mode)
    except (FileNotFoundError, OSError):
        return False


def _sftp_makedirs(sftp, path: str) -> None:
    """遞迴建立遠端目錄（模擬 mkdir -p）。"""
    # 正規化路徑，由根往下逐層建立
    parts: list[str] = []
    current = path
    while current and current != "/":
        parts.append(current)
        # 取 parent
        parent = current.rsplit("/", 1)[0] if "/" in current else ""
        if parent == current:
            break
        current = parent

    for dir_path in reversed(parts):
        try:
            sftp.stat(dir_path)
        except FileNotFoundError:
            sftp.mkdir(dir_path)


def _sftp_copytree(sftp, src: str, dst: str) -> None:
    """遞迴複製遠端目錄。"""
    _sftp_makedirs(sftp, dst)
    for item in sftp.listdir_attr(src):
        src_path = f"{src}/{item.filename}"
        dst_path = f"{dst}/{item.filename}"
        if stat.S_ISDIR(item.st_mode):
            _sftp_copytree(sftp, src_path, dst_path)
        else:
            with sftp.open(src_path, "rb") as sf:
                data = sf.read()
            with sftp.open(dst_path, "wb") as df:
                df.write(data)


def _sftp_rmtree(sftp, path: str) -> None:
    """遞迴刪除遠端目錄（深度優先）。"""
    for item in sftp.listdir_attr(path):
        item_path = f"{path}/{item.filename}"
        if stat.S_ISDIR(item.st_mode):
            _sftp_rmtree(sftp, item_path)
        else:
            sftp.remove(item_path)
    sftp.rmdir(path)
