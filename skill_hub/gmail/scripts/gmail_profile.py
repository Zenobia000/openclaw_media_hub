#!/usr/bin/env python3
"""取得 Gmail 個人資料。

用法：
    python3 gmail_profile.py \
        --credentials credentials.json \
        --token token.json

    # Dry-run 模式
    python3 gmail_profile.py --dry-run \
        --credentials credentials.json --token token.json

輸出：JSON 格式（stdout），錯誤訊息輸出至 stderr。
"""

import argparse
import json
import sys


def get_profile(credentials_path: str, token_path: str, scopes: list[str]) -> dict:
    """取得 Gmail 個人資料。"""
    try:
        from gmail_auth import load_credentials
    except ImportError:
        sys.path.insert(0, __import__("os").path.dirname(__file__))
        from gmail_auth import load_credentials

    try:
        from googleapiclient.discovery import build
    except ImportError:
        return {"ok": False, "error": "google-api-python-client 未安裝。"}

    creds = load_credentials(credentials_path, token_path, scopes)
    service = build("gmail", "v1", credentials=creds)

    try:
        profile = service.users().getProfile(userId="me").execute()
        return {
            "ok": True,
            "email_address": profile.get("emailAddress", ""),
            "messages_total": profile.get("messagesTotal", 0),
            "threads_total": profile.get("threadsTotal", 0),
            "history_id": profile.get("historyId", ""),
        }
    except Exception as e:
        return {"ok": False, "error": f"無法取得個人資料：{e}"}


def main():
    parser = argparse.ArgumentParser(description="取得 Gmail 個人資料")
    parser.add_argument("--credentials", required=True, help="OAuth2 client secret JSON 路徑")
    parser.add_argument("--token", default="token.json", help="Token 路徑")
    parser.add_argument("--scopes", default=None, help="Gmail API scopes（逗號分隔）")
    parser.add_argument("--dry-run", action="store_true", help="不呼叫 API，僅驗證參數")
    args = parser.parse_args()

    scopes = [s.strip() for s in args.scopes.split(",") if s.strip()] if args.scopes else None

    if args.dry_run:
        result = {
            "ok": True,
            "dry_run": True,
            "credentials": args.credentials,
            "token": args.token,
            "scopes": scopes or [
                "https://www.googleapis.com/auth/gmail.modify",
            ],
        }
    else:
        result = get_profile(args.credentials, args.token, scopes)

    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result.get("ok") else 1)


if __name__ == "__main__":
    main()
