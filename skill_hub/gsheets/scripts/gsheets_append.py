#!/usr/bin/env python3
"""新增一列資料至 Google Sheets。

用法：
    python3 gsheets_append.py \
        --credentials credentials.json --token token.json \
        --spreadsheet-id SPREADSHEET_ID \
        --sheet-name Sheet1 \
        --fields "name,email,date,notes" \
        --data '{"name":"王大明","email":"wang@example.com","date":"2026-03-18","notes":"備註"}' \
        [--dry-run]

輸出：JSON 格式（stdout）。
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gsheets_auth


def main():
    parser = argparse.ArgumentParser(description="新增一列資料至 Google Sheets")
    parser.add_argument("--credentials", required=True, help="OAuth2 client secret JSON 路徑")
    parser.add_argument("--token", required=True, help="Token 路徑")
    parser.add_argument("--spreadsheet-id", required=True, help="Google Sheets ID")
    parser.add_argument("--sheet-name", default="Sheet1", help="目標 Sheet 名稱")
    parser.add_argument("--fields", required=True, help="欄位順序（逗號分隔），對應 A, B, C... 欄")
    parser.add_argument("--data", required=True, help="JSON 字串，含欄位資料")
    parser.add_argument("--dry-run", action="store_true", help="僅顯示將寫入的資料，不實際執行")
    args = parser.parse_args()

    try:
        data = json.loads(args.data)
    except json.JSONDecodeError as e:
        print(json.dumps({"ok": False, "error": f"無效的 JSON：{e}"}, ensure_ascii=False))
        sys.exit(1)

    field_order = [f.strip() for f in args.fields.split(",") if f.strip()]
    col_end = chr(ord("A") + len(field_order) - 1)

    # 按欄位順序組合 row
    row = [data.get(field, "") for field in field_order]

    if args.dry_run:
        print(json.dumps({
            "ok": True,
            "dry_run": True,
            "sheet": f"{args.sheet_name}!A:{col_end}",
            "row": row,
            "fields": dict(zip(field_order, row)),
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
            range=f"{args.sheet_name}!A:{col_end}",
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
