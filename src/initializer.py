"""初始化器 — 六步驟系統初始化邏輯 (ADR-003)。

步驟：建立目錄 → 產生設定檔 → 儲存金鑰 → 啟動服務 →
      等待 Gateway → 設定語音轉文字。
"""

import shutil
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

from src import config_manager

# ── 常數 ──

STEP_KEYS = [
    "create_dirs", "generate_config", "store_keys",
    "start_service", "wait_gateway", "configure_stt",
]

SERVICE_START_TIMEOUT = 120   # Docker Compose 啟動逾時（秒）
SYSTEMCTL_TIMEOUT = 30        # systemctl 啟動逾時（秒）
GATEWAY_POLL_TIMEOUT = 60     # Gateway 就緒輪詢逾時（秒）
GATEWAY_POLL_INTERVAL = 2     # 輪詢間隔（秒）


# ── 資料結構 ──


@dataclass
class StepResult:
    """單一初始化步驟的執行結果。"""
    step: int
    key: str
    status: str   # "done" | "error" | "skipped"
    message: str


# ── 各步驟實作 ──


def _step_create_dirs(project_root: Path) -> StepResult:
    """步驟 1：建立必要的目錄結構。"""
    dirs = [
        project_root / ".openclaw",
        project_root / "agents" / "main" / "agent",
        project_root / "workspace" / "skills",
    ]
    try:
        for d in dirs:
            if d.exists() and not d.is_dir():
                d.unlink()
            d.mkdir(parents=True, exist_ok=True)
        return StepResult(1, "create_dirs", "done", f"已建立 {len(dirs)} 個目錄")
    except OSError as e:
        return StepResult(1, "create_dirs", "error", f"目錄建立失敗: {e}")


def _step_generate_config(project_root: Path, init_config: dict) -> StepResult:
    """步驟 2：產生或合併 openclaw.json 設定檔。"""
    try:
        config_patch = {
            "gateway": {
                "mode": init_config.get("gatewayMode", "local"),
                "bind": "custom",
                "customBindHost": init_config.get("bindHost", "0.0.0.0"),
                "port": init_config.get("gatewayPort", 18789),
            },
        }
        config_manager.merge_config(project_root, config_patch)
        return StepResult(2, "generate_config", "done", "設定檔已產生")
    except Exception as e:
        return StepResult(2, "generate_config", "error", f"設定檔產生失敗: {e}")


def _step_store_keys(secrets: dict[str, str]) -> StepResult:
    """步驟 3：將 API 金鑰儲存至系統 keyring。"""
    try:
        results = config_manager.store_secrets(secrets)
        failed = [k for k, ok in results.items() if not ok]
        if failed:
            return StepResult(3, "store_keys", "error", f"金鑰儲存失敗: {', '.join(failed)}")
        stored = sum(1 for ok in results.values() if ok)
        return StepResult(3, "store_keys", "done", f"已儲存 {stored} 組金鑰")
    except Exception as e:
        return StepResult(3, "store_keys", "error", f"金鑰儲存失敗: {e}")


def _run_service_cmd(cmd: list[str], cwd: Path, timeout: int) -> str | None:
    """執行服務啟動指令，回傳錯誤訊息或 None（成功）。"""
    result = subprocess.run(
        cmd, cwd=str(cwd), capture_output=True, text=True, timeout=timeout,
    )
    if result.returncode != 0:
        return result.stderr.strip() or result.stdout.strip()
    return None


