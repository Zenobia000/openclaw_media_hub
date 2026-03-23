"""Platform Utils - OS detection and cross-platform utilities."""

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
    system = platform.system()
    if system == "Windows":
        return OSType.WINDOWS
    return OSType.LINUX


def detect_env_type() -> EnvType:
    if shutil.which("docker"):
        return EnvType.DOCKER
    return EnvType.NATIVE


def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent
