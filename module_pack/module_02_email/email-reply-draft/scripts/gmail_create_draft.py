#!/usr/bin/env python3
"""建立 Gmail 草稿。

用法：
    python3 gmail_create_draft.py \
        --credentials credentials.json \
        --token token.json \
        --scopes "https://www.googleapis.com/auth/gmail.readonly,https://www.googleapis.com/auth/gmail.compose" \
        --to "wang@example.com" \
        --subject "Re: 請問網站設計方案報價" \
        --body "王先生您好，感謝您的來信詢問..." \
        --in-reply-to "<original-message-id@mail.gmail.com>" \
        --thread-id "thread_abc123"

    # Dry-run 模式
    python3 gmail_create_draft.py --dry-run \
        --credentials credentials.json --token token.json \
        --to "wang@example.com" --subject "Re: Test" --body "Hello"

輸出：JSON 格式（stdout），錯誤訊息輸出至 stderr。
"""

import argparse
import base64
import json
import sys
from email.mime.text import MIMEText


def create_draft(credentials_path: str, token_path: str, scopes: list[str],
                 to: str, subject: str, body: str,
                 in_reply_to: str | None = None, thread_id: str | None = None,
                 cc: str | None = None, bcc: str | None = None) -> dict:
    """建立 Gmail 草稿。"""
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

    # 構建 MIME 訊息
    message = MIMEText(body, "plain", "utf-8")
    message["To"] = to
    message["Subject"] = subject

    if cc:
        message["Cc"] = cc
    if bcc:
        message["Bcc"] = bcc
    if in_reply_to:
        message["In-Reply-To"] = in_reply_to
        message["References"] = in_reply_to

    # base64url 編碼
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

    # 構建 draft body
    draft_body = {"message": {"raw": raw}}
    if thread_id:
        draft_body["message"]["threadId"] = thread_id

    try:
        draft = service.users().drafts().create(
            userId="me", body=draft_body
        ).execute()

        return {
            "ok": True,
            "draft_id": draft["id"],
            "message": "Draft 已存入 Gmail 草稿匣。",
        }
    except Exception as e:
        return {"ok": False, "error": f"無法建立草稿：{e}"}


def main():
    parser = argparse.ArgumentParser(description="建立 Gmail 草稿")
    parser.add_argument("--credentials", required=True, help="OAuth2 client secret JSON 路徑")
    parser.add_argument("--token", default="token.json", help="Token 路徑")
    parser.add_argument("--scopes", default=None, help="Gmail API scopes（逗號分隔）")
    parser.add_argument("--to", required=True, help="收件人 email")
    parser.add_argument("--subject", required=True, help="郵件主旨")
    parser.add_argument("--body", required=True, help="郵件內文")
    parser.add_argument("--in-reply-to", default=None, help="原信的 Message-ID header（確保執行緒正確）")
    parser.add_argument("--thread-id", default=None, help="Gmail thread ID（確保執行緒正確）")
    parser.add_argument("--cc", default=None, help="CC 收件人（逗號分隔）")
    parser.add_argument("--bcc", default=None, help="BCC 收件人（逗號分隔）")
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
                "https://www.googleapis.com/auth/gmail.readonly",
                "https://www.googleapis.com/auth/gmail.compose",
            ],
            "to": args.to,
            "subject": args.subject,
            "body_length": len(args.body),
            "in_reply_to": args.in_reply_to,
            "thread_id": args.thread_id,
            "cc": args.cc,
            "bcc": args.bcc,
        }
    else:
        result = create_draft(args.credentials, args.token, scopes,
                              args.to, args.subject, args.body,
                              args.in_reply_to, args.thread_id,
                              args.cc, args.bcc)

    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result.get("ok") else 1)


if __name__ == "__main__":
    main()
