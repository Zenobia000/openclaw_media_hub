#!/usr/bin/env python3
"""為 Gmail 郵件加標籤。

用法：
    python3 gmail_modify_labels.py \
        --credentials credentials.json \
        --token token.json \
        --scopes "https://www.googleapis.com/auth/gmail.readonly,https://www.googleapis.com/auth/gmail.labels" \
        --message-id "abc123" \
        --add-labels "AI/Inquiry,AI/High" \
        --create-if-missing

    # Dry-run 模式
    python3 gmail_modify_labels.py --dry-run \
        --credentials credentials.json --token token.json \
        --message-id "abc123" --add-labels "AI/Inquiry"

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


def modify_labels(credentials_path: str, token_path: str, scopes: list[str],
                  message_id: str, add_labels: list[str], create_if_missing: bool) -> dict:
    """為郵件加上指定標籤。"""
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

    # 逐一解析標籤名稱為 ID
    label_ids = []
    labels_added = []
    for label_name in add_labels:
        label_id = _get_or_create_label(service, label_name, create_if_missing)
        if label_id:
            label_ids.append(label_id)
            labels_added.append(label_name)
        else:
            print(f"跳過不存在的標籤：{label_name}", file=sys.stderr)

    if not label_ids:
        return {"ok": False, "error": "沒有可用的標籤 ID，操作取消。"}

    try:
        service.users().messages().modify(
            userId="me",
            id=message_id,
            body={"addLabelIds": label_ids},
        ).execute()

        return {
            "ok": True,
            "message_id": message_id,
            "labels_added": labels_added,
        }
    except Exception as e:
        return {"ok": False, "error": f"無法修改郵件標籤 {message_id}：{e}"}


def main():
    parser = argparse.ArgumentParser(description="為 Gmail 郵件加標籤")
    parser.add_argument("--credentials", required=True, help="OAuth2 client secret JSON 路徑")
    parser.add_argument("--token", default="token.json", help="Token 路徑")
    parser.add_argument("--scopes", default=None, help="Gmail API scopes（逗號分隔）")
    parser.add_argument("--message-id", required=True, help="Gmail 郵件 ID")
    parser.add_argument("--add-labels", required=True, help="要加的標籤（逗號分隔），例如 AI/Inquiry,AI/High")
    parser.add_argument("--create-if-missing", action="store_true", help="標籤不存在時自動建立")
    parser.add_argument("--dry-run", action="store_true", help="不呼叫 API，僅驗證參數")
    args = parser.parse_args()

    scopes = [s.strip() for s in args.scopes.split(",") if s.strip()] if args.scopes else None
    add_labels = [l.strip() for l in args.add_labels.split(",") if l.strip()]

    if args.dry_run:
        result = {
            "ok": True,
            "dry_run": True,
            "credentials": args.credentials,
            "token": args.token,
            "scopes": scopes or [
                "https://www.googleapis.com/auth/gmail.readonly",
                "https://www.googleapis.com/auth/gmail.labels",
            ],
            "message_id": args.message_id,
            "add_labels": add_labels,
            "create_if_missing": args.create_if_missing,
        }
    else:
        result = modify_labels(args.credentials, args.token, scopes,
                               args.message_id, add_labels, args.create_if_missing)

    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result.get("ok") else 1)


if __name__ == "__main__":
    main()
