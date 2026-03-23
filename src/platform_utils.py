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


_SCRIPT_MAP = {
    (OSType.WINDOWS, EnvType.DOCKER): ("docker", ".ps1"),
    (OSType.LINUX, EnvType.DOCKER): ("docker", ".sh"),
    (OSType.LINUX, EnvType.NATIVE): ("native", ".sh"),
}


def resolve_script(script_base: str, os_type: OSType, env_type: EnvType) -> Path:
    key = (os_type, env_type)
    if key not in _SCRIPT_MAP:
        raise ValueError(f"Unsupported platform: {os_type.value}/{env_type.value}")
    suffix_label, ext = _SCRIPT_MAP[key]
    filename = f"{script_base}-{suffix_label}{ext}"
    return get_project_root() / "scripts" / filename


def build_command(script_path: Path) -> list[str]:
    ext = script_path.suffix.lower()
    path_str = str(script_path)
    if ext == ".ps1":
        return ["powershell", "-ExecutionPolicy", "Bypass", "-File", path_str]
    return ["bash", path_str]
