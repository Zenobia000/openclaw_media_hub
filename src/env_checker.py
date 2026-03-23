"""環境檢查器 — 以 Python 原生偵測系統環境 (ADR-003)。

透過 shutil.which() 與 subprocess.run() 偵測必要軟體，
回傳結構化結果供前端渲染為狀態卡片。
"""

import re
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

from src.platform_utils import EnvType, OSType, detect_env_type, detect_os, get_project_root

# ── 資料結構 ──


@dataclass
class CheckResult:
    """單項檢查結果。"""
    name: str
    key: str
    installed: bool
    version: str
    message: str
    required: bool = True


# ── 工具檢查規格（宣告式） ──

@dataclass
class ToolSpec:
    """工具檢查規格：名稱、指令、版本參數、安裝提示。"""
    name: str
    key: str
    cmd: str
    version_args: list[str]
    install_hint: str
    required: bool = True
    min_major: int | None = None  # 最低主版本要求


# 所有工具的宣告式檢查規格
TOOL_SPECS: list[ToolSpec] = [
    ToolSpec("Docker", "docker", "docker",
             ["--version"], "Docker 未安裝。請安裝 Docker Desktop。"),
    ToolSpec("VS Code", "vscode", "code",
             ["--version"], "VS Code 未安裝。請至 https://code.visualstudio.com/ 下載安裝。"),
    ToolSpec("ngrok", "ngrok", "ngrok",
             ["version"], "ngrok 未安裝。請至 https://ngrok.com/download 下載安裝。"),
    ToolSpec("Node.js", "nodejs", "node",
             ["--version"], "Node.js 未安裝。請安裝 Node.js >= 18。",
             min_major=18),
    ToolSpec("openclaw CLI", "openclaw", "openclaw",
             ["--version"], "openclaw CLI 未安裝或不在 PATH 中。"),
    ToolSpec("jq", "jq", "jq",
             ["--version"], "jq 未安裝。請執行：sudo apt-get install -y jq"),
]


# ── 內部工具函式 ──


def _run_cmd(command: list[str], timeout: int = 10) -> str | None:
    """執行指令並回傳 stdout，失敗則回傳 None。

    透過 shutil.which() 解析執行檔路徑，
    確保 Windows 上的 .CMD/.BAT 包裝器能正確找到。
    """
    resolved = shutil.which(command[0])
    if resolved is None:
        return None
    try:
        result = subprocess.run(
            [resolved, *command[1:]],
            capture_output=True, text=True, timeout=timeout,
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None


def _extract_version(text: str, pattern: str = r"(\d+\.\d+[\.\d]*)") -> str:
    """從文字中以正規表達式擷取版本號。"""
    match = re.search(pattern, text)
    return match.group(1) if match else text.split("\n")[0]


# ── 通用工具檢查 ──


def _check_tool(spec: ToolSpec) -> CheckResult:
    """依照 ToolSpec 執行單項工具檢查。"""
    if not shutil.which(spec.cmd):
        return CheckResult(
            spec.name, spec.key, False, "", spec.install_hint, spec.required,
        )

    output = _run_cmd([spec.cmd, *spec.version_args])
    if output is None:
        return CheckResult(
            spec.name, spec.key, True, "",
            f"{spec.name} 已安裝但無法取得版本。", spec.required,
        )

    version = _extract_version(output.split("\n")[0])

    # 版本下限檢查
    if spec.min_major is not None:
        major = re.match(r"(\d+)", version)
        if major and int(major.group(1)) < spec.min_major:
            return CheckResult(
                spec.name, spec.key, True, version,
                f"{spec.name} {version} 版本過舊，建議升級至 >= {spec.min_major}。",
                spec.required,
            )

    return CheckResult(
        spec.name, spec.key, True, version,
        f"{spec.name} {version} 已安裝。", spec.required,
    )


# ── 特殊檢查（無法用通用模式處理） ──


def _check_docker_running() -> CheckResult:
    """檢查 Docker 引擎是否正在執行。"""
    if not shutil.which("docker"):
        return CheckResult(
            "Docker Desktop", "docker_running", False, "",
            "Docker 未安裝，無法檢查執行狀態。",
        )
    if _run_cmd(["docker", "info"]) is None:
        return CheckResult(
            "Docker Desktop", "docker_running", False, "",
            "Docker 未啟動，請開啟 Docker Desktop。",
        )
    return CheckResult(
        "Docker Desktop", "docker_running", True, "",
        "Docker 引擎運作中。",
    )


def _check_systemd_service() -> CheckResult:
    """檢查 openclaw-gateway systemd 服務狀態（僅限 Linux 原生環境）。"""
    service = "openclaw-gateway"

    if not shutil.which("systemctl"):
        return CheckResult(
            "systemd 服務", "systemd", False, "",
            "systemctl 不可用。", required=False,
        )

    output = _run_cmd(["systemctl", "is-active", service])
    if output is None:
        return CheckResult(
            "systemd 服務", "systemd", False, "",
            f"{service} 服務尚未設定（可稍後透過 init 建立）。", required=False,
        )

    state = output.strip()
    is_active = state == "active"
    msg = f"{service} 服務已設定且正在執行。" if is_active else f"{service} 服務狀態：{state}。"
    return CheckResult("systemd 服務", "systemd", is_active, "", msg, required=False)


def _check_env_file() -> CheckResult:
    """檢查 .env 檔案是否存在，必要時從 .env.example 複製。"""
    project_root = get_project_root()
    env_file = project_root / ".env"
    env_example = project_root / ".env.example"

    if env_file.exists():
        return CheckResult(".env 檔案", "env_file", True, "", ".env 檔案已存在。")

    if not env_example.exists():
        return CheckResult(
            ".env 檔案", "env_file", False, "",
            ".env.example 不存在，請手動建立 .env 檔案。",
        )

    try:
        shutil.copy2(env_example, env_file)
        return CheckResult(
            ".env 檔案", "env_file", True, "",
            "已從 .env.example 複製建立 .env。",
        )
    except OSError as e:
        return CheckResult(
            ".env 檔案", "env_file", False, "",
            f"複製 .env.example 失敗：{e}",
        )


# ── 檢查規格查詢 ──


def _get_spec(key: str) -> ToolSpec | None:
    """依 key 取得工具規格。"""
    return next((s for s in TOOL_SPECS if s.key == key), None)


# ── 環境檢查組合（依 OS 與環境類型） ──

# 各環境需檢查的工具 key 清單
_DOCKER_CHECKS = ["docker", "vscode", "ngrok"]
_NATIVE_CHECKS = ["nodejs", "openclaw", "jq", "vscode", "ngrok"]


def run_all_checks() -> list[dict]:
    """依偵測到的作業系統與環境類型執行所有檢查。"""
    os_type = detect_os()
    env_type = detect_env_type()

    results: list[CheckResult] = []

    if env_type == EnvType.DOCKER:
        for key in _DOCKER_CHECKS:
            spec = _get_spec(key)
            if spec:
                results.append(_check_tool(spec))
        results.append(_check_docker_running())
    else:
        for key in _NATIVE_CHECKS:
            spec = _get_spec(key)
            if spec:
                results.append(_check_tool(spec))
        if os_type == OSType.LINUX:
            results.append(_check_systemd_service())

    results.append(_check_env_file())
    return [asdict(r) for r in results]
