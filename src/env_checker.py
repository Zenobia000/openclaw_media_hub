"""Env Checker - Python native environment detection (ADR-003).

Detects required software via shutil.which() and subprocess.run(),
returns structured results for the frontend to render as status cards.
"""

import shutil
import subprocess
import re
from dataclasses import dataclass, asdict
from pathlib import Path

from src.platform_utils import EnvType, OSType, detect_env_type, detect_os, get_project_root


@dataclass
class CheckResult:
    name: str
    installed: bool
    version: str
    message: str
    required: bool = True


def _run_version(command: list[str], timeout: int = 10) -> str | None:
    """Run a command and return stdout, or None on failure.

    Resolves the executable via shutil.which() so that .CMD/.BAT wrappers
    on Windows are found correctly by subprocess.
    """
    try:
        resolved = shutil.which(command[0])
        if resolved is None:
            return None
        cmd = [resolved] + command[1:]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None


def _extract_version(text: str, pattern: str = r"(\d+\.\d+[\.\d]*)") -> str:
    """Extract version number from text using regex."""
    match = re.search(pattern, text)
    return match.group(1) if match else text.split("\n")[0]


def check_docker() -> CheckResult:
    """Check Docker installation and running status."""
    if not shutil.which("docker"):
        return CheckResult(
            name="Docker",
            installed=False,
            version="",
            message="Docker 未安裝。請安裝 Docker Desktop。",
        )

    output = _run_version(["docker", "--version"])
    if output is None:
        return CheckResult(
            name="Docker",
            installed=False,
            version="",
            message="Docker 指令執行失敗。",
        )

    version = _extract_version(output)

    # Check if Docker daemon is running
    info = _run_version(["docker", "info"])
    if info is None:
        return CheckResult(
            name="Docker",
            installed=True,
            version=version,
            message=f"Docker {version} 已安裝但未啟動，請開啟 Docker Desktop。",
        )

    return CheckResult(
        name="Docker",
        installed=True,
        version=version,
        message=f"Docker {version} 已安裝且正在執行。",
    )


def check_vscode() -> CheckResult:
    """Check VS Code installation."""
    if not shutil.which("code"):
        return CheckResult(
            name="VS Code",
            installed=False,
            version="",
            message="VS Code 未安裝。請至 https://code.visualstudio.com/ 下載安裝。",
        )

    output = _run_version(["code", "--version"])
    if output is None:
        return CheckResult(
            name="VS Code",
            installed=True,
            version="",
            message="VS Code 已安裝但無法取得版本。",
        )

    # code --version returns version on first line
    first_line = output.split("\n")[0]
    version = _extract_version(first_line)

    return CheckResult(
        name="VS Code",
        installed=True,
        version=version,
        message=f"VS Code {version} 已安裝。",
    )


def check_ngrok() -> CheckResult:
    """Check ngrok installation."""
    if not shutil.which("ngrok"):
        return CheckResult(
            name="ngrok",
            installed=False,
            version="",
            message="ngrok 未安裝。請至 https://ngrok.com/download 下載安裝。",
        )

    output = _run_version(["ngrok", "version"])
    if output is None:
        return CheckResult(
            name="ngrok",
            installed=True,
            version="",
            message="ngrok 已安裝但無法取得版本。",
        )

    version = _extract_version(output)
    return CheckResult(
        name="ngrok",
        installed=True,
        version=version,
        message=f"ngrok {version} 已安裝。",
    )


def check_nodejs() -> CheckResult:
    """Check Node.js installation (native env, requires >= 18)."""
    if not shutil.which("node"):
        return CheckResult(
            name="Node.js",
            installed=False,
            version="",
            message="Node.js 未安裝。請安裝 Node.js >= 18。",
        )

    output = _run_version(["node", "--version"])
    if output is None:
        return CheckResult(
            name="Node.js",
            installed=True,
            version="",
            message="Node.js 已安裝但無法取得版本。",
        )

    version = _extract_version(output)
    major_match = re.match(r"(\d+)", version)
    if major_match and int(major_match.group(1)) < 18:
        return CheckResult(
            name="Node.js",
            installed=True,
            version=version,
            message=f"Node.js {version} 版本過舊，建議升級至 >= 18。",
        )

    return CheckResult(
        name="Node.js",
        installed=True,
        version=version,
        message=f"Node.js {version} 已安裝。",
    )


