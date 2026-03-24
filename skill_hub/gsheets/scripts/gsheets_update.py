#!/usr/bin/env python3
"""更新 Google Sheets 現有紀錄的特定欄位。

用法：
    python3 gsheets_update.py \
        --credentials creds.json --token token.json \
        --spreadsheet-id ID \
        --sheet-name Sheet1 \
        --field-map '{"name":"A","email":"B","status":"C","notes":"D"}' \
        --row 5 --field status --value "active" \
        [--protected-fields "name,email"] \
        [--append-mode] [--dry-run]

--field-map：JSON 物件，key 為欄位名稱，value 為對應的欄號（A, B, C...）。
--protected-fields：受保護欄位（逗號分隔），拒絕更新。
--append-mode：追加模式（在現有值後追加而非覆蓋）。

輸出：JSON 格式（stdout）。
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gsheets_auth


def main():
    parser = argparse.ArgumentParser(description="更新 Google Sheets 紀錄")
    parser.add_argument("--credentials", required=True, help="OAuth2 client secret JSON 路徑")
    parser.add_argument("--token", required=True, help="Token 路徑")
    parser.add_argument("--spreadsheet-id", required=True, help="Google Sheets ID")
    parser.add_argument("--sheet-name", default="Sheet1", help="目標 Sheet 名稱")
    parser.add_argument("--field-map", required=True, help="欄位→欄號對應 JSON（如 {\"name\":\"A\",\"status\":\"C\"}）")
    parser.add_argument("--row", required=True, type=int, help="要更新的列號（1-based，含表頭）")
    parser.add_argument("--field", required=True, help="要更新的欄位名稱")
    parser.add_argument("--value", required=True, help="新值")
    parser.add_argument("--protected-fields", default="", help="受保護欄位（逗號分隔），不允許更新")
    parser.add_argument("--append-mode", action="store_true",
                        help="追加模式，在現有值後追加而非覆蓋")
    parser.add_argument("--dry-run", action="store_true", help="僅顯示將更新的內容，不實際執行")
    args = parser.parse_args()

    # 解析 field-map
    try:
        field_map = json.loads(args.field_map)
    except json.JSONDecodeError as e:
        print(json.dumps({"ok": False, "error": f"field-map JSON 解析失敗：{e}"}, ensure_ascii=False))
        sys.exit(1)

    # 解析 protected-fields
    protected = set(f.strip() for f in args.protected_fields.split(",") if f.strip())

    # 驗證欄位
    if args.field in protected:
        print(json.dumps({
            "ok": False,
            "error": f"欄位 '{args.field}' 為受保護欄位，不允許修改。受保護欄位：{', '.join(sorted(protected))}",
        }, ensure_ascii=False))
        sys.exit(1)

    if args.field not in field_map:
        print(json.dumps({
            "ok": False,
            "error": f"欄位 '{args.field}' 不在 field-map 中。可用欄位：{', '.join(sorted(field_map.keys()))}",
        }, ensure_ascii=False))
        sys.exit(1)

    if args.row < 2:
        print(json.dumps({"ok": False, "error": "row 必須 >= 2（第 1 列是表頭）"}, ensure_ascii=False))
        sys.exit(1)

    col = field_map[args.field]
    cell = f"{args.sheet_name}!{col}{args.row}"

    if args.dry_run:
        print(json.dumps({
            "ok": True,
            "dry_run": True,
            "cell": cell,
            "field": args.field,
            "value": args.value,
            "append_mode": args.append_mode,
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

        final_value = args.value

        # append-mode：先讀取現有值再追加
        if args.append_mode:
            existing = service.spreadsheets().values().get(
                spreadsheetId=args.spreadsheet_id,
                range=cell,
            ).execute()
            old_values = existing.get("values", [[""]])
            old_value = old_values[0][0] if old_values and old_values[0] else ""
            if old_value:
                final_value = old_value + "\n" + args.value
            else:
                final_value = args.value

        body = {"values": [[final_value]]}
        service.spreadsheets().values().update(
            spreadsheetId=args.spreadsheet_id,
            range=cell,
            valueInputOption="USER_ENTERED",
            body=body,
        ).execute()

        print(json.dumps({
            "ok": True,
            "updated_cell": cell,
            "field": args.field,
            "value": final_value,
            "append_mode": args.append_mode,
            "message": f"已更新 {cell}（{args.field}）",
        }, indent=2, ensure_ascii=False))
        sys.exit(0)

    except Exception as e:
        print(json.dumps({"ok": False, "error": f"更新失敗：{e}"}, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
