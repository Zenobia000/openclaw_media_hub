#!/usr/bin/env python3
"""Google Calendar 認證模組。

統一處理 OAuth2 Desktop App 與 Service Account 兩種認證方式，
供 gcal_freebusy.py 與 gcal_create_event.py 共用。
"""

import json
import os
import sys

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def load_credentials(credentials_path: str, token_path: str | None = None):
    """載入 Google API 認證，自動偵測 OAuth2 Desktop 或 Service Account。"""
    with open(credentials_path, "r") as f:
        cred_data = json.load(f)

    if "installed" in cred_data or "web" in cred_data:
        return _load_oauth2(credentials_path, token_path)
    return _load_service_account(credentials_path)


def _load_oauth2(credentials_path: str, token_path: str | None):
    """載入 OAuth2 Desktop App 認證，首次需瀏覽器授權。"""
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
    except ImportError:
        _exit("google-auth-oauthlib 未安裝。執行: pip install google-auth-oauthlib google-api-python-client")

    creds = None
    if token_path and os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            creds = _run_auth_flow(credentials_path)

        if token_path:
            with open(token_path, "w") as f:
                f.write(creds.to_json())
            print(f"Token 已儲存至 {token_path}", file=sys.stderr)

    return creds


def _run_auth_flow(credentials_path: str):
    """執行 OAuth2 授權流程（優先本地伺服器，備援手動貼網址）。"""
    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)

    # 嘗試本地伺服器授權
    if os.environ.get("DISPLAY") or os.environ.get("BROWSER"):
        try:
            creds = flow.run_local_server(port=0, open_browser=False)
            if getattr(creds, "token", None):
                return creds
        except Exception:
            pass

    # 備援：手動貼網址
    flow.redirect_uri = "http://localhost:1"
    auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")
    print(f"\n{'='*60}", file=sys.stderr)
    print("請在瀏覽器開啟以下網址進行 Google 授權：", file=sys.stderr)
    print(f"\n{auth_url}\n", file=sys.stderr)
    print("授權後瀏覽器會跳轉到無法載入的頁面，", file=sys.stderr)
    print("請複製該頁面完整網址（http://localhost:1 開頭）貼到這裡：", file=sys.stderr)
    print(f"{'='*60}\n", file=sys.stderr)
    redirect_response = input("貼上完整網址: ").strip()
    flow.fetch_token(authorization_response=redirect_response)
    return flow.credentials


def _load_service_account(credentials_path: str):
    """載入 Service Account 認證。"""
    try:
        from google.oauth2 import service_account
    except ImportError:
        _exit("google-auth 未安裝。執行: pip install google-auth")
    return service_account.Credentials.from_service_account_file(
        credentials_path, scopes=SCOPES
    )


def _exit(message: str):
    """輸出錯誤訊息並結束程式。"""
    print(f"錯誤：{message}", file=sys.stderr)
    sys.exit(1)
