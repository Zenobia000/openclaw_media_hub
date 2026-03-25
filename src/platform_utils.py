"""Platform Utils — 跨平台偵測與工具函式。

偵測作業系統類型（Windows / Linux）與執行環境（Docker / Native），
供上層模組選擇對應的操作邏輯分支。
"""

from __future__ import annotations

import platform
import shutil
from dataclasses import dataclass
from pathlib import Path

# 支援的部署模式
DEPLOY_DOCKER_WINDOWS = "docker-windows"
DEPLOY_DOCKER_LINUX = "docker-linux"
DEPLOY_NATIVE_LINUX = "native-linux"
DEPLOY_REMOTE_SSH = "remote-ssh"


@dataclass(frozen=True, slots=True)
class PlatformInfo:
    """平台偵測結果。"""

    os_name: str  # "windows" | "linux" | "darwin"
    is_docker: bool
    deployment_mode: str  # suggested mode based on detection


def _detect_os() -> str:
    """回傳正規化的 OS 名稱。"""
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    if system == "linux":
        return "linux"
    if system == "darwin":
        return "darwin"
    return system


def _has_docker() -> bool:
    """檢查 Docker CLI 是否可用。"""
    return shutil.which("docker") is not None


def _is_native_linux() -> bool:
    """檢查是否為 Native Linux（有 systemctl 且非 Docker-in-Docker）。"""
    if _detect_os() != "linux":
        return False
    # 有 systemctl 且不在容器內（/.dockerenv 不存在）
    has_systemctl = shutil.which("systemctl") is not None
    in_container = Path("/.dockerenv").exists()
    return has_systemctl and not in_container


def suggest_deployment_mode(os_name: str, has_docker: bool) -> str:
    """根據 OS 與環境推薦部署模式。"""
    if os_name == "windows":
        return DEPLOY_DOCKER_WINDOWS if has_docker else DEPLOY_DOCKER_WINDOWS
    if os_name == "linux":
        if _is_native_linux():
            return DEPLOY_NATIVE_LINUX
        return DEPLOY_DOCKER_LINUX if has_docker else DEPLOY_NATIVE_LINUX
    # darwin 或其他：預設 Docker
    return DEPLOY_DOCKER_LINUX if has_docker else DEPLOY_NATIVE_LINUX


def detect_platform() -> PlatformInfo:
    """偵測當前平台與執行環境，回傳 PlatformInfo。"""
    os_name = _detect_os()
    has_docker = _has_docker()
    mode = suggest_deployment_mode(os_name, has_docker)

    return PlatformInfo(
        os_name=os_name,
        is_docker=has_docker,
        deployment_mode=mode,
    )
