"""OpenClaw GUI — PyWebView 入口點。

建立桌面視窗，載入前端 UI，註冊 Bridge API。
"""

from __future__ import annotations

from pathlib import Path

import webview

from src.bridge import Bridge


def _on_started(bridge: Bridge, window: webview.Window) -> None:
    """視窗啟動後注入 window 實例至 Bridge。"""
    bridge.set_window(window)


def main() -> None:
    """啟動 OpenClaw GUI 應用程式。"""
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
    webview.start(lambda: _on_started(bridge, window), debug=True)


if __name__ == "__main__":
    main()
