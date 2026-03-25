"""TransferService — 跨本機/遠端檔案傳輸 (ADR-004).

用於技能部署場景：將本機 module_pack/ 目錄上傳至遠端 skills/ 目錄，
或反向下載。透過 Executor 介面操作，不直接依賴 paramiko。
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol, runtime_checkable

from src.executor import Executor


@runtime_checkable
class ProgressCallback(Protocol):
    """傳輸進度回呼。"""

    def __call__(self, current: int, total: int, filename: str) -> None: ...


class TransferService:
    """跨機器檔案傳輸服務。

    接收 source executor（讀取端）與 target executor（寫入端），
    支援任意方向的目錄樹傳輸。
    """

    def __init__(self, source: Executor, target: Executor) -> None:
        self._source = source
        self._target = target

    async def upload_tree(
        self,
        local_src: str,
        remote_dst: str,
        on_progress: ProgressCallback | None = None,
    ) -> int:
        """上傳目錄樹：source → target。

        Args:
            local_src: 來源路徑（source executor 上的目錄）。
            remote_dst: 目標路徑（target executor 上的目錄）。
            on_progress: 進度回呼 (current, total, filename)。

        Returns:
            傳輸的檔案數量。
        """
        files = await self._collect_files(self._source, local_src, "")
        total = len(files)

        await self._target.mkdir(remote_dst)

        for i, rel_path in enumerate(files, 1):
            src_full = f"{local_src}/{rel_path}"
            dst_full = f"{remote_dst}/{rel_path}"

            # 確保目標子目錄存在
            if "/" in rel_path:
                parent = dst_full.rsplit("/", 1)[0]
                await self._target.mkdir(parent)

            data = await self._source.read_file(src_full)
            await self._target.write_file(dst_full, data)

            if on_progress:
                on_progress(i, total, rel_path)

        return total

    async def download_tree(
        self,
        remote_src: str,
        local_dst: str,
        on_progress: ProgressCallback | None = None,
    ) -> int:
        """下載目錄樹：source → target（反向操作，source=remote, target=local）。

        注意：此方法假設 self._source 為遠端，self._target 為本機。
        若需反向，請在建構時調換 source/target。
        """
        files = await self._collect_files(self._source, remote_src, "")
        total = len(files)

        await self._target.mkdir(local_dst)

        for i, rel_path in enumerate(files, 1):
            src_full = f"{remote_src}/{rel_path}"
            dst_full = f"{local_dst}/{rel_path}"

            if "/" in rel_path:
                parent = dst_full.rsplit("/", 1)[0]
                await self._target.mkdir(parent)

            data = await self._source.read_file(src_full)
            await self._target.write_file(dst_full, data)

            if on_progress:
                on_progress(i, total, rel_path)

        return total

    async def _collect_files(
        self,
        executor: Executor,
        base: str,
        prefix: str,
    ) -> list[str]:
        """遞迴收集目錄下的所有檔案相對路徑。"""
        result: list[str] = []
        entries = await executor.list_dir(base)

        for name in entries:
            full = f"{base}/{name}"
            rel = f"{prefix}/{name}" if prefix else name

            # 嘗試 list_dir 判斷是否為目錄
            try:
                sub_files = await self._collect_files(executor, full, rel)
                result.extend(sub_files)
            except (OSError, PermissionError, NotADirectoryError):
                result.append(rel)

        return result
