#!/usr/bin/env python3
"""Gmail 草稿 CRUD + 寄送。

用法：
    # 建立草稿
    python3 gmail_drafts.py --credentials credentials.json --token token.json \
        --action create --to "recipient@example.com" \
        --subject "草稿主旨" --body "草稿內容"

    # 列出草稿
    python3 gmail_drafts.py --credentials credentials.json --token token.json \
        --action list --max-results 10

    # 取得草稿
    python3 gmail_drafts.py --credentials credentials.json --token token.json \
        --action get --draft-id "draft_abc123"

    # 寄送草稿
    python3 gmail_drafts.py --credentials credentials.json --token token.json \
        --action send --draft-id "draft_abc123"

    # 刪除草稿
    python3 gmail_drafts.py --credentials credentials.json --token token.json \
        --action delete --draft-id "draft_abc123"

    # Dry-run 模式
    python3 gmail_drafts.py --dry-run --credentials credentials.json --token token.json \
        --action list

輸出：JSON 格式（stdout），錯誤訊息輸出至 stderr。
"""

import argparse
import base64
import json
import sys
from email.mime.text import MIMEText


def _build_mime_raw(to: str, subject: str, body: str,
                    cc: str | None = None, bcc: str | None = None,
                    in_reply_to: str | None = None) -> str:
    """構建 MIME 訊息並回傳 base64url 編碼字串。"""
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

    return base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")


def _parse_draft_message(msg: dict) -> dict:
    """從草稿的 message 物件中提取摘要資訊。"""
    payload = msg.get("payload", {})
    headers = {}
    for h in payload.get("headers", []):
        if h["name"] in {"From", "To", "Subject", "Date"}:
            headers[h["name"].lower()] = h["value"]

    return {
        "message_id": msg.get("id", ""),
        "snippet": msg.get("snippet", ""),
        "from": headers.get("from", ""),
        "to": headers.get("to", ""),
        "subject": headers.get("subject", ""),
        "date": headers.get("date", ""),
    }


def manage_drafts(credentials_path: str, token_path: str, scopes: list[str],
                  action: str, draft_id: str | None,
                  to: str | None, subject: str | None, body: str | None,
                  cc: str | None, bcc: str | None,
                  in_reply_to: str | None, thread_id: str | None,
                  max_results: int, page_token: str | None) -> dict:
    """執行草稿 CRUD + 寄送操作。"""
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
            if page_token:
                kwargs["pageToken"] = page_token

            response = service.users().drafts().list(**kwargs).execute()
            drafts = response.get("drafts", [])

            result = {
                "ok": True,
                "total_results": len(drafts),
                "drafts": [
                    {"draft_id": d["id"], "message_id": d.get("message", {}).get("id", "")}
                    for d in drafts
                ],
            }

            next_page_token = response.get("nextPageToken")
            if next_page_token:
                result["next_page_token"] = next_page_token

            return result

        if action == "get":
            if not draft_id:
                return {"ok": False, "error": "get 動作需要 --draft-id 參數。"}

            draft = service.users().drafts().get(userId="me", id=draft_id).execute()
            msg = draft.get("message", {})

            return {
                "ok": True,
                "draft_id": draft["id"],
                "message": _parse_draft_message(msg),
            }

        if action == "create":
            if not to or not subject or not body:
                return {"ok": False, "error": "create 動作需要 --to、--subject、--body 參數。"}

            raw = _build_mime_raw(to, subject, body, cc, bcc, in_reply_to)
            draft_body = {"message": {"raw": raw}}
            if thread_id:
                draft_body["message"]["threadId"] = thread_id

            draft = service.users().drafts().create(userId="me", body=draft_body).execute()
            return {
                "ok": True,
                "draft_id": draft["id"],
                "message": "草稿已建立。",
            }

        if action == "send":
            if not draft_id:
                return {"ok": False, "error": "send 動作需要 --draft-id 參數。"}

            sent = service.users().drafts().send(
                userId="me", body={"id": draft_id}
            ).execute()
            return {
                "ok": True,
                "message_id": sent.get("id", ""),
                "thread_id": sent.get("threadId", ""),
                "message": "草稿已寄送。",
            }

        if action == "delete":
            if not draft_id:
                return {"ok": False, "error": "delete 動作需要 --draft-id 參數。"}

            service.users().drafts().delete(userId="me", id=draft_id).execute()
            return {
                "ok": True,
                "draft_id": draft_id,
                "message": "草稿已刪除。",
            }

        return {"ok": False, "error": f"未知動作：{action}"}
    except Exception as e:
        return {"ok": False, "error": f"草稿操作失敗：{e}"}


def main():
    parser = argparse.ArgumentParser(description="Gmail 草稿 CRUD + 寄送")
    parser.add_argument("--credentials", required=True, help="OAuth2 client secret JSON 路徑")
    parser.add_argument("--token", default="token.json", help="Token 路徑")
    parser.add_argument("--scopes", default=None, help="Gmail API scopes（逗號分隔）")
    parser.add_argument("--action", required=True,
                        choices=["create", "list", "get", "send", "delete"],
                        help="動作：create | list | get | send | delete")
    parser.add_argument("--draft-id", default=None, help="草稿 ID（get/send/delete 用）")
    parser.add_argument("--to", default=None, help="收件人 email（create 用）")
    parser.add_argument("--subject", default=None, help="郵件主旨（create 用）")
    parser.add_argument("--body", default=None, help="郵件內文（create 用）")
    parser.add_argument("--cc", default=None, help="CC 收件人（逗號分隔）")
    parser.add_argument("--bcc", default=None, help="BCC 收件人（逗號分隔）")
    parser.add_argument("--in-reply-to", default=None, help="原信的 Message-ID header")
    parser.add_argument("--thread-id", default=None, help="Gmail thread ID")
    parser.add_argument("--max-results", type=int, default=20, help="最多回傳幾筆（預設 20）")
    parser.add_argument("--page-token", default=None, help="分頁 token")
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
            "action": args.action,
            "draft_id": args.draft_id,
            "to": args.to,
            "subject": args.subject,
            "body_length": len(args.body) if args.body else 0,
            "cc": args.cc,
            "bcc": args.bcc,
            "in_reply_to": args.in_reply_to,
            "thread_id": args.thread_id,
            "max_results": args.max_results,
            "page_token": args.page_token,
        }
    else:
        result = manage_drafts(args.credentials, args.token, scopes,
                               args.action, args.draft_id,
                               args.to, args.subject, args.body,
                               args.cc, args.bcc,
                               args.in_reply_to, args.thread_id,
                               args.max_results, args.page_token)

    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result.get("ok") else 1)


if __name__ == "__main__":
    main()
