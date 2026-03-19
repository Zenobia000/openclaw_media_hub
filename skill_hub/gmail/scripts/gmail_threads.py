#!/usr/bin/env python3
"""Gmail 對話串操作（列出/取得）。

用法：
    # 列出對話串
    python3 gmail_threads.py --credentials credentials.json --token token.json \
        --action list --max-results 10 --query "is:unread"

    # 取得單一對話串（含所有郵件）
    python3 gmail_threads.py --credentials credentials.json --token token.json \
        --action get --thread-id "thread_abc123"

    # 分頁
    python3 gmail_threads.py --credentials credentials.json --token token.json \
        --action list --page-token "TOKEN_FROM_PREVIOUS"

    # Dry-run 模式
    python3 gmail_threads.py --dry-run --credentials credentials.json --token token.json \
        --action list

輸出：JSON 格式（stdout），錯誤訊息輸出至 stderr。
"""

import argparse
import base64
import json
import sys


def _parse_headers(headers: list[dict]) -> dict:
    """從 MIME headers 中提取常用欄位。"""
    result = {}
    target_headers = {"From", "To", "Subject", "Date", "Cc"}
    for h in headers:
        if h["name"] in target_headers:
            result[h["name"].lower()] = h["value"]
    return result


def _extract_body(payload: dict, truncate: int) -> str:
    """遍歷 MIME parts，提取 text/plain 內容並截斷。"""
    body_text = ""

    if payload.get("mimeType", "").startswith("text/plain"):
        data = payload.get("body", {}).get("data", "")
        if data:
            body_text = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    parts = payload.get("parts", [])
    for part in parts:
        mime = part.get("mimeType", "")
        if mime == "text/plain":
            data = part.get("body", {}).get("data", "")
            if data:
                body_text = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                break
        elif mime.startswith("multipart/"):
            nested = _extract_body(part, truncate)
            if nested:
                body_text = nested
                break

    if truncate and len(body_text) > truncate:
        body_text = body_text[:truncate] + "…"

    return body_text.strip()


def _parse_message(msg: dict, truncate: int) -> dict:
    """解析對話串中單封郵件的 headers 與 body。"""
    payload = msg.get("payload", {})
    headers = _parse_headers(payload.get("headers", []))

    return {
        "message_id": msg["id"],
        "snippet": msg.get("snippet", ""),
        "from": headers.get("from", ""),
        "to": headers.get("to", ""),
        "cc": headers.get("cc", ""),
        "subject": headers.get("subject", ""),
        "date": headers.get("date", ""),
        "body_snippet": _extract_body(payload, truncate),
        "label_ids": msg.get("labelIds", []),
    }


def manage_threads(credentials_path: str, token_path: str, scopes: list[str],
                   action: str, thread_id: str | None,
                   max_results: int, query: str | None,
                   page_token: str | None, fmt: str, truncate: int) -> dict:
    """執行對話串操作。"""
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
        if action == "list":
            kwargs = {"userId": "me", "maxResults": max_results}
            if query:
                kwargs["q"] = query
            if page_token:
                kwargs["pageToken"] = page_token

            response = service.users().threads().list(**kwargs).execute()
            threads = response.get("threads", [])

            result = {
                "ok": True,
                "query": query or "(all)",
                "total_results": len(threads),
                "threads": [
                    {"thread_id": t["id"], "snippet": t.get("snippet", "")}
                    for t in threads
                ],
            }

            next_page_token = response.get("nextPageToken")
            if next_page_token:
                result["next_page_token"] = next_page_token

            return result

        if action == "get":
            if not thread_id:
                return {"ok": False, "error": "get 動作需要 --thread-id 參數。"}

            kwargs = {"userId": "me", "id": thread_id, "format": fmt}
            thread = service.users().threads().get(**kwargs).execute()
            messages = thread.get("messages", [])

            return {
                "ok": True,
                "thread_id": thread["id"],
                "total_messages": len(messages),
                "messages": [_parse_message(m, truncate) for m in messages],
            }

        return {"ok": False, "error": f"未知動作：{action}"}
    except Exception as e:
        return {"ok": False, "error": f"對話串操作失敗：{e}"}


def main():
    parser = argparse.ArgumentParser(description="Gmail 對話串操作")
    parser.add_argument("--credentials", required=True, help="OAuth2 client secret JSON 路徑")
    parser.add_argument("--token", default="token.json", help="Token 路徑")
    parser.add_argument("--scopes", default=None, help="Gmail API scopes（逗號分隔）")
    parser.add_argument("--action", required=True, choices=["list", "get"],
                        help="動作：list（列出對話串）| get（取得對話串詳情）")
    parser.add_argument("--thread-id", default=None, help="Gmail thread ID（get 動作必要）")
    parser.add_argument("--max-results", type=int, default=20, help="最多回傳幾筆（預設 20）")
    parser.add_argument("--query", default=None, help="Gmail 查詢條件")
    parser.add_argument("--page-token", default=None, help="分頁 token")
    parser.add_argument("--format", default="full", choices=["full", "metadata"],
                        help="回傳格式（get 動作用）：full | metadata")
    parser.add_argument("--truncate", type=int, default=500, help="每封郵件內文截斷字數（預設 500）")
    parser.add_argument("--dry-run", action="store_true", help="不呼叫 API，僅驗證參數")
    args = parser.parse_args()

    scopes = [s.strip() for s in args.scopes.split(",") if s.strip()] if args.scopes else None

    if args.dry_run:
        result = {
            "ok": True,
            "dry_run": True,
            "credentials": args.credentials,
            "token": args.token,
            "scopes": scopes or ["https://www.googleapis.com/auth/gmail.modify"],
            "action": args.action,
            "thread_id": args.thread_id,
            "max_results": args.max_results,
            "query": args.query,
            "page_token": args.page_token,
            "format": args.format,
            "truncate": args.truncate,
        }
    else:
        result = manage_threads(args.credentials, args.token, scopes,
                                args.action, args.thread_id,
                                args.max_results, args.query,
                                args.page_token, args.format, args.truncate)

    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result.get("ok") else 1)


if __name__ == "__main__":
    main()
