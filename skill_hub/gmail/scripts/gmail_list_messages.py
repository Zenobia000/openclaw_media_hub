#!/usr/bin/env python3
"""列出 Gmail 郵件。

用法：
    python3 gmail_list_messages.py \
        --credentials credentials.json \
        --token token.json \
        --max-results 20 \
        --query "is:unread" \
        --time-range 24h

    # 篩選特定標籤
    python3 gmail_list_messages.py \
        --credentials credentials.json --token token.json \
        --label-ids "INBOX,UNREAD" --max-results 10

    # 分頁
    python3 gmail_list_messages.py \
        --credentials credentials.json --token token.json \
        --page-token "TOKEN_FROM_PREVIOUS_RESPONSE"

    # Dry-run 模式（不呼叫 API，僅驗證參數）
    python3 gmail_list_messages.py --dry-run \
        --credentials credentials.json --token token.json

輸出：JSON 格式（stdout），錯誤訊息輸出至 stderr。
"""

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone


def parse_time_range(time_range: str) -> str | None:
    """將時間範圍（如 24h、7d）轉為 Gmail query 的 after:YYYY/MM/DD 條件。"""
    now = datetime.now(timezone.utc)
    value = time_range.strip()

    if value.endswith("h"):
        hours = int(value[:-1])
        cutoff = now - timedelta(hours=hours)
    elif value.endswith("d"):
        days = int(value[:-1])
        cutoff = now - timedelta(days=days)
    else:
        return None

    return f"after:{cutoff.strftime('%Y/%m/%d')}"


def list_messages(credentials_path: str, token_path: str, scopes: list[str],
                  max_results: int, query: str, time_range: str | None,
                  label_ids: list[str] | None, page_token: str | None) -> dict:
    """列出符合條件的 Gmail 郵件。"""
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

    # 組合查詢條件
    q_parts = [query] if query else []
    if time_range:
        after_clause = parse_time_range(time_range)
        if after_clause:
            q_parts.append(after_clause)

    q = " ".join(q_parts) if q_parts else None

    try:
        kwargs = {"userId": "me", "maxResults": max_results}
        if q:
            kwargs["q"] = q
        if label_ids:
            kwargs["labelIds"] = label_ids
        if page_token:
            kwargs["pageToken"] = page_token

        response = service.users().messages().list(**kwargs).execute()
        messages = response.get("messages", [])

        results = [
            {"message_id": msg["id"], "thread_id": msg["threadId"]}
            for msg in messages
        ]

        result = {
            "ok": True,
            "query": q or "(all)",
            "total_results": len(results),
            "messages": results,
        }

        # 分頁 token
        next_page_token = response.get("nextPageToken")
        if next_page_token:
            result["next_page_token"] = next_page_token

        return result
    except Exception as e:
        return {"ok": False, "error": f"無法列出郵件：{e}"}


def main():
    parser = argparse.ArgumentParser(description="列出 Gmail 郵件")
    parser.add_argument("--credentials", required=True, help="OAuth2 client secret JSON 路徑")
    parser.add_argument("--token", default="token.json", help="Token 路徑")
    parser.add_argument("--scopes", default=None, help="Gmail API scopes（逗號分隔）")
    parser.add_argument("--max-results", type=int, default=20, help="最多回傳幾封（預設 20）")
    parser.add_argument("--query", default="", help="Gmail 查詢條件（預設空字串，全部郵件）")
    parser.add_argument("--time-range", default=None, help="往回查看的時間範圍（如 24h、7d）")
    parser.add_argument("--label-ids", default=None, help="篩選標籤 ID（逗號分隔），例如 INBOX,UNREAD")
    parser.add_argument("--page-token", default=None, help="分頁 token（從前次回應取得）")
    parser.add_argument("--dry-run", action="store_true", help="不呼叫 API，僅驗證參數")
    args = parser.parse_args()

    scopes = [s.strip() for s in args.scopes.split(",") if s.strip()] if args.scopes else None
    label_ids = [l.strip() for l in args.label_ids.split(",") if l.strip()] if args.label_ids else None

    if args.dry_run:
        after_clause = parse_time_range(args.time_range) if args.time_range else None
        q_parts = [args.query] if args.query else []
        if after_clause:
            q_parts.append(after_clause)
        result = {
            "ok": True,
            "dry_run": True,
            "credentials": args.credentials,
            "token": args.token,
            "scopes": scopes or ["https://www.googleapis.com/auth/gmail.modify"],
            "max_results": args.max_results,
            "query": " ".join(q_parts) if q_parts else "(all)",
            "time_range": args.time_range,
            "label_ids": label_ids,
            "page_token": args.page_token,
        }
    else:
        result = list_messages(args.credentials, args.token, scopes,
                               args.max_results, args.query, args.time_range,
                               label_ids, args.page_token)

    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result.get("ok") else 1)


if __name__ == "__main__":
    main()
