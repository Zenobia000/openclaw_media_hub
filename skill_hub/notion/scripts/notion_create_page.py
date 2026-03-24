#!/usr/bin/env python3
"""新增 Page 至 Notion 資料庫。

用法：
    python3 notion_create_page.py \
        --token "ntn_xxx" \
        --database-id "xxx" \
        --properties '{"客戶姓名":{"title":[{"text":{"content":"王大明"}}]},"狀態":{"select":{"name":"新詢問"}}}'

--properties 接受完整的 Notion properties JSON 物件，
格式遵循 Notion API Create a page 的 properties 規格。

輸出：JSON 含 ok、page_id、url 或 error
"""

import argparse
import json
import sys
import urllib.error
import urllib.request


def create_page(token: str, database_id: str, properties: dict) -> dict:
    """透過 Notion API 在指定 database 建立 page。"""
    url = "https://api.notion.com/v1/pages"

    payload = json.dumps({
        "parent": {"database_id": database_id},
        "properties": properties,
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        raise RuntimeError(f"Notion API error {e.code}: {body}") from e


def main():
    parser = argparse.ArgumentParser(description="新增 Page 至 Notion 資料庫")
    parser.add_argument("--token", required=True, help="Notion Integration Token")
    parser.add_argument("--database-id", required=True, help="Notion 資料庫 ID")
    parser.add_argument("--properties", required=True, help="Notion properties JSON 字串（完整格式）")
    parser.add_argument("--dry-run", action="store_true", help="僅輸出請求內容，不實際建立")
    args = parser.parse_args()

    try:
        properties = json.loads(args.properties)
    except json.JSONDecodeError as e:
        print(json.dumps({"ok": False, "error": f"properties JSON 解析失敗: {e}"}))
        sys.exit(1)

    if args.dry_run:
        print(json.dumps({
            "ok": True,
            "dry_run": True,
            "database_id": args.database_id,
            "properties": properties,
        }, indent=2, ensure_ascii=False))
        sys.exit(0)

    try:
        result = create_page(args.token, args.database_id, properties)
        print(json.dumps({
            "ok": True,
            "page_id": result.get("id"),
            "url": result.get("url"),
        }))
    except RuntimeError as e:
        print(json.dumps({"ok": False, "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
