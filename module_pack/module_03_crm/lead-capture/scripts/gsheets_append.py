#!/usr/bin/env python3
"""新增一列 lead 至 Google Sheets CRM_Pipeline sheet。

用法：
    python3 gsheets_append.py \
        --credentials credentials.json --token token.json \
        --spreadsheet-id SPREADSHEET_ID \
        --sheet-name CRM_Pipeline \
        --data '{"date":"2026-03-18","client_name":"王大明","contact":"wang@example.com","source":"Telegram","needs_summary":"詢問企業內訓","status":"新詢問","priority":"高","owner":"Sunny","followup_date":"2026-03-19","notes":"","ai_log":"[2026-03-18] 首次詢問"}' \
        [--dry-run]

輸出：JSON 格式（stdout）。
"""

import argparse
import json
import os
import sys

# 確保可以 import 同目錄的 gsheets_auth
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gsheets_auth

# A-K 欄位順序
FIELD_ORDER = [
    "date", "client_name", "contact", "source", "needs_summary",
    "status", "priority", "owner", "followup_date", "notes", "ai_log",
]


def main():
    parser = argparse.ArgumentParser(description="新增 lead 至 CRM Sheet")
    parser.add_argument("--credentials", required=True, help="OAuth2 client secret JSON 路徑")
    parser.add_argument("--token", required=True, help="Token 路徑")
    parser.add_argument("--spreadsheet-id", required=True, help="Google Sheets ID")
    parser.add_argument("--sheet-name", default="CRM_Pipeline", help="目標 Sheet 名稱")
    parser.add_argument("--data", required=True, help="JSON 字串，含 lead 欄位")
    parser.add_argument("--dry-run", action="store_true", help="僅顯示將寫入的資料，不實際執行")
    args = parser.parse_args()

    try:
        lead = json.loads(args.data)
    except json.JSONDecodeError as e:
        print(json.dumps({"ok": False, "error": f"無效的 JSON：{e}"}, ensure_ascii=False))
        sys.exit(1)

    # 按欄位順序組合 row
    row = [lead.get(field, "") for field in FIELD_ORDER]

    if args.dry_run:
        print(json.dumps({
            "ok": True,
            "dry_run": True,
            "sheet": f"{args.sheet_name}!A:K",
            "row": row,
            "fields": dict(zip(FIELD_ORDER, row)),
        }, indent=2, ensure_ascii=False))
        sys.exit(0)

    try:
        creds = gsheets_auth.load_credentials(args.credentials, args.token)
    except SystemExit:
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"ok": False, "error": f"認證失敗：{e}"}, ensure_ascii=False))
        sys.exit(1)

    try:
        from googleapiclient.discovery import build
        service = build("sheets", "v4", credentials=creds)

        body = {"values": [row]}
        result = service.spreadsheets().values().append(
            spreadsheetId=args.spreadsheet_id,
            range=f"{args.sheet_name}!A:K",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body=body,
        ).execute()

        updated_range = result.get("updates", {}).get("updatedRange", "")
        updated_rows = result.get("updates", {}).get("updatedRows", 0)

        print(json.dumps({
            "ok": True,
            "updated_range": updated_range,
            "updated_rows": updated_rows,
            "row": row,
            "message": f"已新增 1 列至 {args.sheet_name}",
        }, indent=2, ensure_ascii=False))
        sys.exit(0)

    except Exception as e:
        print(json.dumps({"ok": False, "error": f"寫入失敗：{e}"}, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
