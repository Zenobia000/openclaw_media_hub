#!/usr/bin/env python3
"""Google Calendar OAuth2 初始化腳本。

用法：
    python3 gcal_setup.py --credentials client_secret.json --token token.json --step auth-url
    python3 gcal_setup.py --credentials client_secret.json --token token.json --step exchange --code "CODE"
    python3 gcal_setup.py --credentials client_secret.json --token token.json --step verify --calendar-id primary

輸出：JSON（stdout），錯誤訊息至 stderr。
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gcal_auth import DEFAULT_SCOPES

REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"


# --- 共用工具 ---

def _parse_scopes(scopes_str: str | None) -> list[str]:
    """解析逗號分隔的 scopes 字串，回傳 list。"""
    if not scopes_str:
        return DEFAULT_SCOPES
    return [s.strip() for s in scopes_str.split(",") if s.strip()]


def _create_flow(credentials_path: str, scopes: list[str]):
    """建立 OAuth2 Flow，含檔案存在檢查。回傳 (flow, error_dict)。"""
    from google_auth_oauthlib.flow import InstalledAppFlow

    if not os.path.exists(credentials_path):
        return None, {"ok": False, "error": f"找不到認證檔案：{credentials_path}"}

    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, scopes)
    flow.redirect_uri = REDIRECT_URI
    return flow, None


def _verifier_path(token_path: str) -> str:
    """PKCE code_verifier 暫存檔路徑。"""
    return token_path + ".verifier"


# --- 步驟函數 ---

def step_auth_url(credentials_path: str, token_path: str, scopes: list[str]) -> dict:
    """產生 OAuth2 授權網址，儲存 PKCE code_verifier。"""
    flow, err = _create_flow(credentials_path, scopes)
    if err:
        return err

    auth_url, state = flow.authorization_url(prompt="consent", access_type="offline")

    # 儲存 code_verifier 供 exchange 使用
    with open(_verifier_path(token_path), "w") as f:
        json.dump({"code_verifier": getattr(flow, "code_verifier", "") or "", "state": state}, f)

    return {
        "ok": True,
        "step": "auth-url",
        "auth_url": auth_url,
        "instructions": "請在瀏覽器開啟上方網址，完成 Google 帳號授權後，複製授權碼。",
    }


def step_exchange(credentials_path: str, token_path: str, code: str, scopes: list[str]) -> dict:
    """用授權碼換取 token 並儲存。"""
    flow, err = _create_flow(credentials_path, scopes)
    if err:
        return err

    # 還原 PKCE code_verifier
    vpath = _verifier_path(token_path)
    if os.path.exists(vpath):
        with open(vpath, "r") as f:
            flow.code_verifier = json.load(f).get("code_verifier", "")

    try:
        flow.fetch_token(code=code)
    except Exception as e:
        return {"ok": False, "error": f"授權碼無效或已過期：{e}"}

    with open(token_path, "w") as f:
        f.write(flow.credentials.to_json())

    # 清理暫存檔
    if os.path.exists(vpath):
        os.remove(vpath)

    return {"ok": True, "step": "exchange", "token_path": token_path, "message": "Token 已成功儲存。"}


def step_verify(credentials_path: str, token_path: str, calendar_id: str, scopes: list[str]) -> dict:
    """驗證 token 有效性，讀取行事曆資訊。"""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    if not os.path.exists(token_path):
        return {"ok": False, "error": f"找不到 token 檔案：{token_path}。請先完成授權步驟。"}

    creds = Credentials.from_authorized_user_file(token_path, scopes)

    # 自動刷新過期 token
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            with open(token_path, "w") as f:
                f.write(creds.to_json())
        except Exception as e:
            return {"ok": False, "error": f"Token 刷新失敗：{e}"}

    if not creds.valid:
        return {"ok": False, "error": "Token 無效，請重新授權。"}

    try:
        cal = build("calendar", "v3", credentials=creds).calendars().get(calendarId=calendar_id).execute()
        return {
            "ok": True,
            "step": "verify",
            "calendar_summary": cal.get("summary", ""),
            "calendar_timezone": cal.get("timeZone", ""),
            "message": f"認證成功！已連接行事曆：{cal.get('summary', calendar_id)}",
        }
    except Exception as e:
        return {"ok": False, "error": f"無法存取行事曆：{e}"}


# --- 主程式 ---

def main():
    parser = argparse.ArgumentParser(description="Google Calendar OAuth2 初始化")
    parser.add_argument("--credentials", required=True, help="OAuth2 client secret JSON 路徑")
    parser.add_argument("--token", default="token.json", help="Token 儲存路徑")
    parser.add_argument("--scopes", default=None, help="OAuth2 scopes（逗號分隔，預設 calendar）")
    parser.add_argument("--step", required=True, choices=["auth-url", "exchange", "verify"],
                        help="執行步驟：auth-url | exchange | verify")
    parser.add_argument("--code", default="", help="授權碼（exchange 用）")
    parser.add_argument("--calendar-id", default="primary", help="驗證用行事曆 ID")
    args = parser.parse_args()

    scopes = _parse_scopes(args.scopes)

    if args.step == "auth-url":
        result = step_auth_url(args.credentials, args.token, scopes)
    elif args.step == "exchange":
        if not args.code:
            result = {"ok": False, "error": "exchange 步驟需要 --code 參數。"}
        else:
            result = step_exchange(args.credentials, args.token, args.code, scopes)
    elif args.step == "verify":
        result = step_verify(args.credentials, args.token, args.calendar_id, scopes)
    else:
        result = {"ok": False, "error": f"未知步驟：{args.step}"}

    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result.get("ok") else 1)


if __name__ == "__main__":
    main()