def _step_start_service(project_root: Path, deploy_mode: str) -> StepResult:
    """步驟 4：透過 docker compose 或 systemctl 啟動服務。"""
    try:
        if deploy_mode in ("docker_windows", "docker_linux"):
            docker = shutil.which("docker")
            if not docker:
                return StepResult(4, "start_service", "error", "Docker 未安裝或不在 PATH 中")
            err = _run_service_cmd(
                [docker, "compose", "up", "-d"], project_root, SERVICE_START_TIMEOUT,
            )
            if err:
                return StepResult(4, "start_service", "error", f"Docker Compose 啟動失敗: {err}")
            return StepResult(4, "start_service", "done", "Docker 服務已啟動")

        if deploy_mode == "native_linux":
            systemctl = shutil.which("systemctl")
            if not systemctl:
                return StepResult(4, "start_service", "error", "systemctl 不可用")
            err = _run_service_cmd(
                [systemctl, "start", "openclaw-gateway"], project_root, SYSTEMCTL_TIMEOUT,
            )
            if err:
                return StepResult(4, "start_service", "error", f"服務啟動失敗: {err}")
            return StepResult(4, "start_service", "done", "openclaw-gateway 服務已啟動")

        return StepResult(4, "start_service", "error", f"不支援的部署模式: {deploy_mode}")

    except subprocess.TimeoutExpired:
        return StepResult(4, "start_service", "error", "服務啟動逾時")
    except Exception as e:
        return StepResult(4, "start_service", "error", f"服務啟動失敗: {e}")


def _step_wait_gateway(port: int) -> StepResult:
    """步驟 5：輪詢 Gateway 健康端點直到回應或逾時。"""
    url = f"http://127.0.0.1:{port}"
    start = time.time()

    while time.time() - start < GATEWAY_POLL_TIMEOUT:
        try:
            urllib.request.urlopen(url, timeout=3)
            elapsed = round(time.time() - start, 1)
            return StepResult(5, "wait_gateway", "done", f"Gateway 已就緒 ({elapsed}s)")
        except (urllib.error.URLError, OSError):
            time.sleep(GATEWAY_POLL_INTERVAL)

    return StepResult(
        5, "wait_gateway", "error",
        f"Gateway 在 {GATEWAY_POLL_TIMEOUT} 秒內未回應 (port {port})",
    )


def _step_configure_stt(project_root: Path) -> StepResult:
    """步驟 6：若有 OpenAI API Key 則設定語音轉文字。"""
    if not config_manager.get_secret("openai_api_key"):
        return StepResult(6, "configure_stt", "skipped", "未設定 OpenAI API Key，跳過 STT 設定")

    try:
        config_manager.merge_config(project_root, {
            "stt": {"provider": "openai", "model": "whisper-1"},
        })
        return StepResult(6, "configure_stt", "done", "語音轉文字已設定 (whisper-1)")
    except Exception as e:
        return StepResult(6, "configure_stt", "error", f"STT 設定失敗: {e}")


# ── 主流程 ──


def run_init(
    project_root: Path,
    init_config: dict,
    secrets: dict[str, str],
    on_step_update: Callable[[dict], None] | None = None,
) -> dict:
    """依序執行全部 6 個初始化步驟。

    每步驟前推送 status=running，完成後推送 status=done/error/skipped。
    遇到錯誤立即中止。
    """
    deploy_mode = init_config.get("deployMode", "docker_windows")
    gateway_port = init_config.get("gatewayPort", 18789)

    steps = [
        lambda: _step_create_dirs(project_root),
        lambda: _step_generate_config(project_root, init_config),
        lambda: _step_store_keys(secrets),
        lambda: _step_start_service(project_root, deploy_mode),
        lambda: _step_wait_gateway(gateway_port),
        lambda: _step_configure_stt(project_root),
    ]

    for i, step_fn in enumerate(steps):
        step_num = i + 1
        step_key = STEP_KEYS[i]

        if on_step_update:
            on_step_update({"step": step_num, "key": step_key, "status": "running", "message": ""})

        result = step_fn()

        if on_step_update:
            on_step_update(asdict(result))

        if result.status == "error":
            return {
                "success": False,
                "dashboard_url": None,
                "access_token": None,
                "failed_step": step_num,
                "error": result.message,
            }

    # 讀回設定以取得 dashboard 資訊
    config = config_manager.read_config(project_root)
    gateway = config.get("gateway", {})

    return {
        "success": True,
        "dashboard_url": f"http://127.0.0.1:{gateway.get('port', gateway_port)}",
        "access_token": gateway.get("auth", {}).get("token"),
        "failed_step": None,
        "error": None,
    }
