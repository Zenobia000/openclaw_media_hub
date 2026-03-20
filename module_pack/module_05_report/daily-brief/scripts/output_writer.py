#!/usr/bin/env python3
"""Write a daily brief report to file, Notion, or Google Sheets.

File mode writes both JSON and Markdown versions.
Notion and Sheets modes are stubs with clear TODO markers.

Outputs JSON with {status, location} to stdout.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


def load_report(input_path: str) -> dict[str, Any]:
    """Load report JSON from a file path or stdin."""
    if input_path == "-":
        raw = sys.stdin.read()
    else:
        raw = Path(input_path).read_text(encoding="utf-8")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(json.dumps({"error": f"Invalid JSON: {exc}"}), file=sys.stderr)
        sys.exit(1)
    if not isinstance(data, dict):
        print(json.dumps({"error": "Report must be a JSON object"}), file=sys.stderr)
        sys.exit(1)
    return data


def slugify(text: str) -> str:
    """Convert text to a filename-safe slug."""
    slug = re.sub(r"[^\w\u4e00-\u9fff]+", "_", text)
    return slug.strip("_").lower()


def report_to_markdown(report: dict[str, Any]) -> str:
    """Convert a report JSON object to Markdown format."""
    lines: list[str] = []

    title = report.get("title", "Daily Brief")
    date = report.get("date", "")
    topic = report.get("topic", "")
    summary = report.get("summary", "")
    key_points: list[str] = report.get("key_points", [])
    sources: list[dict[str, str]] = report.get("sources", [])
    generated_at = report.get("generated_at", "")

    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"**Date:** {date}")
    lines.append(f"**Topic:** {topic}")
    lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append(summary)
    lines.append("")

    lines.append("## Key Points")
    lines.append("")
    for i, point in enumerate(key_points, 1):
        lines.append(f"{i}. {point}")
    lines.append("")

    if sources:
        lines.append("## Sources")
        lines.append("")
        for src in sources:
            src_title = src.get("title", "")
            src_url = src.get("url", "")
            if src_url:
                lines.append(f"- [{src_title}]({src_url})")
            else:
                lines.append(f"- {src_title}")
        lines.append("")

    lines.append(f"---")
    lines.append(f"Generated at: {generated_at}")
    lines.append("")

    return "\n".join(lines)


def write_to_file(
    report: dict[str, Any],
    output_path: str,
) -> dict[str, str]:
    """Write report as JSON and Markdown files."""
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    topic_slug = slugify(report.get("topic", "report"))
    date = report.get("date", "unknown")
    base_name = f"daily_brief_{date}_{topic_slug}"

    json_path = output_dir / f"{base_name}.json"
    md_path = output_dir / f"{base_name}.md"

    # Write JSON
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    # Write Markdown
    md_content = report_to_markdown(report)
    md_path.write_text(md_content, encoding="utf-8")

    return {
        "status": "success",
        "location": str(json_path.resolve()),
        "files": {
            "json": str(json_path.resolve()),
            "markdown": str(md_path.resolve()),
        },
    }


def write_to_notion(report: dict[str, Any]) -> dict[str, str]:
    """Write report to Notion page.

    TODO: Implement Notion integration.
    Requirements:
    - NOTION_API_KEY environment variable
    - NOTION_DATABASE_ID environment variable
    - pip install notion-client

    Steps:
    1. Initialize Notion client with API key
    2. Create a new page in the target database
    3. Map report fields to Notion page properties:
       - title -> Page title
       - date -> Date property
       - summary -> Rich text block
       - key_points -> Bulleted list blocks
       - sources -> Bookmark blocks
    4. Return the page URL
    """
    return {
        "status": "not_implemented",
        "location": "",
        "message": "Notion integration not yet implemented. Set NOTION_API_KEY and NOTION_DATABASE_ID environment variables, then implement the write_to_notion function.",
    }


def write_to_sheets(report: dict[str, Any]) -> dict[str, str]:
    """Write report to Google Sheets.

    TODO: Implement Google Sheets integration.
    Requirements:
    - Google Sheets API credentials (service account or OAuth2)
    - SHEETS_SPREADSHEET_ID environment variable
    - pip install google-api-python-client google-auth

    Steps:
    1. Authenticate with Google Sheets API
    2. Append a row to the target spreadsheet:
       [date, topic, title, summary, key_points_joined, sources_count, generated_at]
    3. Return the spreadsheet URL
    """
    return {
        "status": "not_implemented",
        "location": "",
        "message": "Google Sheets integration not yet implemented. Set up Sheets API credentials and SHEETS_SPREADSHEET_ID environment variable, then implement the write_to_sheets function.",
    }


def write_report(
    report: dict[str, Any],
    destination: str,
    output_path: str,
) -> dict[str, Any]:
    """Route report to the correct output destination."""
    if destination == "file":
        return write_to_file(report, output_path)
    elif destination == "notion":
        return write_to_notion(report)
    elif destination == "sheets":
        return write_to_sheets(report)
    else:
        return {
            "status": "error",
            "message": f"Unknown destination: {destination}. Supported: file, notion, sheets",
        }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Write a daily brief report to file, Notion, or Google Sheets.",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to report JSON file, or '-' for stdin",
    )
    parser.add_argument(
        "--destination",
        choices=["file", "notion", "sheets"],
        default="file",
        help="Output destination (default: file)",
    )
    parser.add_argument(
        "--output-path",
        default=".",
        help="Output directory for file mode (default: current directory)",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args()

    try:
        report = load_report(args.input)
        result = write_report(
            report=report,
            destination=args.destination,
            output_path=args.output_path,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))

    except Exception as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        sys.exit(1)
