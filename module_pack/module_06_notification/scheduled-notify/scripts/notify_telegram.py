#!/usr/bin/env python3
"""Send a Telegram notification via Bot API.

Uses only Python stdlib (urllib.request). Supports quiet-hours check.
Output: JSON to stdout.
"""

import argparse
import json
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from typing import Any


# ---------------------------------------------------------------------------
# Timezone helper (same compact mapping as scheduler.py)
# ---------------------------------------------------------------------------

_TZ_OFFSETS: dict[str, int] = {
    "Asia/Taipei": 8,
    "Asia/Tokyo": 9,
    "Asia/Shanghai": 8,
    "Asia/Hong_Kong": 8,
    "US/Eastern": -5,
    "US/Pacific": -8,
    "Europe/London": 0,
    "UTC": 0,
}


def _resolve_tz(name: str) -> timezone:
    hours = _TZ_OFFSETS.get(name)
    if hours is not None:
        return timezone(timedelta(hours=hours))
    return timezone.utc


# ---------------------------------------------------------------------------
# Quiet hours check
# ---------------------------------------------------------------------------

def _in_quiet_hours(
    now: datetime,
    quiet_start: str | None,
    quiet_end: str | None,
) -> bool:
    """Return True if *now* falls within the quiet window.

    Handles overnight ranges like 23:00 - 07:00.
    """
    if not quiet_start or not quiet_end:
        return False
    start_h, start_m = (int(x) for x in quiet_start.split(":"))
    end_h, end_m = (int(x) for x in quiet_end.split(":"))

    start_minutes = start_h * 60 + start_m
    end_minutes = end_h * 60 + end_m
    now_minutes = now.hour * 60 + now.minute

    if start_minutes <= end_minutes:
        # Same-day range (e.g. 01:00 - 06:00)
        return start_minutes <= now_minutes < end_minutes
    else:
        # Overnight range (e.g. 23:00 - 07:00)
        return now_minutes >= start_minutes or now_minutes < end_minutes


# ---------------------------------------------------------------------------
# Telegram API
# ---------------------------------------------------------------------------

def send_telegram_message(
    bot_token: str,
    chat_id: str,
    message: str,
    parse_mode: str = "Markdown",
) -> dict[str, Any]:
    """Call Telegram Bot API sendMessage. Return parsed response."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id,
        "text": message,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("ok"):
                return {
                    "status": "sent",
                    "message_id": data["result"]["message_id"],
                }
            return {
                "status": "failed",
                "error": data.get("description", "Unknown Telegram error"),
            }
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return {"status": "failed", "error": f"HTTP {exc.code}: {body}"}
    except urllib.error.URLError as exc:
        return {"status": "failed", "error": str(exc.reason)}
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Send Telegram notification.")
    p.add_argument("--bot-token", required=True, help="Telegram Bot token.")
    p.add_argument("--chat-id", required=True, help="Telegram chat ID.")
    p.add_argument("--message", required=True, help="Message text to send.")
    p.add_argument(
        "--parse-mode", default="Markdown",
        choices=["Markdown", "MarkdownV2", "HTML"],
        help="Telegram parse mode (default: Markdown).",
    )
    p.add_argument("--quiet-start", default=None, help="Quiet hours start (HH:MM).")
    p.add_argument("--quiet-end", default=None, help="Quiet hours end (HH:MM).")
    p.add_argument("--timezone", default="Asia/Taipei", help="Timezone for quiet hours.")
    return p


def main() -> None:
    args = build_parser().parse_args()

    tz = _resolve_tz(args.timezone)
    now = datetime.now(tz)

    if _in_quiet_hours(now, args.quiet_start, args.quiet_end):
        result = {"status": "queued", "reason": "quiet_hours"}
        print(json.dumps(result, ensure_ascii=False))
        return

    result = send_telegram_message(
        bot_token=args.bot_token,
        chat_id=args.chat_id,
        message=args.message,
        parse_mode=args.parse_mode,
    )
    print(json.dumps(result, ensure_ascii=False))

    if result["status"] == "failed":
        sys.exit(1)


if __name__ == "__main__":
    main()
