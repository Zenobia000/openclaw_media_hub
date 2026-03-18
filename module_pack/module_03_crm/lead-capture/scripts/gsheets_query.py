#!/usr/bin/env python3
"""查詢 Google Sheets CRM_Pipeline leads。

支援按欄位過濾及逾期追蹤。

用法：
    # 查詢所有
    python3 gsheets_query.py --credentials creds.json --token token.json --spreadsheet-id ID

    # 按欄位過濾
    python3 gsheets_query.py --credentials creds.json --token token.json --spreadsheet-id ID \
        --filter-field status --filter-value "新詢問"

    # 僅逾期 follow-up
    python3 gsheets_query.py --credentials creds.json --token token.json --spreadsheet-id ID \
        --overdue-only

輸出：JSON 格式（stdout）。
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gsheets_auth

HEADERS = [
    "date", "client_name", "contact", "source", "needs_summary",
    "status", "priority", "owner", "followup_date", "notes", "ai_log",
]

# 不參與逾期過濾的結案狀態
CLOSED_STATUSES = {"已成交", "已流失"}


def main():
    parser = argparse.ArgumentParser(description="查詢 CRM Sheet leads")
    parser.add_argument("--credentials", required=True, help="OAuth2 client secret JSON 路徑")
    parser.add_argument("--token", required=True, help="Token 路徑")
    parser.add_argument("--spreadsheet-id", required=True, help="Google Sheets ID")
    parser.add_argument("--sheet-name", default="CRM_Pipeline", help="目標 Sheet 名稱")
    parser.add_argument("--filter-field", default="", help="過濾欄位名稱（如 status、priority、source）")
    parser.add_argument("--filter-value", default="", help="過濾值")
    parser.add_argument("--overdue-only", action="store_true", help="僅顯示 follow-up 已逾期的紀錄")
    parser.add_argument("--dry-run", action="store_true", help="僅顯示查詢參數，不實際執行")
    args = parser.parse_args()

    if args.dry_run:
        print(json.dumps({
            "ok": True,
            "dry_run": True,
            "range": f"{args.sheet_name}!A:K",
            "filter_field": args.filter_field,
            "filter_value": args.filter_value,
            "overdue_only": args.overdue_only,
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
            range=f"{args.sheet_name}!A:K",
        ).execute()

        rows = result.get("values", [])
        if not rows:
            print(json.dumps({"ok": True, "total": 0, "leads": [], "message": "CRM 無資料"}, ensure_ascii=False))
            sys.exit(0)

        # 跳過表頭
        data_rows = rows[1:] if len(rows) > 1 else []

        leads = []
        for i, row in enumerate(data_rows, start=2):
            # 補齊不足的欄位
            padded = row + [""] * (len(HEADERS) - len(row))
            lead = {HEADERS[j]: padded[j] for j in range(len(HEADERS))}
            lead["_row"] = i  # 紀錄 row number（1-based，含表頭）
            leads.append(lead)

        # 按欄位過濾
        if args.filter_field and args.filter_value:
            field = args.filter_field
            if field in HEADERS:
                leads = [l for l in leads if l.get(field, "") == args.filter_value]

        # 逾期過濾
        if args.overdue_only:
            today = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d")
            filtered = []
            for l in leads:
                fu_date = l.get("followup_date", "")
                status = l.get("status", "")
                if fu_date and fu_date < today and status not in CLOSED_STATUSES:
                    filtered.append(l)
            leads = filtered

        print(json.dumps({
            "ok": True,
            "total": len(leads),
            "leads": leads,
        }, indent=2, ensure_ascii=False))
        sys.exit(0)

    except Exception as e:
        print(json.dumps({"ok": False, "error": f"查詢失敗：{e}"}, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
