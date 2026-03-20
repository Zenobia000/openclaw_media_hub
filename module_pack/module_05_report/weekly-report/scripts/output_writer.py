#!/usr/bin/env python3
"""Write weekly report to file, Notion, or Google Sheets.

Usage:
    python3 output_writer.py \
        --input weekly_report.json \
        --destination file \
        --output-path ./output/weekly_report_2026-03-20.json

Output: JSON status object to stdout.
"""

import argparse
import json
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Write weekly report to various destinations."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to weekly report JSON file, or '-' for stdin",
    )
    parser.add_argument(
        "--destination",
        choices=["file", "notion", "sheets"],
        default="file",
        help="Output destination (default: file)",
    )
    parser.add_argument(
        "--output-path",
        default=None,
        help="Output file path (file mode). Markdown is written alongside with .md extension.",
    )
    return parser.parse_args()


def load_report(input_path: str) -> dict:
    """Load the weekly report JSON."""
    if input_path == "-":
        return json.load(sys.stdin)
    with open(input_path, encoding="utf-8") as f:
        return json.load(f)


def format_change_str(current: int, last: int) -> str:
    """Format a metric change column."""
    diff = current - last
    sign = "+" if diff >= 0 else ""
    return f"{sign}{diff}"


def report_to_markdown(report: dict) -> str:
    """Convert weekly report JSON to a readable Markdown string."""
    lines: list[str] = []
    week_range = report.get("week_range", "N/A")
    lines.append(f"# 週報：{week_range}")
    lines.append("")

    # Highlights
    lines.append("## 本週重點摘要")
    lines.append("")
    for i, h in enumerate(report.get("highlights", []), 1):
        lines.append(f"{i}. {h}")
    lines.append("")

    # Metrics
    metrics = report.get("metrics", {})
    lines.append("## 業務數據")
    lines.append("")
    lines.append("| 指標 | 本週 | 完成率 |")
    lines.append("|------|------|--------|")
    lines.append(f"| 新 Lead 數 | {metrics.get('new_leads', 0)} | — |")
    lines.append(f"| 跟進數 | {metrics.get('follow_ups', 0)} | — |")
    lines.append(f"| 成交數 | {metrics.get('conversions', 0)} | — |")

    tasks_completed = metrics.get("tasks_completed", 0)
    tasks_total = metrics.get("tasks_total", 0)
    completion = f"{tasks_completed / tasks_total * 100:.0f}%" if tasks_total > 0 else "N/A"
    lines.append(f"| 任務完成 | {tasks_completed}/{tasks_total} | {completion} |")
    lines.append("")

    # Todos
    lines.append("## 下週待辦事項")
    lines.append("")
    for todo in report.get("next_week_todos", []):
        lines.append(f"- [ ] {todo}")
    lines.append("")

    # Risks
    risks = report.get("risks", [])
    if risks:
        lines.append("## 風險提醒")
        lines.append("")
        for risk in risks:
            lines.append(f"- {risk}")
        lines.append("")

    lines.append(f"*生成時間：{report.get('generated_at', 'N/A')}*")
    lines.append("")

    return "\n".join(lines)


def write_file(report: dict, output_path: str) -> dict:
    """Write report as JSON and Markdown files."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
        f.write("\n")

    # Write Markdown alongside
    md_path = out.with_suffix(".md")
    md_content = report_to_markdown(report)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    return {
        "status": "ok",
        "destination": "file",
        "json_path": str(out),
        "markdown_path": str(md_path),
    }


def write_notion(report: dict) -> dict:
    """Write report to Notion page."""
    # TODO: Implement Notion API integration
    # 1. Create or update a Notion page with report content
    # 2. Map report fields to Notion blocks
    print("Warning: Notion destination not yet implemented", file=sys.stderr)
    return {"status": "error", "destination": "notion", "message": "not implemented"}


def write_sheets(report: dict) -> dict:
    """Write report to Google Sheets."""
    # TODO: Implement Google Sheets API integration
    # 1. Append report data to configured sheet
    # 2. Format cells as needed
    print("Warning: Sheets destination not yet implemented", file=sys.stderr)
    return {"status": "error", "destination": "sheets", "message": "not implemented"}


def main() -> None:
    args = parse_args()

    try:
        report = load_report(args.input)
    except (json.JSONDecodeError, OSError) as e:
        result = {"status": "error", "message": f"Failed to load report: {e}"}
        json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
        print()
        sys.exit(1)

    if args.destination == "file":
        if not args.output_path:
            print("Error: --output-path is required for file destination", file=sys.stderr)
            sys.exit(1)
        result = write_file(report, args.output_path)
    elif args.destination == "notion":
        result = write_notion(report)
    elif args.destination == "sheets":
        result = write_sheets(report)
    else:
        result = {"status": "error", "message": f"Unsupported destination: {args.destination}"}

    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()
