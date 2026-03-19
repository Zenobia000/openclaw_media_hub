#!/usr/bin/env python3
"""Gmail 標籤 CRUD。

用法：
    # 列出所有標籤
    python3 gmail_labels.py --credentials credentials.json --token token.json \
        --action list

    # 取得單一標籤
    python3 gmail_labels.py --credentials credentials.json --token token.json \
        --action get --label-id "Label_123"

    # 建立標籤
    python3 gmail_labels.py --credentials credentials.json --token token.json \
        --action create --label-name "AI/Reports"

    # 更新標籤
    python3 gmail_labels.py --credentials credentials.json --token token.json \
        --action update --label-id "Label_123" --label-name "AI/Summary" \
        --visibility labelShow --message-visibility show

    # 刪除標籤
    python3 gmail_labels.py --credentials credentials.json --token token.json \
        --action delete --label-id "Label_123"

    # Dry-run 模式
    python3 gmail_labels.py --dry-run --credentials credentials.json --token token.json \
        --action list

輸出：JSON 格式（stdout），錯誤訊息輸出至 stderr。
"""

import argparse
import json
import sys


def manage_labels(credentials_path: str, token_path: str, scopes: list[str],
                  action: str, label_id: str | None, label_name: str | None,
                  visibility: str | None, message_visibility: str | None) -> dict:
    """執行標籤 CRUD 操作。"""
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
            response = service.users().labels().list(userId="me").execute()
            labels = response.get("labels", [])
            return {
                "ok": True,
                "total": len(labels),
                "labels": [
                    {"id": l["id"], "name": l["name"], "type": l.get("type", "")}
                    for l in labels
                ],
            }

        if action == "get":
            if not label_id:
                return {"ok": False, "error": "get 動作需要 --label-id 參數。"}
            label = service.users().labels().get(userId="me", id=label_id).execute()
            return {
                "ok": True,
                "label": {
                    "id": label["id"],
                    "name": label["name"],
                    "type": label.get("type", ""),
                    "messages_total": label.get("messagesTotal", 0),
                    "messages_unread": label.get("messagesUnread", 0),
                    "threads_total": label.get("threadsTotal", 0),
                    "threads_unread": label.get("threadsUnread", 0),
                    "visibility": label.get("labelListVisibility", ""),
                    "message_visibility": label.get("messageListVisibility", ""),
                },
            }

        if action == "create":
            if not label_name:
                return {"ok": False, "error": "create 動作需要 --label-name 參數。"}
            body = {
                "name": label_name,
                "labelListVisibility": visibility or "labelShow",
                "messageListVisibility": message_visibility or "show",
            }
            label = service.users().labels().create(userId="me", body=body).execute()
            return {
                "ok": True,
                "label_id": label["id"],
                "label_name": label["name"],
                "message": f"標籤「{label_name}」已建立。",
            }

        if action == "update":
            if not label_id:
                return {"ok": False, "error": "update 動作需要 --label-id 參數。"}
            body = {}
            if label_name:
                body["name"] = label_name
            if visibility:
                body["labelListVisibility"] = visibility
            if message_visibility:
                body["messageListVisibility"] = message_visibility
            if not body:
                return {"ok": False, "error": "update 動作至少需要一個更新欄位。"}
            label = service.users().labels().update(userId="me", id=label_id, body=body).execute()
            return {
                "ok": True,
                "label_id": label["id"],
                "label_name": label["name"],
                "message": "標籤已更新。",
            }

        if action == "delete":
            if not label_id:
                return {"ok": False, "error": "delete 動作需要 --label-id 參數。"}
            service.users().labels().delete(userId="me", id=label_id).execute()
            return {
                "ok": True,
                "label_id": label_id,
                "message": "標籤已刪除。",
            }

        return {"ok": False, "error": f"未知動作：{action}"}
    except Exception as e:
        return {"ok": False, "error": f"標籤操作失敗：{e}"}


def main():
    parser = argparse.ArgumentParser(description="Gmail 標籤 CRUD")
    parser.add_argument("--credentials", required=True, help="OAuth2 client secret JSON 路徑")
    parser.add_argument("--token", default="token.json", help="Token 路徑")
    parser.add_argument("--scopes", default=None, help="Gmail API scopes（逗號分隔）")
    parser.add_argument("--action", required=True,
                        choices=["list", "create", "get", "update", "delete"],
                        help="動作：list | create | get | update | delete")
    parser.add_argument("--label-id", default=None, help="標籤 ID（get/update/delete 用）")
    parser.add_argument("--label-name", default=None, help="標籤名稱（create/update 用）")
    parser.add_argument("--visibility", default=None,
                        choices=["labelShow", "labelShowIfUnread", "labelHide"],
                        help="標籤清單顯示方式")
    parser.add_argument("--message-visibility", default=None,
                        choices=["show", "hide"],
                        help="郵件清單顯示方式")
    parser.add_argument("--dry-run", action="store_true", help="不呼叫 API，僅驗證參數")
    args = parser.parse_args()

    scopes = [s.strip() for s in args.scopes.split(",") if s.strip()] if args.scopes else None

    if args.dry_run:
        result = {
            "ok": True,
            "dry_run": True,
            "credentials": args.credentials,
            "token": args.token,
            "scopes": scopes or ["https://www.googleapis.com/auth/gmail.labels"],
            "action": args.action,
            "label_id": args.label_id,
            "label_name": args.label_name,
            "visibility": args.visibility,
            "message_visibility": args.message_visibility,
        }
    else:
        result = manage_labels(args.credentials, args.token, scopes,
                               args.action, args.label_id, args.label_name,
                               args.visibility, args.message_visibility)

    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result.get("ok") else 1)


if __name__ == "__main__":
    main()
