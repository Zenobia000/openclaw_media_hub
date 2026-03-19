#!/usr/bin/env python3
"""撰寫並寄送 Gmail 郵件。

用法：
    python3 gmail_send_message.py \
        --credentials credentials.json \
        --token token.json \
        --to "recipient@example.com" \
        --subject "會議通知" \
        --body "您好，提醒明天下午的會議。"

    # 回覆郵件（指定 thread）
    python3 gmail_send_message.py \
        --credentials credentials.json --token token.json \
        --to "recipient@example.com" \
        --subject "Re: 原始主旨" \
        --body "回覆內容" \
        --in-reply-to "<original-message-id@mail.gmail.com>" \
        --references "<original-message-id@mail.gmail.com>" \
        --thread-id "thread_abc123"

    # Dry-run 模式
    python3 gmail_send_message.py --dry-run \
        --credentials credentials.json --token token.json \
        --to "test@example.com" --subject "Test" --body "Hello"

輸出：JSON 格式（stdout），錯誤訊息輸出至 stderr。
"""

import argparse
import base64
import json
import sys
from email.mime.text import MIMEText


def send_message(credentials_path: str, token_path: str, scopes: list[str],
                 to: str, subject: str, body: str,
                 cc: str | None = None, bcc: str | None = None,
                 in_reply_to: str | None = None, references: str | None = None,
                 thread_id: str | None = None) -> dict:
    """撰寫並寄送 Gmail 郵件。"""
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
    if references:
        message["References"] = references
    elif in_reply_to:
        message["References"] = in_reply_to

    # base64url 編碼
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

    # 構建 send body
    send_body = {"raw": raw}
    if thread_id:
        send_body["threadId"] = thread_id

    try:
        sent = service.users().messages().send(
            userId="me", body=send_body
        ).execute()

        return {
            "ok": True,
            "message_id": sent["id"],
            "thread_id": sent.get("threadId", ""),
            "message": f"郵件已寄送至 {to}。",
        }
    except Exception as e:
        return {"ok": False, "error": f"無法寄送郵件：{e}"}


def main():
    parser = argparse.ArgumentParser(description="撰寫並寄送 Gmail 郵件")
    parser.add_argument("--credentials", required=True, help="OAuth2 client secret JSON 路徑")
    parser.add_argument("--token", default="token.json", help="Token 路徑")
    parser.add_argument("--scopes", default=None, help="Gmail API scopes（逗號分隔）")
    parser.add_argument("--to", required=True, help="收件人 email")
    parser.add_argument("--subject", required=True, help="郵件主旨")
    parser.add_argument("--body", required=True, help="郵件內文")
    parser.add_argument("--cc", default=None, help="CC 收件人（逗號分隔）")
    parser.add_argument("--bcc", default=None, help="BCC 收件人（逗號分隔）")
    parser.add_argument("--in-reply-to", default=None, help="原信的 Message-ID header")
    parser.add_argument("--references", default=None, help="References header（通常同 In-Reply-To）")
    parser.add_argument("--thread-id", default=None, help="Gmail thread ID（確保回覆在同一對話串）")
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
                "https://www.googleapis.com/auth/gmail.compose",
            ],
            "to": args.to,
            "subject": args.subject,
            "body_length": len(args.body),
            "cc": args.cc,
            "bcc": args.bcc,
            "in_reply_to": args.in_reply_to,
            "references": args.references,
            "thread_id": args.thread_id,
        }
    else:
        result = send_message(args.credentials, args.token, scopes,
                              args.to, args.subject, args.body,
                              args.cc, args.bcc,
                              args.in_reply_to, args.references,
                              args.thread_id)

    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result.get("ok") else 1)


if __name__ == "__main__":
    main()
