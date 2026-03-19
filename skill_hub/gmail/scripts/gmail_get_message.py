#!/usr/bin/env python3
"""取得單封 Gmail 郵件詳情。

用法：
    python3 gmail_get_message.py \
        --credentials credentials.json \
        --token token.json \
        --message-id "abc123"

    # 指定格式與標頭
    python3 gmail_get_message.py \
        --credentials credentials.json --token token.json \
        --message-id "abc123" --format metadata \
        --metadata-headers "From,Subject,Date"

    # Dry-run 模式
    python3 gmail_get_message.py --dry-run \
        --credentials credentials.json --token token.json --message-id "abc123"

輸出：JSON 格式（stdout），錯誤訊息輸出至 stderr。
"""

import argparse
import base64
import json
import sys


def _parse_headers(headers: list[dict], target_names: set[str] | None = None) -> dict:
    """從 MIME headers 中提取指定欄位。"""
    if target_names is None:
        target_names = {"From", "To", "Subject", "Date", "Cc", "Bcc", "In-Reply-To", "References"}
    result = {}
    for h in headers:
        if h["name"] in target_names:
            result[h["name"].lower()] = h["value"]
    return result


def _parse_from(from_str: str) -> tuple[str, str]:
    """解析 From 欄位，回傳 (name, email)。"""
    if "<" in from_str and ">" in from_str:
        name = from_str.split("<")[0].strip().strip('"')
        email = from_str.split("<")[1].split(">")[0].strip()
        return name, email
    return "", from_str.strip()


def _extract_body(payload: dict, truncate: int) -> str:
    """遍歷 MIME parts，提取 text/plain 內容並截斷。"""
    body_text = ""

    # 單一 part（無 multipart）
    if payload.get("mimeType", "").startswith("text/plain"):
        data = payload.get("body", {}).get("data", "")
        if data:
            body_text = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    # multipart 遍歷
    parts = payload.get("parts", [])
    for part in parts:
        mime = part.get("mimeType", "")
        if mime == "text/plain":
            data = part.get("body", {}).get("data", "")
            if data:
                body_text = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
                break
        elif mime.startswith("multipart/"):
            # 遞迴處理巢狀 multipart
            nested = _extract_body(part, truncate)
            if nested:
                body_text = nested
                break

    if truncate and len(body_text) > truncate:
        body_text = body_text[:truncate] + "…"

    return body_text.strip()


def get_message(credentials_path: str, token_path: str, scopes: list[str],
                message_id: str, truncate: int, fmt: str,
                metadata_headers: list[str] | None) -> dict:
    """取得單封 Gmail 郵件詳情。"""
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
        kwargs = {"userId": "me", "id": message_id, "format": fmt}
        if fmt == "metadata" and metadata_headers:
            kwargs["metadataHeaders"] = metadata_headers

        msg = service.users().messages().get(**kwargs).execute()

        # raw 格式直接回傳
        if fmt == "raw":
            return {
                "ok": True,
                "message_id": msg["id"],
                "thread_id": msg["threadId"],
                "snippet": msg.get("snippet", ""),
                "raw": msg.get("raw", ""),
                "label_ids": msg.get("labelIds", []),
            }

        payload = msg.get("payload", {})
        header_names = set(metadata_headers) if metadata_headers else None
        headers = _parse_headers(payload.get("headers", []), header_names)
        from_name, from_email = _parse_from(headers.get("from", ""))

        result = {
            "ok": True,
            "message_id": msg["id"],
            "thread_id": msg["threadId"],
            "snippet": msg.get("snippet", ""),
            "from": from_email,
            "from_name": from_name,
            "to": headers.get("to", ""),
            "subject": headers.get("subject", ""),
            "date": headers.get("date", ""),
            "label_ids": msg.get("labelIds", []),
        }

        # full 格式才解析 body
        if fmt == "full":
            result["body_snippet"] = _extract_body(payload, truncate)

        return result
    except Exception as e:
        return {"ok": False, "error": f"無法取得郵件 {message_id}：{e}"}


def main():
    parser = argparse.ArgumentParser(description="取得 Gmail 郵件詳情")
    parser.add_argument("--credentials", required=True, help="OAuth2 client secret JSON 路徑")
    parser.add_argument("--token", default="token.json", help="Token 路徑")
    parser.add_argument("--scopes", default=None, help="Gmail API scopes（逗號分隔）")
    parser.add_argument("--message-id", required=True, help="Gmail 郵件 ID")
    parser.add_argument("--truncate", type=int, default=500, help="內文截斷字數（預設 500）")
    parser.add_argument("--format", default="full", choices=["full", "metadata", "raw"],
                        help="回傳格式：full（完整）| metadata（僅標頭）| raw（原始 MIME）")
    parser.add_argument("--metadata-headers", default=None,
                        help="選擇性取得的標頭（逗號分隔），僅 metadata 格式有效")
    parser.add_argument("--dry-run", action="store_true", help="不呼叫 API，僅驗證參數")
    args = parser.parse_args()

    scopes = [s.strip() for s in args.scopes.split(",") if s.strip()] if args.scopes else None
    metadata_headers = [h.strip() for h in args.metadata_headers.split(",") if h.strip()] if args.metadata_headers else None

    if args.dry_run:
        result = {
            "ok": True,
            "dry_run": True,
            "credentials": args.credentials,
            "token": args.token,
            "scopes": scopes or ["https://www.googleapis.com/auth/gmail.modify"],
            "message_id": args.message_id,
            "truncate": args.truncate,
            "format": args.format,
            "metadata_headers": metadata_headers,
        }
    else:
        result = get_message(args.credentials, args.token, scopes,
                             args.message_id, args.truncate, args.format,
                             metadata_headers)

    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result.get("ok") else 1)


if __name__ == "__main__":
    main()
