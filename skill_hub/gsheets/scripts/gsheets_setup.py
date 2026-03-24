#!/usr/bin/env python3
"""Google Sheets OAuth2 初始化腳本。

用法：
    # 步驟 1：產生授權網址
    python3 gsheets_setup.py --credentials client_secret.json --token token.json --step auth-url

    # 步驟 2：用授權碼換取 token
    python3 gsheets_setup.py --credentials client_secret.json --token token.json --step exchange --code "AUTHORIZATION_CODE"

    # 驗證：測試 token 是否有效
    python3 gsheets_setup.py --credentials client_secret.json --token token.json --step verify --spreadsheet-id SPREADSHEET_ID

輸出：JSON 格式（stdout），錯誤訊息輸出至 stderr。
"""

import argparse
import json
import os
import sys


SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def step_auth_url(credentials_path: str, token_path: str) -> dict:
    """產生 OAuth2 授權網址，回傳 JSON。儲存 PKCE code_verifier 供 exchange 使用。"""
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        return {"ok": False, "error": "google-auth-oauthlib 未安裝。執行: pip install google-auth-oauthlib google-api-python-client"}

    if not os.path.exists(credentials_path):
        return {"ok": False, "error": f"找不到認證檔案：{credentials_path}"}

    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
    flow.redirect_uri = "urn:ietf:wg:oauth:2.0:oob"
    auth_url, state = flow.authorization_url(prompt="consent", access_type="offline")

    # 儲存 code_verifier 供 exchange 步驟使用
    verifier_path = token_path + ".verifier"
    verifier = getattr(flow, "code_verifier", None) or ""
    with open(verifier_path, "w") as f:
        json.dump({"code_verifier": verifier, "state": state}, f)

    return {
        "ok": True,
        "step": "auth-url",
        "auth_url": auth_url,
        "instructions": "請在瀏覽器開啟上方網址，完成 Google 帳號授權後，複製授權碼（authorization code）。",
    }


def step_exchange(credentials_path: str, token_path: str, code: str) -> dict:
    """用授權碼換取 token 並儲存。"""
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        return {"ok": False, "error": "google-auth-oauthlib 未安裝。"}

    if not os.path.exists(credentials_path):
        return {"ok": False, "error": f"找不到認證檔案：{credentials_path}"}

    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
    flow.redirect_uri = "urn:ietf:wg:oauth:2.0:oob"

    # 還原 PKCE code_verifier
    verifier_path = token_path + ".verifier"
    if os.path.exists(verifier_path):
        with open(verifier_path, "r") as f:
            saved = json.load(f)
        flow.code_verifier = saved.get("code_verifier", "")

    try:
        flow.fetch_token(code=code)
    except Exception as e:
        return {"ok": False, "error": f"授權碼無效或已過期：{e}"}

    creds = flow.credentials
    with open(token_path, "w") as f:
        f.write(creds.to_json())

    # 清理 verifier 暫存檔
    if os.path.exists(verifier_path):
        os.remove(verifier_path)

    return {
        "ok": True,
        "step": "exchange",
        "token_path": token_path,
        "message": "Token 已成功儲存。",
    }


def step_verify(credentials_path: str, token_path: str, spreadsheet_id: str) -> dict:
    """驗證 token 是否有效，嘗試讀取試算表資訊。"""
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
    except ImportError:
        return {"ok": False, "error": "google-api-python-client 未安裝。"}

    if not os.path.exists(token_path):
        return {"ok": False, "error": f"找不到 token 檔案：{token_path}。請先完成 auth-url 與 exchange 步驟。"}

    creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            with open(token_path, "w") as f:
                f.write(creds.to_json())
        except Exception as e:
            return {"ok": False, "error": f"Token 刷新失敗：{e}"}

    if not creds.valid:
        return {"ok": False, "error": "Token 無效，請重新執行授權流程。"}

    try:
        service = build("sheets", "v4", credentials=creds)
        spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        title = spreadsheet.get("properties", {}).get("title", "")
        sheets = [s["properties"]["title"] for s in spreadsheet.get("sheets", [])]
        return {
            "ok": True,
            "step": "verify",
            "spreadsheet_title": title,
            "sheets": sheets,
            "message": f"認證成功！已連接試算表：{title}",
        }
    except Exception as e:
        return {"ok": False, "error": f"無法存取試算表：{e}"}


def main():
    parser = argparse.ArgumentParser(description="Google Sheets OAuth2 初始化")
    parser.add_argument("--credentials", required=True, help="OAuth2 client secret JSON 路徑")
    parser.add_argument("--token", default="token.json", help="Token 儲存路徑")
    parser.add_argument("--step", required=True, choices=["auth-url", "exchange", "verify"],
                        help="執行步驟：auth-url（產生授權網址）| exchange（換取 token）| verify（驗證連線）")
    parser.add_argument("--code", default="", help="授權碼（exchange 步驟用）")
    parser.add_argument("--spreadsheet-id", default="", help="驗證用試算表 ID")
    args = parser.parse_args()

    if args.step == "auth-url":
        result = step_auth_url(args.credentials, args.token)
    elif args.step == "exchange":
        if not args.code:
            result = {"ok": False, "error": "exchange 步驟需要 --code 參數。"}
        else:
            result = step_exchange(args.credentials, args.token, args.code)
    elif args.step == "verify":
        if not args.spreadsheet_id:
            result = {"ok": False, "error": "verify 步驟需要 --spreadsheet-id 參數。"}
        else:
            result = step_verify(args.credentials, args.token, args.spreadsheet_id)
    else:
        result = {"ok": False, "error": f"未知步驟：{args.step}"}

    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result.get("ok") else 1)


if __name__ == "__main__":
    main()
