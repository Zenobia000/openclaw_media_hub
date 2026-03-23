"""Config Manager - settings and key management via keyring."""

import json
from pathlib import Path

import keyring
import keyring.errors

KEYRING_SERVICE = "openclaw-gui"
CONFIG_FILENAME = "openclaw.json"


# ── Secret operations ──


def store_secret(key: str, value: str) -> bool:
    """Store a secret in the system keyring."""
    try:
        keyring.set_password(KEYRING_SERVICE, key, value)
        return True
    except keyring.errors.NoKeyringError:
        return False
    except Exception:
        return False


def get_secret(key: str) -> str | None:
    """Retrieve a secret from the system keyring."""
    try:
        return keyring.get_password(KEYRING_SERVICE, key)
    except keyring.errors.NoKeyringError:
        return None
    except Exception:
        return None


def delete_secret(key: str) -> bool:
    """Delete a secret from the system keyring."""
    try:
        keyring.delete_password(KEYRING_SERVICE, key)
        return True
    except keyring.errors.PasswordDeleteError:
        return False
    except keyring.errors.NoKeyringError:
        return False
    except Exception:
        return False


def store_secrets(secrets: dict[str, str]) -> dict[str, bool]:
    """Store multiple secrets, skipping empty values."""
    results = {}
    for key, value in secrets.items():
        if value:
            results[key] = store_secret(key, value)
        else:
            results[key] = True  # skip empty, not an error
    return results


# ── Config file operations ──


def get_config_path(project_root: Path) -> Path:
    """Return path to openclaw.json inside .openclaw directory."""
    return project_root / ".openclaw" / CONFIG_FILENAME


def read_config(project_root: Path) -> dict:
    """Read openclaw.json, return empty dict if missing."""
    config_path = get_config_path(project_root)
    if not config_path.exists():
        return {}
    try:
        return json.loads(config_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def write_config(project_root: Path, data: dict) -> None:
    """Write data to openclaw.json, creating directories as needed."""
    config_path = get_config_path(project_root)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _deep_merge(base: dict, patch: dict) -> dict:
    """Recursively merge patch into base, returning a new dict."""
    result = base.copy()
    for key, value in patch.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def merge_config(project_root: Path, patch: dict) -> dict:
    """Read existing config, deep-merge patch, write back, return merged."""
    existing = read_config(project_root)
    merged = _deep_merge(existing, patch)
    write_config(project_root, merged)
    return merged


# ── Defaults ──


def get_defaults_for_mode(deploy_mode: str) -> dict:
    """Return sensible default config values for a deployment mode."""
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