def check_openclaw_cli() -> CheckResult:
    """Check openclaw CLI installation (native env)."""
    if not shutil.which("openclaw"):
        return CheckResult(
            name="openclaw CLI",
            installed=False,
            version="",
            message="openclaw CLI 未安裝或不在 PATH 中。",
        )

    output = _run_version(["openclaw", "--version"])
    version = _extract_version(output) if output else ""

    return CheckResult(
        name="openclaw CLI",
        installed=True,
        version=version,
        message=f"openclaw CLI {version} 已安裝。" if version else "openclaw CLI 已安裝。",
    )


def check_jq() -> CheckResult:
    """Check jq installation (native env)."""
    if not shutil.which("jq"):
        return CheckResult(
            name="jq",
            installed=False,
            version="",
            message="jq 未安裝。請執行：sudo apt-get install -y jq",
        )

    output = _run_version(["jq", "--version"])
    version = _extract_version(output) if output else ""

    return CheckResult(
        name="jq",
        installed=True,
        version=version,
        message=f"jq {version} 已安裝。" if version else "jq 已安裝。",
    )


def check_systemd_service() -> CheckResult:
    """Check openclaw-gateway systemd service (native Linux env)."""
    service_name = "openclaw-gateway"

    if not shutil.which("systemctl"):
        return CheckResult(
            name="systemd 服務",
            installed=False,
            version="",
            message="systemctl 不可用。",
            required=False,
        )

    result = _run_version(["systemctl", "is-active", service_name])
    if result is None:
        return CheckResult(
            name="systemd 服務",
            installed=False,
            version="",
            message=f"{service_name} 服務尚未設定（可稍後透過 init 建立）。",
            required=False,
        )

    state = result.strip()
    if state == "active":
        return CheckResult(
            name="systemd 服務",
            installed=True,
            version="",
            message=f"{service_name} 服務已設定且正在執行。",
            required=False,
        )

    return CheckResult(
        name="systemd 服務",
        installed=True,
        version="",
        message=f"{service_name} 服務狀態：{state}。",
        required=False,
    )


def check_env_file() -> CheckResult:
    """Check if .env file exists, copy from .env.example if needed."""
    project_root = get_project_root()
    env_file = project_root / ".env"
    env_example = project_root / ".env.example"

    if env_file.exists():
        return CheckResult(
            name=".env 檔案",
            installed=True,
            version="",
            message=".env 檔案已存在。",
        )

    if env_example.exists():
        try:
            shutil.copy2(env_example, env_file)
            return CheckResult(
                name=".env 檔案",
                installed=True,
                version="",
                message="已從 .env.example 複製建立 .env。",
            )
        except OSError as e:
            return CheckResult(
                name=".env 檔案",
                installed=False,
                version="",
                message=f"複製 .env.example 失敗：{e}",
            )

    return CheckResult(
        name=".env 檔案",
        installed=False,
        version="",
        message=".env.example 不存在，請手動建立 .env 檔案。",
    )


def run_all_checks() -> list[dict]:
    """Run all environment checks based on detected OS and environment type.

    Returns a list of structured check results.
    """
    os_type = detect_os()
    env_type = detect_env_type()

    results: list[CheckResult] = []

    if env_type == EnvType.DOCKER:
        # Docker environment: Docker, VS Code, ngrok, .env
        results.append(check_docker())
        results.append(check_vscode())
        results.append(check_ngrok())
    else:
        # Native environment: Node.js, openclaw CLI, jq, VS Code, ngrok
        results.append(check_nodejs())
        results.append(check_openclaw_cli())
        results.append(check_jq())
        results.append(check_vscode())
        results.append(check_ngrok())
        if os_type == OSType.LINUX:
            results.append(check_systemd_service())

    results.append(check_env_file())

    return [asdict(r) for r in results]
