"""Bridge API — PyWebView 前端 Bridge 類別。

所有 public method 自動暴露為 window.pywebview.api.* 供前端呼叫。
回傳格式統一: {"success": True/False, "data": ..., "error": ...}
"""

from __future__ import annotations


class Bridge:
    """PyWebView Bridge API。

    每個 public method 都會成為前端可呼叫的 JavaScript API。
    回傳值由 PyWebView 自動序列化為 JSON。
    """

    def ping(self) -> dict:
        """連線測試，前端用來確認 Bridge 可用。"""
        return {"success": True, "data": {"message": "pong"}, "error": None}
