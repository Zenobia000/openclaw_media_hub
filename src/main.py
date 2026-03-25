"""OpenClaw GUI — PyWebView 入口點。

建立桌面視窗，載入前端 UI，註冊 Bridge API。
"""

from __future__ import annotations

from pathlib import Path

import webview

from src.bridge import Bridge


def main() -> None:
    """啟動 OpenClaw GUI 應用程式。"""
    bridge = Bridge()
    frontend_path = Path(__file__).parent / "frontend" / "index.html"

    webview.create_window(
        title="OpenClaw",
        url=str(frontend_path),
        js_api=bridge,
        width=1280,
        height=800,
        resizable=False,
    )
    webview.start(debug=True)


if __name__ == "__main__":
    main()
