#!/usr/bin/env python3
"""Collect CRM and task metrics for weekly report comparison.

Usage:
    python3 collect_metrics.py \
        --source local \
        --week-start 2026-03-16 --week-end 2026-03-20 \
        --last-week-start 2026-03-09 --last-week-end 2026-03-13

Output: JSON with {"this_week": {...}, "last_week": {...}} to stdout.
"""

import argparse
import json
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect CRM + task metrics for this week and last week."
    )
    parser.add_argument(
        "--source",
        choices=["notion", "sheets", "local"],
        default="local",
        help="Data source type (default: local)",
    )
    parser.add_argument("--week-start", required=True, help="This week start, YYYY-MM-DD")
    parser.add_argument("--week-end", required=True, help="This week end, YYYY-MM-DD")
    parser.add_argument("--last-week-start", required=True, help="Last week start, YYYY-MM-DD")
    parser.add_argument("--last-week-end", required=True, help="Last week end, YYYY-MM-DD")
    parser.add_argument(
        "--metrics-file",
        default=None,
        help="Path to local metrics JSON file (local mode)",
    )
    return parser.parse_args()


def empty_metrics() -> dict:
    """Return a metrics object with all zeros."""
    return {
        "new_leads": 0,
        "follow_ups": 0,
        "conversions": 0,
        "tasks_completed": 0,
        "tasks_total": 0,
    }


def collect_local(metrics_file: str | None, week_start: str, week_end: str,
                   last_week_start: str, last_week_end: str) -> dict:
    """Read metrics from a local JSON file.

    Expected file format:
    {
      "weeks": {
        "2026-03-16": {"new_leads": 10, "follow_ups": 5, "conversions": 2,
                       "tasks_completed": 15, "tasks_total": 20},
        "2026-03-09": { ... }
      }
    }

    Keys are week-start dates (YYYY-MM-DD).
    """
    if not metrics_file:
        print("Warning: no --metrics-file provided, returning zeros", file=sys.stderr)
        return {"this_week": empty_metrics(), "last_week": empty_metrics()}

    path = Path(metrics_file)
    if not path.is_file():
        print(f"Warning: metrics file not found: {metrics_file}", file=sys.stderr)
        return {"this_week": empty_metrics(), "last_week": empty_metrics()}

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Error: failed to read metrics file: {e}", file=sys.stderr)
        return {"this_week": empty_metrics(), "last_week": empty_metrics()}

    weeks = data.get("weeks", {})
    this_week = weeks.get(week_start, empty_metrics())
    last_week = weeks.get(last_week_start, empty_metrics())

    # Ensure all required keys exist
    for key in empty_metrics():
        this_week.setdefault(key, 0)
        last_week.setdefault(key, 0)

    return {"this_week": this_week, "last_week": last_week}


def collect_notion(week_start: str, week_end: str,
                   last_week_start: str, last_week_end: str) -> dict:
    """Collect metrics from Notion databases."""
    # TODO: Implement Notion API integration
    # 1. Query CRM database for this_week and last_week date ranges
    # 2. Count new_leads, follow_ups, conversions
    # 3. Query task database for completed/total counts
    print("Warning: Notion source not yet implemented, returning zeros", file=sys.stderr)
    return {"this_week": empty_metrics(), "last_week": empty_metrics()}


def collect_sheets(week_start: str, week_end: str,
                   last_week_start: str, last_week_end: str) -> dict:
    """Collect metrics from Google Sheets."""
    # TODO: Implement Google Sheets API integration
    # 1. Read CRM sheet rows, filter by date range
    # 2. Aggregate metrics for this_week and last_week
    print("Warning: Sheets source not yet implemented, returning zeros", file=sys.stderr)
    return {"this_week": empty_metrics(), "last_week": empty_metrics()}


def main() -> None:
    args = parse_args()

    if args.source == "local":
        result = collect_local(
            args.metrics_file, args.week_start, args.week_end,
            args.last_week_start, args.last_week_end,
        )
    elif args.source == "notion":
        result = collect_notion(
            args.week_start, args.week_end,
            args.last_week_start, args.last_week_end,
        )
    elif args.source == "sheets":
        result = collect_sheets(
            args.week_start, args.week_end,
            args.last_week_start, args.last_week_end,
        )
    else:
        print(f"Error: unsupported source: {args.source}", file=sys.stderr)
        sys.exit(1)

    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()
