"""OpenClaw GUI — PyWebView 入口點。

建立桌面視窗，載入前端 UI，註冊 Bridge API。
"""

from __future__ import annotations

import os
from pathlib import Path

import webview

from src.bridge import Bridge


def _on_started(bridge: Bridge, window: webview.Window) -> None:
    """視窗啟動後注入 window 實例至 Bridge。"""
    bridge.set_window(window)


def _load_dotenv() -> None:
    """載入專案根目錄 .env 至 os.environ（不覆蓋已存在的變數）。"""
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if not env_file.exists():
        return
    from src.config_manager import ConfigManager

    for key, value in ConfigManager.parse_env_content(env_file.read_text("utf-8")).items():
        os.environ.setdefault(key, value)


def main() -> None:
    """啟動 OpenClaw GUI 應用程式。"""
    _load_dotenv()
    bridge = Bridge()
    frontend_path = Path(__file__).parent / "frontend" / "index.html"

    window = webview.create_window(
        title="OpenClaw",
        url=str(frontend_path),
        js_api=bridge,
        width=1280,
        height=800,
        resizable=False,
    )
    debug = os.environ.get("OPENCLAW_DEBUG", "1").lower() not in ("0", "false")
    webview.start(lambda: _on_started(bridge, window), debug=debug)


if __name__ == "__main__":
    main()
