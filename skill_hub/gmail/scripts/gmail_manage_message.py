#!/usr/bin/env python3
"""管理 Gmail 郵件（修改標籤、垃圾桶、封存）。

用法：
    # 修改標籤
    python3 gmail_manage_message.py \
        --credentials credentials.json --token token.json \
        --message-id "abc123" --action modify-labels \
        --add-labels "STARRED" --remove-labels "UNREAD"

    # 自動建立不存在的標籤
    python3 gmail_manage_message.py \
        --credentials credentials.json --token token.json \
        --message-id "abc123" --action modify-labels \
        --add-labels "AI/Inquiry,AI/High" --create-if-missing

    # 移至垃圾桶
    python3 gmail_manage_message.py \
        --credentials credentials.json --token token.json \
        --message-id "abc123" --action trash

    # 從垃圾桶還原
    python3 gmail_manage_message.py \
        --credentials credentials.json --token token.json \
        --message-id "abc123" --action untrash

    # 封存（從收件匣移除）
    python3 gmail_manage_message.py \
        --credentials credentials.json --token token.json \
        --message-id "abc123" --action archive

    # Dry-run 模式
    python3 gmail_manage_message.py --dry-run \
        --credentials credentials.json --token token.json \
        --message-id "abc123" --action trash

輸出：JSON 格式（stdout），錯誤訊息輸出至 stderr。
"""

import argparse
import json
import sys


def _get_or_create_label(service, label_name: str, create_if_missing: bool) -> str | None:
    """取得標籤 ID，若不存在且 create_if_missing 為 True 則自動建立。"""
    try:
        response = service.users().labels().list(userId="me").execute()
        labels = response.get("labels", [])

        for label in labels:
            if label["name"] == label_name:
                return label["id"]

        if not create_if_missing:
            return None

        # 建立新標籤
        new_label = service.users().labels().create(
            userId="me",
            body={
                "name": label_name,
                "labelListVisibility": "labelShow",
                "messageListVisibility": "show",
            },
        ).execute()
        print(f"已建立標籤：{label_name}", file=sys.stderr)
        return new_label["id"]
    except Exception as e:
        print(f"標籤操作失敗 ({label_name})：{e}", file=sys.stderr)
        return None


def _resolve_label_ids(service, label_names: list[str], create_if_missing: bool) -> list[str]:
    """將標籤名稱列表解析為 ID 列表。系統標籤（全大寫）直接使用。"""
    label_ids = []
    for name in label_names:
        # 系統標籤（如 INBOX, UNREAD, STARRED）直接當 ID 使用
        if name.isupper() and "/" not in name:
            label_ids.append(name)
        else:
            label_id = _get_or_create_label(service, name, create_if_missing)
            if label_id:
                label_ids.append(label_id)
            else:
                print(f"跳過不存在的標籤：{name}", file=sys.stderr)
    return label_ids


def manage_message(credentials_path: str, token_path: str, scopes: list[str],
                   message_id: str, action: str,
                   add_labels: list[str] | None, remove_labels: list[str] | None,
                   create_if_missing: bool) -> dict:
    """管理 Gmail 郵件。"""
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
        if action == "trash":
            service.users().messages().trash(userId="me", id=message_id).execute()
            return {"ok": True, "message_id": message_id, "action": "trash", "message": "郵件已移至垃圾桶。"}

        if action == "untrash":
            service.users().messages().untrash(userId="me", id=message_id).execute()
            return {"ok": True, "message_id": message_id, "action": "untrash", "message": "郵件已從垃圾桶還原。"}

        if action == "archive":
            service.users().messages().modify(
                userId="me", id=message_id,
                body={"removeLabelIds": ["INBOX"]},
            ).execute()
            return {"ok": True, "message_id": message_id, "action": "archive", "message": "郵件已封存。"}

        if action == "modify-labels":
            body = {}
            added = []
            removed = []

            if add_labels:
                ids = _resolve_label_ids(service, add_labels, create_if_missing)
                if ids:
                    body["addLabelIds"] = ids
                    added = add_labels

            if remove_labels:
                ids = _resolve_label_ids(service, remove_labels, create_if_missing=False)
                if ids:
                    body["removeLabelIds"] = ids
                    removed = remove_labels

            if not body:
                return {"ok": False, "error": "沒有可用的標籤 ID，操作取消。"}

            service.users().messages().modify(
                userId="me", id=message_id, body=body,
            ).execute()

            return {
                "ok": True,
                "message_id": message_id,
                "action": "modify-labels",
                "labels_added": added,
                "labels_removed": removed,
            }

        return {"ok": False, "error": f"未知動作：{action}"}
    except Exception as e:
        return {"ok": False, "error": f"無法管理郵件 {message_id}：{e}"}


def main():
    parser = argparse.ArgumentParser(description="管理 Gmail 郵件")
    parser.add_argument("--credentials", required=True, help="OAuth2 client secret JSON 路徑")
    parser.add_argument("--token", default="token.json", help="Token 路徑")
    parser.add_argument("--scopes", default=None, help="Gmail API scopes（逗號分隔）")
    parser.add_argument("--message-id", required=True, help="Gmail 郵件 ID")
    parser.add_argument("--action", required=True,
                        choices=["modify-labels", "trash", "untrash", "archive"],
                        help="動作：modify-labels | trash | untrash | archive")
    parser.add_argument("--add-labels", default=None, help="要加的標籤（逗號分隔）")
    parser.add_argument("--remove-labels", default=None, help="要移除的標籤（逗號分隔）")
    parser.add_argument("--create-if-missing", action="store_true", help="標籤不存在時自動建立")
    parser.add_argument("--dry-run", action="store_true", help="不呼叫 API，僅驗證參數")
    args = parser.parse_args()

    scopes = [s.strip() for s in args.scopes.split(",") if s.strip()] if args.scopes else None
    add_labels = [l.strip() for l in args.add_labels.split(",") if l.strip()] if args.add_labels else None
    remove_labels = [l.strip() for l in args.remove_labels.split(",") if l.strip()] if args.remove_labels else None

    if args.dry_run:
        result = {
            "ok": True,
            "dry_run": True,
            "credentials": args.credentials,
            "token": args.token,
            "scopes": scopes or ["https://www.googleapis.com/auth/gmail.modify"],
            "message_id": args.message_id,
            "action": args.action,
            "add_labels": add_labels,
            "remove_labels": remove_labels,
            "create_if_missing": args.create_if_missing,
        }
    else:
        result = manage_message(args.credentials, args.token, scopes,
                                args.message_id, args.action,
                                add_labels, remove_labels, args.create_if_missing)

    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result.get("ok") else 1)


if __name__ == "__main__":
    main()
