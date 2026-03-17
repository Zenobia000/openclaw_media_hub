#!/usr/bin/env python3
"""Query Google Calendar freebusy API and return available slots.

Supports two credential types:
  1. OAuth2 Desktop (installed) app — requires initial browser auth
  2. Service Account — headless, no browser needed

Usage:
    # OAuth2 Desktop App (first run opens browser for consent)
    python3 gcal_freebusy.py \
        --credentials client_secret_xxx.json \
        --token token.json \
        --calendar-id primary \
        --date 2026-03-18 \
        --timezone Asia/Taipei

    # Service Account
    python3 gcal_freebusy.py \
        --credentials service_account.json \
        --calendar-id primary \
        --date 2026-03-18

Output: JSON array of available slots, e.g.:
    [
        {"start": "09:00", "end": "10:00"},
        {"start": "10:15", "end": "11:15"}
    ]
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone as tz

try:
    import zoneinfo
    ZoneInfo = zoneinfo.ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def parse_time(t: str) -> tuple[int, int]:
    parts = t.strip().split(":")
    return int(parts[0]), int(parts[1])


def time_to_minutes(h: int, m: int) -> int:
    return h * 60 + m


def minutes_to_str(mins: int) -> str:
    return f"{mins // 60:02d}:{mins % 60:02d}"


def load_credentials(credentials_path: str, token_path: str | None = None):
    """Load credentials — auto-detect OAuth2 installed vs service account."""
    with open(credentials_path, "r") as f:
        cred_data = json.load(f)

    # OAuth2 Desktop (installed) app
    if "installed" in cred_data or "web" in cred_data:
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
        except ImportError:
            print("Error: google-auth-oauthlib is required for OAuth2 desktop flow.", file=sys.stderr)
            print("Install with: pip install google-auth-oauthlib google-api-python-client", file=sys.stderr)
            sys.exit(1)

        creds = None
        if token_path and os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                # Use redirect to localhost and run local server
                # If no display / headless, fall back to console-based flow
                if os.environ.get("DISPLAY") or os.environ.get("BROWSER"):
                    try:
                        creds = flow.run_local_server(port=0, open_browser=False)
                    except Exception:
                        creds = None
                if not creds or not getattr(creds, 'token', None):
                    # Console flow: print URL, user pastes redirect URL back
                    flow.redirect_uri = "http://localhost:1"
                    auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")
                    print(f"\n{'='*60}", file=sys.stderr)
                    print("請在瀏覽器開啟以下網址進行 Google 授權：", file=sys.stderr)
                    print(f"\n{auth_url}\n", file=sys.stderr)
                    print("授權後瀏覽器會跳轉到一個無法載入的頁面，", file=sys.stderr)
                    print("請複製該頁面的完整網址（以 http://localhost:1 開頭）貼到這裡：", file=sys.stderr)
                    print(f"{'='*60}\n", file=sys.stderr)
                    redirect_response = input("貼上完整網址: ").strip()
                    flow.fetch_token(authorization_response=redirect_response)
                    creds = flow.credentials

            if token_path:
                with open(token_path, "w") as token_file:
                    token_file.write(creds.to_json())
                print(f"Token saved to {token_path}", file=sys.stderr)

        return creds

    # Service Account
    else:
        try:
            from google.oauth2 import service_account
        except ImportError:
            print("Error: google-auth is required.", file=sys.stderr)
            sys.exit(1)
        return service_account.Credentials.from_service_account_file(credentials_path, scopes=SCOPES)


def get_busy_periods(creds, calendar_id: str, date_str: str, timezone: str, start_hour: str, end_hour: str):
    """Query Google Calendar freebusy API for busy periods on the given date."""
    from googleapiclient.discovery import build

    service = build("calendar", "v3", credentials=creds)

    sh, sm = parse_time(start_hour)
    eh, em = parse_time(end_hour)

    local_tz = ZoneInfo(timezone)
    date = datetime.strptime(date_str, "%Y-%m-%d")
    time_min = date.replace(hour=sh, minute=sm, second=0, tzinfo=local_tz).isoformat()
    time_max = date.replace(hour=eh, minute=em, second=0, tzinfo=local_tz).isoformat()

    body = {
        "timeMin": time_min,
        "timeMax": time_max,
        "timeZone": timezone,
        "items": [{"id": calendar_id}]
    }

    result = service.freebusy().query(body=body).execute()
    busy = result.get("calendars", {}).get(calendar_id, {}).get("busy", [])

    busy_periods = []
    for period in busy:
        start = datetime.fromisoformat(period["start"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(period["end"].replace("Z", "+00:00"))
        busy_periods.append((
            time_to_minutes(start.hour, start.minute),
            time_to_minutes(end.hour, end.minute)
        ))

    return busy_periods


def find_available_slots(busy_periods: list, start_hour: str, end_hour: str, duration: int, buffer: int) -> list:
    """Find available slots given busy periods, within business hours."""
    sh, sm = parse_time(start_hour)
    eh, em = parse_time(end_hour)
    day_start = time_to_minutes(sh, sm)
    day_end = time_to_minutes(eh, em)

    busy_periods.sort()

    slots = []
    cursor = day_start

    for busy_start, busy_end in busy_periods:
        # Fill slots before this busy period
        while cursor + duration <= busy_start:
            slots.append({
                "start": minutes_to_str(cursor),
                "end": minutes_to_str(cursor + duration)
            })
            cursor += duration + buffer

        # Move cursor past busy period + buffer
        if cursor < busy_end + buffer:
            cursor = busy_end + buffer

    # Fill remaining slots after last busy period
    while cursor + duration <= day_end:
        slots.append({
            "start": minutes_to_str(cursor),
            "end": minutes_to_str(cursor + duration)
        })
        cursor += duration + buffer

    return slots


def main():
    parser = argparse.ArgumentParser(description="Query Google Calendar for available booking slots")
    parser.add_argument("--credentials", required=True, help="Path to credentials JSON (OAuth2 or Service Account)")
    parser.add_argument("--token", default=None, help="Path to OAuth2 token cache (for installed app flow)")
    parser.add_argument("--calendar-id", required=True, help="Google Calendar ID")
    parser.add_argument("--date", required=True, help="Date to query (YYYY-MM-DD)")
    parser.add_argument("--timezone", default="Asia/Taipei", help="Timezone")
    parser.add_argument("--start-hour", default="09:00", help="Business hours start (HH:MM)")
    parser.add_argument("--end-hour", default="18:00", help="Business hours end (HH:MM)")
    parser.add_argument("--duration", type=int, default=60, help="Slot duration in minutes")
    parser.add_argument("--buffer", type=int, default=15, help="Buffer between slots in minutes")
    parser.add_argument("--dry-run", action="store_true", help="Skip API call, return all possible slots")
    args = parser.parse_args()

    if args.dry_run:
        busy_periods = []
    else:
        creds = load_credentials(args.credentials, args.token)
        busy_periods = get_busy_periods(
            creds, args.calendar_id, args.date,
            args.timezone, args.start_hour, args.end_hour
        )

    slots = find_available_slots(
        busy_periods, args.start_hour, args.end_hour,
        args.duration, args.buffer
    )

    print(json.dumps(slots, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
