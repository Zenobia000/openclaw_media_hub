"""設定管理器 — 設定檔讀寫與金鑰安全儲存（keyring 整合）。"""

import json
from pathlib import Path

import keyring
import keyring.errors

KEYRING_SERVICE = "openclaw-gui"
CONFIG_FILENAME = "openclaw.json"


# ── 金鑰操作 ──


def _keyring_op(fn, default=None):
    """執行 keyring 操作，失敗時回傳預設值。"""
    try:
        return fn()
    except (keyring.errors.NoKeyringError, keyring.errors.KeyringError, Exception):
        return default


def store_secret(key: str, value: str) -> bool:
    """將金鑰儲存至系統 keyring。"""
    return _keyring_op(lambda: (keyring.set_password(KEYRING_SERVICE, key, value), True)[1], False)


def get_secret(key: str) -> str | None:
    """從系統 keyring 取得金鑰。"""
    return _keyring_op(lambda: keyring.get_password(KEYRING_SERVICE, key))


def delete_secret(key: str) -> bool:
    """從系統 keyring 刪除金鑰。"""
    return _keyring_op(lambda: (keyring.delete_password(KEYRING_SERVICE, key), True)[1], False)


def store_secrets(secrets: dict[str, str]) -> dict[str, bool]:
    """批次儲存金鑰，空值視為跳過（不算失敗）。"""
    return {
        key: store_secret(key, value) if value else True
        for key, value in secrets.items()
    }


# ── 設定檔操作 ──


def get_config_path(project_root: Path) -> Path:
    """取得 .openclaw/openclaw.json 路徑。"""
    return project_root / ".openclaw" / CONFIG_FILENAME


def read_config(project_root: Path) -> dict:
    """讀取 openclaw.json，不存在或格式錯誤時回傳空字典。"""
    config_path = get_config_path(project_root)
    if not config_path.exists():
        return {}
    try:
        return json.loads(config_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def write_config(project_root: Path, data: dict) -> None:
    """寫入 openclaw.json，自動建立父目錄。"""
    config_path = get_config_path(project_root)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _deep_merge(base: dict, patch: dict) -> dict:
    """遞迴合併 patch 至 base，回傳新字典。"""
    result = base.copy()
    for key, value in patch.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def merge_config(project_root: Path, patch: dict) -> dict:
    """讀取設定、深層合併、寫回並回傳合併結果。"""
    merged = _deep_merge(read_config(project_root), patch)
    write_config(project_root, merged)
    return merged


# ── 預設值 ──


def get_defaults_for_mode(deploy_mode: str) -> dict:
    """依部署模式回傳合理的預設設定。"""
    base = {
        "gateway": {
            "mode": "local",
            "bind": "custom",
            "customBindHost": "0.0.0.0",
        },
    }
    if deploy_mode == "native_linux":
        base["gateway"]["customBindHost"] = "127.0.0.1"
    return base
