#!/usr/bin/env python3
"""透過 Telegram Bot API 發送通知訊息。

用法：
    python3 tg_notify.py \
        --bot-token "123456:ABC-DEF" \
        --chat-id "987654321" \
        --message "升級通知：客戶詢問報價"

輸出：JSON 含 ok、message_id 或 error
"""

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request


def send_message(bot_token: str, chat_id: str, message: str,
                 parse_mode: str | None = None) -> dict:
    """透過 Telegram Bot API sendMessage 發送訊息。"""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": message,
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return {
                "ok": True,
                "message_id": body.get("result", {}).get("message_id"),
            }
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(error_body)
        except json.JSONDecodeError:
            detail = {"raw": error_body}

        # 429 Too Many Requests — 回傳 retry_after
        if e.code == 429:
            retry_after = detail.get("parameters", {}).get("retry_after", 30)
            return {
                "ok": False,
                "error": f"Rate limited. Retry after {retry_after}s",
                "retry_after": retry_after,
            }

        return {
            "ok": False,
            "error": f"HTTP {e.code}: {detail.get('description', error_body)}",
        }
    except urllib.error.URLError as e:
        return {
            "ok": False,
            "error": f"Connection error: {e.reason}",
        }


def main():
    parser = argparse.ArgumentParser(description="透過 Telegram Bot API 發送通知")
    parser.add_argument("--bot-token", required=True, help="Telegram Bot Token")
    parser.add_argument("--chat-id", required=True, help="目標 Chat ID")
    parser.add_argument("--message", required=True, help="訊息內容")
    parser.add_argument("--parse-mode", default=None,
                        choices=["HTML", "Markdown", "MarkdownV2"],
                        help="訊息格式（選填）")
    parser.add_argument("--dry-run", action="store_true",
                        help="僅輸出請求內容，不實際發送")
    args = parser.parse_args()

    if args.dry_run:
        result = {
            "dry_run": True,
            "bot_token": f"{args.bot_token[:8]}...",
            "chat_id": args.chat_id,
            "message": args.message,
            "parse_mode": args.parse_mode,
        }
    else:
        result = send_message(args.bot_token, args.chat_id, args.message,
                              args.parse_mode)

    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result.get("ok", result.get("dry_run")) else 1)


if __name__ == "__main__":
    main()
