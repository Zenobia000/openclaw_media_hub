#!/usr/bin/env python3
"""Collect this week's daily brief records from various sources.

Usage:
    python3 collect_dailies.py \
        --source local \
        --week-start 2026-03-16 \
        --week-end 2026-03-20 \
        --data-dir ./data/daily_briefs

Output: JSON array of daily brief records to stdout.
"""

import argparse
import glob
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Collect daily brief records for a given week."
    )
    parser.add_argument(
        "--source",
        choices=["notion", "sheets", "local"],
        default="local",
        help="Data source type (default: local)",
    )
    parser.add_argument(
        "--week-start",
        required=True,
        help="Week start date, format: YYYY-MM-DD",
    )
    parser.add_argument(
        "--week-end",
        required=True,
        help="Week end date, format: YYYY-MM-DD",
    )
    parser.add_argument(
        "--data-dir",
        default=".",
        help="Directory containing daily brief JSON files (local mode)",
    )
    return parser.parse_args()


def collect_local(data_dir: str, week_start: str, week_end: str) -> list[dict]:
    """Read daily_brief_YYYY-MM-DD_*.json files from data_dir within date range."""
    start = datetime.strptime(week_start, "%Y-%m-%d").date()
    end = datetime.strptime(week_end, "%Y-%m-%d").date()
    data_path = Path(data_dir)

    if not data_path.is_dir():
        print(f"Warning: data directory not found: {data_dir}", file=sys.stderr)
        return []

    records: list[dict] = []
    current = start
    while current <= end:
        date_str = current.strftime("%Y-%m-%d")
        pattern = str(data_path / f"daily_brief_{date_str}_*.json")
        matched_files = sorted(glob.glob(pattern))

        for file_path in matched_files:
            try:
                with open(file_path, encoding="utf-8") as f:
                    data = json.load(f)
                records.append(data)
            except (json.JSONDecodeError, OSError) as e:
                print(f"Warning: failed to read {file_path}: {e}", file=sys.stderr)

        current += timedelta(days=1)

    return records


def collect_notion(week_start: str, week_end: str) -> list[dict]:
    """Collect daily briefs from Notion database."""
    # TODO: Implement Notion API integration
    # 1. Query Notion database with date filter (week_start <= date <= week_end)
    # 2. Parse page properties into daily brief format
    # 3. Return list of records
    print("Warning: Notion source not yet implemented, returning empty list", file=sys.stderr)
    return []


def collect_sheets(week_start: str, week_end: str) -> list[dict]:
    """Collect daily briefs from Google Sheets."""
    # TODO: Implement Google Sheets API integration
    # 1. Read rows from configured sheet/tab
    # 2. Filter by date range
    # 3. Parse into daily brief format
    # 4. Return list of records
    print("Warning: Sheets source not yet implemented, returning empty list", file=sys.stderr)
    return []


def main() -> None:
    args = parse_args()

    if args.source == "local":
        records = collect_local(args.data_dir, args.week_start, args.week_end)
    elif args.source == "notion":
        records = collect_notion(args.week_start, args.week_end)
    elif args.source == "sheets":
        records = collect_sheets(args.week_start, args.week_end)
    else:
        print(f"Error: unsupported source: {args.source}", file=sys.stderr)
        sys.exit(1)

    json.dump(records, sys.stdout, ensure_ascii=False, indent=2)
    print()  # trailing newline


if __name__ == "__main__":
    main()
