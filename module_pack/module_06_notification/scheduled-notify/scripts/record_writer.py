#!/usr/bin/env python3
"""Write a task execution record to file (JSONL) or Notion (stub).

Uses only Python stdlib. No pip install needed.
Output: JSON to stdout.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def write_to_file(record: dict[str, Any], output_dir: str) -> dict[str, Any]:
    """Append a JSON line to schedule_log.jsonl in *output_dir*."""
    out_path = Path(output_dir) / "schedule_log.jsonl"
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return {"status": "recorded", "location": str(out_path)}
    except OSError as exc:
        return {"status": "failed", "error": f"File write error: {exc}"}


def write_to_notion(record: dict[str, Any]) -> dict[str, Any]:
    """Stub for Notion integration. To be implemented in v2."""
    # TODO: Implement Notion API integration
    #   1. Read NOTION_API_KEY and NOTION_SCHEDULE_LOG_DB from env
    #   2. POST to https://api.notion.com/v1/pages with record properties
    #   3. Return {"status": "recorded", "location": "<notion_page_url>"}
    return {
        "status": "failed",
        "error": "Notion integration is not yet implemented (v2 feature). "
                 "Use --destination file instead.",
    }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Write task execution record to file or Notion."
    )
    p.add_argument("--task-name", required=True, help="Name of the executed task.")
    p.add_argument(
        "--task-type", required=True,
        help="Task type (report / crm_remind / calendar).",
    )
    p.add_argument(
        "--scheduled-at", required=True,
        help="Scheduled execution time (ISO 8601).",
    )
    p.add_argument(
        "--executed-at", required=True,
        help="Actual execution time (ISO 8601).",
    )
    p.add_argument(
        "--status", required=True,
        choices=["success", "failed", "retried_success", "retried_failed", "missed"],
        help="Execution status.",
    )
    p.add_argument(
        "--error-message", default=None,
        help="Error message (only for failed statuses).",
    )
    p.add_argument(
        "--output-location", default=None,
        help="Output location (URL or file path).",
    )
    p.add_argument(
        "--notification-sent", action="store_true", default=False,
        help="Flag indicating notification was sent.",
    )
    p.add_argument(
        "--destination", default="file", choices=["file", "notion"],
        help="Record destination (default: file).",
    )
    p.add_argument(
        "--output-dir", default=".",
        help="Directory for JSONL output (default: current directory).",
    )
    return p


def main() -> None:
    args = build_parser().parse_args()

    record: dict[str, Any] = {
        "task_name": args.task_name,
        "task_type": args.task_type,
        "scheduled_at": args.scheduled_at,
        "executed_at": args.executed_at,
        "status": args.status,
        "error_message": args.error_message,
        "output_location": args.output_location,
        "notification_sent": args.notification_sent,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }

    if args.destination == "file":
        result = write_to_file(record, args.output_dir)
    elif args.destination == "notion":
        result = write_to_notion(record)
    else:
        result = {"status": "failed", "error": f"Unknown destination: {args.destination}"}

    print(json.dumps(result, ensure_ascii=False))

    if result["status"] == "failed":
        sys.exit(1)


if __name__ == "__main__":
    main()
