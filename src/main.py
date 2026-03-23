"""OpenClaw GUI — PyWebView 入口點。"""

import webview
from pathlib import Path

from src.bridge import Bridge


def main():
    frontend_dir = Path(__file__).parent / "frontend"
    bridge = Bridge()
    window = webview.create_window(
        "OpenClaw GUI",
        url=str(frontend_dir / "index.html"),
        js_api=bridge,
        width=1280,
        height=800,
        min_size=(1024, 600),
    )
    bridge.set_window(window)
    webview.start(debug=True)


if __name__ == "__main__":
    main()
