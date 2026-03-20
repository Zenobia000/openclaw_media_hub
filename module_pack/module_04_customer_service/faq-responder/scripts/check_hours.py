#!/usr/bin/env python3
"""檢查當前是否為工作時間。

用法：
    python3 check_hours.py \
        --timezone Asia/Taipei --start 09:00 --end 18:00 \
        --days Mon,Tue,Wed,Thu,Fri

輸出：JSON 含 is_working_hours、current_time、current_day、next_working_time
"""

import argparse
import json
import sys
from datetime import datetime, timedelta

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def check_working_hours(timezone: str, start: str, end: str,
                        days: list[str], now: datetime | None = None) -> dict:
    """判斷當前是否為工作時間，並計算下一個工作時段。"""
    tz = ZoneInfo(timezone)
    now = now or datetime.now(tz)

    current_day = DAY_NAMES[now.weekday()]
    current_time = now.strftime("%H:%M")
    is_working_day = current_day in days

    sh, sm = map(int, start.split(":"))
    eh, em = map(int, end.split(":"))
    start_minutes = sh * 60 + sm
    end_minutes = eh * 60 + em
    now_minutes = now.hour * 60 + now.minute

    is_working_hours = is_working_day and start_minutes <= now_minutes < end_minutes

    # 計算下一個工作時段開始時間
    next_working_time = None
    if not is_working_hours:
        # 若今天是工作日且還沒到上班時間
        if is_working_day and now_minutes < start_minutes:
            next_dt = now.replace(hour=sh, minute=sm, second=0, microsecond=0)
            next_working_time = next_dt.isoformat()
        else:
            # 往後找下一個工作日
            for offset in range(1, 8):
                candidate = now + timedelta(days=offset)
                if DAY_NAMES[candidate.weekday()] in days:
                    next_dt = candidate.replace(hour=sh, minute=sm, second=0, microsecond=0)
                    next_working_time = next_dt.isoformat()
                    break

    return {
        "is_working_hours": is_working_hours,
        "current_time": current_time,
        "current_day": current_day,
        "timezone": timezone,
        "next_working_time": next_working_time,
    }


def main():
    parser = argparse.ArgumentParser(description="檢查當前是否為工作時間")
    parser.add_argument("--timezone", default="Asia/Taipei", help="時區")
    parser.add_argument("--start", default="09:00", help="上班時間（HH:MM）")
    parser.add_argument("--end", default="18:00", help="下班時間（HH:MM）")
    parser.add_argument("--days", default="Mon,Tue,Wed,Thu,Fri",
                        help="工作日（逗號分隔，如 Mon,Tue,Wed,Thu,Fri）")
    parser.add_argument("--dry-run", action="store_true",
                        help="使用模擬時間（下一個工作日 12:00）測試")
    args = parser.parse_args()

    days = [d.strip() for d in args.days.split(",")]

    now = None
    if args.dry_run:
        tz = ZoneInfo(args.timezone)
        now = datetime.now(tz)
        # 模擬下一個工作日的中午
        for offset in range(0, 8):
            candidate = now + timedelta(days=offset)
            if DAY_NAMES[candidate.weekday()] in days:
                now = candidate.replace(hour=12, minute=0, second=0, microsecond=0)
                break

    result = check_working_hours(args.timezone, args.start, args.end, days, now=now)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
