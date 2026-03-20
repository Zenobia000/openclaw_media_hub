#!/usr/bin/env python3
"""
notion_create.py - 新增 Lead 至 Notion CRM 資料庫
用法:
  python3 notion_create.py \
    --token "ntn_xxx" \
    --database-id "xxx" \
    --data '{"client_name":"...","contact":"...","source":"...","needs_summary":"...","status":"新詢問","priority":"中","owner":"luca","followup_date":"2026-03-23","notes":"","ai_log":"..."}'
"""

import argparse
import json
import sys
import urllib.request
import urllib.error
from datetime import date


def create_page(token: str, database_id: str, data: dict) -> dict:
    url = "https://api.notion.com/v1/pages"
    today = date.today().isoformat()

    properties = {
        "客戶姓名": {
            "title": [{"text": {"content": data.get("client_name", "未提供")}}]
        },
        "聯絡方式": {
            "rich_text": [{"text": {"content": data.get("contact", "未提供")}}]
        },
        "需求摘要": {
            "rich_text": [{"text": {"content": data.get("needs_summary", "")}}]
        },
        "狀態": {
            "select": {"name": data.get("status", "新詢問")}
        },
        "優先級": {
            "select": {"name": data.get("priority", "中")}
        },
        "負責人": {
            "rich_text": [{"text": {"content": data.get("owner", "")}}]
        },
        "備註": {
            "rich_text": [{"text": {"content": data.get("notes", "")}}]
        },
        "AI評分記錄": {
            "rich_text": [{"text": {"content": data.get("ai_log", "")}}]
        },
        "建立日期": {
            "date": {"start": data.get("date", today)}
        },
    }

    # 來源（select，若有值才加）
    source = data.get("source", "")
    if source:
        properties["來源"] = {"select": {"name": source}}

    # 追蹤日期（若有值才加）
    followup = data.get("followup_date", "")
    if followup:
        properties["追蹤日期"] = {"date": {"start": followup}}

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
    parser = argparse.ArgumentParser(description="新增 Lead 至 Notion CRM")
    parser.add_argument("--token", required=True, help="Notion Integration Token")
    parser.add_argument("--database-id", required=True, help="Notion 資料庫 ID")
    parser.add_argument("--data", required=True, help="Lead 資料 JSON 字串")
    args = parser.parse_args()

    try:
        data = json.loads(args.data)
    except json.JSONDecodeError as e:
        print(json.dumps({"ok": False, "error": f"JSON 解析失敗: {e}"}))
        sys.exit(1)

    try:
        result = create_page(args.token, args.database_id, data)
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
