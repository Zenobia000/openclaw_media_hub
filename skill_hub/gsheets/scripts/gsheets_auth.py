#!/usr/bin/env python3
"""Google Sheets 認證模組。

統一處理 OAuth2 Desktop App 與 Service Account 兩種認證方式，
供 gsheets_setup.py、gsheets_append.py、gsheets_query.py、gsheets_update.py 共用。

與 gmail_auth.py 同模式：scopes 由呼叫端傳入，不硬編碼。
"""

import json
import os
import sys


DEFAULT_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def load_credentials(credentials_path: str, token_path: str | None = None, scopes: list[str] | None = None):
    """載入 Google API 認證，自動偵測 OAuth2 Desktop 或 Service Account。"""
    if not scopes:
        scopes = DEFAULT_SCOPES

    with open(credentials_path, "r") as f:
        cred_data = json.load(f)

    if "installed" in cred_data or "web" in cred_data:
        return _load_oauth2(credentials_path, token_path, scopes)
    return _load_service_account(credentials_path, scopes)


def _load_oauth2(credentials_path: str, token_path: str | None, scopes: list[str]):
    """載入 OAuth2 Desktop App 認證。"""
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
    except ImportError:
        _exit("google-auth-oauthlib 未安裝。執行: pip install google-auth-oauthlib google-api-python-client")

    creds = None
    if token_path and os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, scopes)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            _exit("Token 不存在或無效。請先執行 gsheets_setup.py 完成 OAuth2 授權。")

        if token_path:
            with open(token_path, "w") as f:
                f.write(creds.to_json())
            print(f"Token 已刷新並儲存至 {token_path}", file=sys.stderr)

    return creds


def _load_service_account(credentials_path: str, scopes: list[str]):
    """載入 Service Account 認證。"""
    try:
        from google.oauth2 import service_account
    except ImportError:
        _exit("google-auth 未安裝。執行: pip install google-auth")
    return service_account.Credentials.from_service_account_file(
        credentials_path, scopes=scopes
    )


def _exit(message: str):
    """輸出錯誤訊息並結束程式。"""
    print(f"錯誤：{message}", file=sys.stderr)
    sys.exit(1)
