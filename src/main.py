"""OpenClaw GUI - PyWebView entry point."""

import webview
from pathlib import Path


def main():
    frontend_dir = Path(__file__).parent / "frontend"
    window = webview.create_window(
        "OpenClaw GUI",
        url=str(frontend_dir / "index.html"),
        width=1024,
        height=768,
    )
    webview.start()


if __name__ == "__main__":
    main()
