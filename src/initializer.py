"""Initializer - 6-step system initialization logic (ADR-003).

Steps: create dirs → generate config → store keys → start service →
       wait gateway → configure STT.
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


@dataclass
class StepResult:
    step: int
    key: str
    status: str  # "done" | "error" | "skipped"
    message: str


STEP_KEYS = [
    "create_dirs",
    "generate_config",
    "store_keys",
    "start_service",
    "wait_gateway",
    "configure_stt",
]


def step_create_directories(project_root: Path) -> StepResult:
    """Create required directory structure under project root."""
    dirs = [
        project_root / ".openclaw",
        project_root / "agents" / "main" / "agent",
        project_root / "workspace" / "skills",
    ]
    try:
        for d in dirs:
            # If path exists as a file, remove it first
            if d.exists() and not d.is_dir():
                d.unlink()
            d.mkdir(parents=True, exist_ok=True)
        return StepResult(1, "create_dirs", "done", f"已建立 {len(dirs)} 個目錄")
    except OSError as e:
        return StepResult(1, "create_dirs", "error", f"目錄建立失敗: {e}")


def step_generate_config(project_root: Path, init_config: dict) -> StepResult:
    """Generate or merge openclaw.json config."""
    try:
        bind_host = init_config.get("bindHost", "0.0.0.0")
        gateway_mode = init_config.get("gatewayMode", "local")
        gateway_port = init_config.get("gatewayPort", 18789)

        config_patch = {
            "gateway": {
                "mode": gateway_mode,
                "bind": "custom",
                "customBindHost": bind_host,
                "port": gateway_port,
            },
        }
        config_manager.merge_config(project_root, config_patch)
        return StepResult(2, "generate_config", "done", "設定檔已產生")
    except Exception as e:
        return StepResult(2, "generate_config", "error", f"設定檔產生失敗: {e}")


def step_store_keys(secrets: dict[str, str]) -> StepResult:
    """Store API keys and tokens in system keyring."""
    try:
        results = config_manager.store_secrets(secrets)
        stored = sum(1 for v in results.values() if v)
        failed = [k for k, v in results.items() if not v]
        if failed:
            return StepResult(
                3, "store_keys", "error",
                f"金鑰儲存失敗: {', '.join(failed)}"
            )
        return StepResult(3, "store_keys", "done", f"已儲存 {stored} 組金鑰")
    except Exception as e:
        return StepResult(3, "store_keys", "error", f"金鑰儲存失敗: {e}")


def step_start_service(project_root: Path, deploy_mode: str) -> StepResult:
    """Start the service via docker compose or systemctl."""
    try:
        if deploy_mode in ("docker_windows", "docker_linux"):
            docker = shutil.which("docker")
            if not docker:
                return StepResult(
                    4, "start_service", "error", "Docker 未安裝或不在 PATH 中"
                )
            result = subprocess.run(
                [docker, "compose", "up", "-d"],
                cwd=str(project_root),
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode != 0:
                msg = result.stderr.strip() or result.stdout.strip()
                return StepResult(
                    4, "start_service", "error", f"Docker Compose 啟動失敗: {msg}"
                )
            return StepResult(4, "start_service", "done", "Docker 服務已啟動")

        elif deploy_mode == "native_linux":
            systemctl = shutil.which("systemctl")
            if not systemctl:
                return StepResult(
                    4, "start_service", "error", "systemctl 不可用"
                )
            result = subprocess.run(
                [systemctl, "start", "openclaw-gateway"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                msg = result.stderr.strip() or result.stdout.strip()
                return StepResult(
                    4, "start_service", "error", f"服務啟動失敗: {msg}"
                )
            return StepResult(4, "start_service", "done", "openclaw-gateway 服務已啟動")

        return StepResult(4, "start_service", "error", f"不支援的部署模式: {deploy_mode}")

    except subprocess.TimeoutExpired:
        return StepResult(4, "start_service", "error", "服務啟動逾時")
    except Exception as e:
        return StepResult(4, "start_service", "error", f"服務啟動失敗: {e}")


def step_wait_gateway(port: int, timeout: int = 60) -> StepResult:
    """Poll gateway health endpoint until it responds or timeout."""
    url = f"http://127.0.0.1:{port}"
    start = time.time()
    while time.time() - start < timeout:
        try:
            urllib.request.urlopen(url, timeout=3)
            elapsed = round(time.time() - start, 1)
            return StepResult(
                5, "wait_gateway", "done", f"Gateway 已就緒 ({elapsed}s)"
            )
        except (urllib.error.URLError, OSError):
            time.sleep(2)

    return StepResult(
        5, "wait_gateway", "error",
        f"Gateway 在 {timeout} 秒內未回應 (port {port})"
    )


def step_configure_stt(project_root: Path) -> StepResult:
    """Configure speech-to-text if OpenAI API key is available."""
    openai_key = config_manager.get_secret("openai_api_key")
    if not openai_key:
        return StepResult(6, "configure_stt", "skipped", "未設定 OpenAI API Key，跳過 STT 設定")

    try:
        stt_patch = {
            "stt": {
                "provider": "openai",
                "model": "whisper-1",
            },
        }
        config_manager.merge_config(project_root, stt_patch)
        return StepResult(6, "configure_stt", "done", "語音轉文字已設定 (whisper-1)")
    except Exception as e:
        return StepResult(6, "configure_stt", "error", f"STT 設定失敗: {e}")


def run_init(
    project_root: Path,
    init_config: dict,
    secrets: dict[str, str],
    on_step_update: Callable[[dict], None] | None = None,
) -> dict:
    """Run all 6 initialization steps in sequence.

    Calls on_step_update before each step (status=running) and after
    (status=done/error/skipped). Stops on first error.

    Returns:
        {"success": True/False, "dashboard_url": ..., "access_token": ...,
         "failed_step": ..., "error": ...}
    """
    deploy_mode = init_config.get("deployMode", "docker_windows")
    gateway_port = init_config.get("gatewayPort", 18789)

    steps = [
        lambda: step_create_directories(project_root),
        lambda: step_generate_config(project_root, init_config),
        lambda: step_store_keys(secrets),
        lambda: step_start_service(project_root, deploy_mode),
        lambda: step_wait_gateway(gateway_port),
        lambda: step_configure_stt(project_root),
    ]

    for i, step_fn in enumerate(steps):
        step_num = i + 1
        step_key = STEP_KEYS[i]

        # Notify: running
        if on_step_update:
            on_step_update({
                "step": step_num,
                "key": step_key,
                "status": "running",
                "message": "",
            })

        result = step_fn()

        # Notify: result
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

    # Read back config for dashboard info
    config = config_manager.read_config(project_root)
    port = config.get("gateway", {}).get("port", gateway_port)
    token = config.get("gateway", {}).get("auth", {}).get("token")

    return {
        "success": True,
        "dashboard_url": f"http://127.0.0.1:{port}",
        "access_token": token,
        "failed_step": None,
        "error": None,
    }
