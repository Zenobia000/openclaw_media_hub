"""平台工具 — 作業系統偵測與跨平台輔助函式。"""

import platform
import shutil
from enum import Enum
from pathlib import Path


class OSType(Enum):
    WINDOWS = "windows"
    LINUX = "linux"


class EnvType(Enum):
    DOCKER = "docker"
    NATIVE = "native"


def detect_os() -> OSType:
    """偵測當前作業系統。"""
    return OSType.WINDOWS if platform.system() == "Windows" else OSType.LINUX


def detect_env_type() -> EnvType:
    """偵測環境類型（Docker 可用則視為 Docker 環境）。"""
    return EnvType.DOCKER if shutil.which("docker") else EnvType.NATIVE


def get_project_root() -> Path:
    """取得專案根目錄路徑。"""
    return Path(__file__).resolve().parent.parent
