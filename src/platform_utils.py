"""Platform Utils — 跨平台偵測與工具函式。

偵測作業系統類型（Windows / Linux）與執行環境（Docker / Native），
供上層模組選擇對應的操作邏輯分支。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PlatformInfo:
    """平台偵測結果。"""

    os_name: str  # "windows" | "linux" | "darwin"
    is_docker: bool
    deployment_mode: str  # "docker-windows" | "docker-linux" | "native-linux" | "remote-ssh"


def detect_platform() -> PlatformInfo:
    """偵測當前平台與執行環境，回傳 PlatformInfo。"""
    raise NotImplementedError
