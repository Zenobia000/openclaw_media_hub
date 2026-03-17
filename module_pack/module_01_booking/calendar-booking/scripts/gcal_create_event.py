#!/usr/bin/env python3
"""Create a Google Calendar event.

Supports two credential types:
  1. OAuth2 Desktop (installed) app — requires initial browser auth
  2. Service Account — headless, no browser needed

Usage:
    # OAuth2 Desktop App
    python3 gcal_create_event.py \
        --credentials client_secret_xxx.json \
        --token token.json \
        --calendar-id primary \
        --title "桑尼工作室 - 王小明 預約" \
        --start "2026-03-18T14:00:00" \
        --end "2026-03-18T15:00:00" \
        --timezone "Asia/Taipei"

Output: JSON with event_id and calendar_link, e.g.:
    {
        "event_id": "abc123xyz",
        "calendar_link": "https://calendar.google.com/event?eid=...",
        "status": "confirmed"
    }
"""

import argparse
import json
import os
import sys

SCOPES = ["https://www.googleapis.com/auth/calendar"]


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
                if os.environ.get("DISPLAY") or os.environ.get("BROWSER"):
                    try:
                        creds = flow.run_local_server(port=0, open_browser=False)
                    except Exception:
                        creds = None
                if not creds or not getattr(creds, 'token', None):
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


def create_event(
    creds,
    calendar_id: str,
    title: str,
    start: str,
    end: str,
    timezone: str,
    description: str = "",
    attendees: list[str] | None = None,
) -> dict:
    """Create a Google Calendar event and return event details."""
    from googleapiclient.discovery import build

    service = build("calendar", "v3", credentials=creds)

    event_body = {
        "summary": title,
        "start": {
            "dateTime": start,
            "timeZone": timezone,
        },
        "end": {
            "dateTime": end,
            "timeZone": timezone,
        },
    }

    if description:
        event_body["description"] = description

    if attendees:
        event_body["attendees"] = [{"email": e.strip()} for e in attendees if e.strip()]

    event = service.events().insert(
        calendarId=calendar_id,
        body=event_body,
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


def main():
    parser = argparse.ArgumentParser(description="Create a Google Calendar event")
    parser.add_argument("--credentials", required=True, help="Path to credentials JSON (OAuth2 or Service Account)")
    parser.add_argument("--token", default=None, help="Path to OAuth2 token cache (for installed app flow)")
    parser.add_argument("--calendar-id", required=True, help="Google Calendar ID")
    parser.add_argument("--title", required=True, help="Event title/summary")
    parser.add_argument("--start", required=True, help="Start time (ISO-8601)")
    parser.add_argument("--end", required=True, help="End time (ISO-8601)")
    parser.add_argument("--timezone", default="Asia/Taipei", help="Timezone")
    parser.add_argument("--description", default="", help="Event description/notes")
    parser.add_argument("--attendees", default="", help="Comma-separated attendee emails")
    parser.add_argument("--dry-run", action="store_true", help="Print event body without creating")
    args = parser.parse_args()

    attendees = [e.strip() for e in args.attendees.split(",") if e.strip()] if args.attendees else []

    if args.dry_run:
        event_body = {
            "summary": args.title,
            "start": {"dateTime": args.start, "timeZone": args.timezone},
            "end": {"dateTime": args.end, "timeZone": args.timezone},
        }
        if args.description:
            event_body["description"] = args.description
        if attendees:
            event_body["attendees"] = [{"email": e} for e in attendees]
        print(json.dumps({
            "dry_run": True,
            "event_body": event_body,
            "event_id": "dry-run-id",
            "calendar_link": "https://calendar.google.com/event?eid=dry-run",
            "status": "confirmed",
        }, indent=2, ensure_ascii=False))
    else:
        creds = load_credentials(args.credentials, args.token)
        result = create_event(
            creds, args.calendar_id, args.title,
            args.start, args.end, args.timezone,
            args.description, attendees
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
