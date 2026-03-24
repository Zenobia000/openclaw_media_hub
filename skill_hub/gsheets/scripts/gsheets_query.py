#!/usr/bin/env python3
"""查詢 Google Sheets 資料。

支援按欄位過濾及逾期追蹤。

用法：
    # 查詢所有
    python3 gsheets_query.py --credentials creds.json --token token.json \
        --spreadsheet-id ID --fields "date,name,email,status"

    # 按欄位過濾
    python3 gsheets_query.py --credentials creds.json --token token.json \
        --spreadsheet-id ID --fields "date,name,email,status" \
        --filter-field status --filter-value "active"

    # 僅逾期紀錄（需指定日期欄位與排除狀態）
    python3 gsheets_query.py --credentials creds.json --token token.json \
        --spreadsheet-id ID --fields "date,name,status,followup_date" \
        --overdue-field followup_date --closed-statuses "done,cancelled"

輸出：JSON 格式（stdout）。
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gsheets_auth


def main():
    parser = argparse.ArgumentParser(description="查詢 Google Sheets 資料")
    parser.add_argument("--credentials", required=True, help="OAuth2 client secret JSON 路徑")
    parser.add_argument("--token", required=True, help="Token 路徑")
    parser.add_argument("--spreadsheet-id", required=True, help="Google Sheets ID")
    parser.add_argument("--sheet-name", default="Sheet1", help="目標 Sheet 名稱")
    parser.add_argument("--fields", required=True, help="欄位名稱（逗號分隔），對應表頭 A, B, C...")
    parser.add_argument("--filter-field", default="", help="過濾欄位名稱")
    parser.add_argument("--filter-value", default="", help="過濾值")
    parser.add_argument("--overdue-field", default="", help="逾期判斷用的日期欄位名稱")
    parser.add_argument("--closed-statuses", default="", help="結案狀態（逗號分隔），逾期過濾時排除")
    parser.add_argument("--status-field", default="status", help="狀態欄位名稱（搭配 --closed-statuses 使用）")
    parser.add_argument("--tz-offset", type=int, default=8, help="時區偏移（小時，預設 +8）")
    parser.add_argument("--dry-run", action="store_true", help="僅顯示查詢參數，不實際執行")
    args = parser.parse_args()

    headers = [f.strip() for f in args.fields.split(",") if f.strip()]
    col_end = chr(ord("A") + len(headers) - 1)

    if args.dry_run:
        print(json.dumps({
            "ok": True,
            "dry_run": True,
            "range": f"{args.sheet_name}!A:{col_end}",
            "filter_field": args.filter_field,
            "filter_value": args.filter_value,
            "overdue_field": args.overdue_field,
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

        result = service.spreadsheets().values().get(
            spreadsheetId=args.spreadsheet_id,
            range=f"{args.sheet_name}!A:{col_end}",
        ).execute()

        rows = result.get("values", [])
        if not rows:
            print(json.dumps({"ok": True, "total": 0, "rows": [], "message": "無資料"}, ensure_ascii=False))
            sys.exit(0)

        # 跳過表頭
        data_rows = rows[1:] if len(rows) > 1 else []

        records = []
        for i, row in enumerate(data_rows, start=2):
            padded = row + [""] * (len(headers) - len(row))
            record = {headers[j]: padded[j] for j in range(len(headers))}
            record["_row"] = i
            records.append(record)

        # 按欄位過濾
        if args.filter_field and args.filter_value:
            if args.filter_field in headers:
                records = [r for r in records if r.get(args.filter_field, "") == args.filter_value]

        # 逾期過濾
        if args.overdue_field and args.overdue_field in headers:
            closed = set(s.strip() for s in args.closed_statuses.split(",") if s.strip())
            today = datetime.now(timezone(timedelta(hours=args.tz_offset))).strftime("%Y-%m-%d")
            filtered = []
            for r in records:
                date_val = r.get(args.overdue_field, "")
                status_val = r.get(args.status_field, "")
                if date_val and date_val < today and status_val not in closed:
                    filtered.append(r)
            records = filtered

        print(json.dumps({
            "ok": True,
            "total": len(records),
            "rows": records,
        }, indent=2, ensure_ascii=False))
        sys.exit(0)

    except Exception as e:
        print(json.dumps({"ok": False, "error": f"查詢失敗：{e}"}, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
