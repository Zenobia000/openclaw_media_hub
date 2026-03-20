#!/usr/bin/env python3
"""建立 Google Calendar 事件。

用法：
    python3 gcal_create_event.py \
        --credentials client_secret.json --token token.json \
        --calendar-id primary \
        --title "桑尼工作室 - 王小明 預約" \
        --start "2026-03-18T14:00:00" --end "2026-03-18T15:00:00" \
        --timezone "Asia/Taipei"

輸出：JSON 含 event_id、calendar_link、status
"""

import argparse
import json

from gcal_auth import load_credentials


def _build_event_body(title: str, start: str, end: str, timezone: str,
                      description: str = "", attendees: list[str] | None = None) -> dict:
    """組裝事件 body dict。"""
    body = {
        "summary": title,
        "start": {"dateTime": start, "timeZone": timezone},
        "end": {"dateTime": end, "timeZone": timezone},
    }
    if description:
        body["description"] = description
    if attendees:
        body["attendees"] = [{"email": e.strip()} for e in attendees if e.strip()]
    return body


def create_event(creds, calendar_id: str, title: str, start: str, end: str,
                 timezone: str, description: str = "",
                 attendees: list[str] | None = None) -> dict:
    """建立日曆事件，回傳事件詳情。"""
    from googleapiclient.discovery import build

    body = _build_event_body(title, start, end, timezone, description, attendees)
    event = build("calendar", "v3", credentials=creds).events().insert(
        calendarId=calendar_id,
        body=body,
        sendUpdates="all" if attendees else "none",
    ).execute()

    return {
        "event_id": event.get("id", ""),
        "calendar_link": event.get("htmlLink", ""),
        "status": event.get("status", ""),
        "summary": event.get("summary", ""),
        "start": event.get("start", {}).get("dateTime", ""),
        "end": event.get("end", {}).get("dateTime", ""),
    }


def _parse_attendees(raw: str) -> list[str]:
    """解析逗號分隔的 email 字串。"""
    return [e.strip() for e in raw.split(",") if e.strip()] if raw else []


def main():
    parser = argparse.ArgumentParser(description="建立 Google Calendar 事件")
    parser.add_argument("--credentials", required=True, help="認證檔路徑")
    parser.add_argument("--token", help="OAuth2 token 快取路徑")
    parser.add_argument("--calendar-id", required=True, help="Google Calendar ID")
    parser.add_argument("--title", required=True, help="事件標題")
    parser.add_argument("--start", required=True, help="開始時間（ISO-8601）")
    parser.add_argument("--end", required=True, help="結束時間（ISO-8601）")
    parser.add_argument("--timezone", default="Asia/Taipei", help="時區")
    parser.add_argument("--description", default="", help="事件描述")
    parser.add_argument("--attendees", default="", help="參與者 email（逗號分隔）")
    parser.add_argument("--dry-run", action="store_true", help="僅輸出事件內容，不實際建立")
    args = parser.parse_args()

    attendees = _parse_attendees(args.attendees)

    if args.dry_run:
        body = _build_event_body(args.title, args.start, args.end, args.timezone,
                                 args.description, attendees)
        print(json.dumps({"dry_run": True, "event_body": body}, indent=2, ensure_ascii=False))
    else:
        result = create_event(
            load_credentials(args.credentials, args.token),
            args.calendar_id, args.title, args.start, args.end,
            args.timezone, args.description, attendees,
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
