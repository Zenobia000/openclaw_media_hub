#!/usr/bin/env python3
"""查詢 Google Calendar 空檔時段。

用法：
    python3 gcal_freebusy.py \
        --credentials client_secret.json --token token.json \
        --calendar-id primary --date 2026-03-18

輸出：JSON 陣列 [{"start": "09:00", "end": "10:00"}, ...]
"""

import argparse
import json
from datetime import datetime

from gcal_auth import load_credentials

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo


# --- 時間工具 ---

def to_minutes(hhmm: str) -> int:
    """將 "HH:MM" 轉為當日分鐘數。"""
    h, m = map(int, hhmm.strip().split(":"))
    return h * 60 + m


def from_minutes(mins: int) -> str:
    """將當日分鐘數轉為 "HH:MM"。"""
    return f"{mins // 60:02d}:{mins % 60:02d}"


# --- 核心邏輯 ---

def query_busy_periods(creds, calendar_id: str, date_str: str, timezone: str,
                       start_hour: str, end_hour: str) -> list[tuple[int, int]]:
    """呼叫 freebusy API，回傳忙碌時段清單（以分鐘數表示）。"""
    from googleapiclient.discovery import build

    local_tz = ZoneInfo(timezone)
    date = datetime.strptime(date_str, "%Y-%m-%d")
    sh, sm = divmod(to_minutes(start_hour), 60)
    eh, em = divmod(to_minutes(end_hour), 60)

    body = {
        "timeMin": date.replace(hour=sh, minute=sm, second=0, tzinfo=local_tz).isoformat(),
        "timeMax": date.replace(hour=eh, minute=em, second=0, tzinfo=local_tz).isoformat(),
        "timeZone": timezone,
        "items": [{"id": calendar_id}],
    }

    result = build("calendar", "v3", credentials=creds).freebusy().query(body=body).execute()
    busy = result.get("calendars", {}).get(calendar_id, {}).get("busy", [])

    periods = []
    for p in busy:
        # 將 API 回傳時間轉換至本地時區，確保分鐘數正確
        start = datetime.fromisoformat(p["start"].replace("Z", "+00:00")).astimezone(local_tz)
        end = datetime.fromisoformat(p["end"].replace("Z", "+00:00")).astimezone(local_tz)
        periods.append((start.hour * 60 + start.minute, end.hour * 60 + end.minute))

    return periods


def find_available_slots(busy: list[tuple[int, int]], start_hour: str,
                         end_hour: str, duration: int, buffer: int,
                         now_minutes: int | None = None) -> list[dict]:
    """根據忙碌時段計算可用預約區間。

    now_minutes: 若查詢日期為今天，傳入當前時間的分鐘數以過濾已過去的時段。
    """
    day_start = to_minutes(start_hour)
    day_end = to_minutes(end_hour)

    # 若為今天，從「現在」之後的下一個完整時段開始
    if now_minutes is not None and now_minutes > day_start:
        day_start = now_minutes
    busy.sort()

    slots = []
    cursor = day_start

    for busy_start, busy_end in busy:
        while cursor + duration <= busy_start:
            slots.append({"start": from_minutes(cursor), "end": from_minutes(cursor + duration)})
            cursor += duration + buffer
        cursor = max(cursor, busy_end + buffer)

    while cursor + duration <= day_end:
        slots.append({"start": from_minutes(cursor), "end": from_minutes(cursor + duration)})
        cursor += duration + buffer

    return slots


def main():
    parser = argparse.ArgumentParser(description="查詢 Google Calendar 可用預約時段")
    parser.add_argument("--credentials", required=True, help="認證檔路徑（OAuth2 或 Service Account）")
    parser.add_argument("--token", help="OAuth2 token 快取路徑")
    parser.add_argument("--calendar-id", required=True, help="Google Calendar ID")
    parser.add_argument("--date", required=True, help="查詢日期（YYYY-MM-DD）")
    parser.add_argument("--timezone", default="Asia/Taipei", help="時區")
    parser.add_argument("--start-hour", default="09:00", help="營業開始時間")
    parser.add_argument("--end-hour", default="18:00", help="營業結束時間")
    parser.add_argument("--duration", type=int, default=60, help="預約時長（分鐘）")
    parser.add_argument("--buffer", type=int, default=15, help="預約間隔（分鐘）")
    parser.add_argument("--dry-run", action="store_true", help="跳過 API 呼叫，回傳所有可能時段")
    args = parser.parse_args()

    busy = [] if args.dry_run else query_busy_periods(
        load_credentials(args.credentials, args.token),
        args.calendar_id, args.date, args.timezone,
        args.start_hour, args.end_hour,
    )

    # 若查詢日期為今天，計算當前時間（分鐘數）以過濾已過去的時段
    local_tz = ZoneInfo(args.timezone)
    now_local = datetime.now(local_tz)
    query_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    now_minutes = None
    if query_date == now_local.date():
        now_minutes = now_local.hour * 60 + now_local.minute

    slots = find_available_slots(busy, args.start_hour, args.end_hour, args.duration, args.buffer,
                                 now_minutes=now_minutes)
    print(json.dumps(slots, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
