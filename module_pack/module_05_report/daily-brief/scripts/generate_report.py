#!/usr/bin/env python3
"""Generate a structured report skeleton from search results.

Reads search results and builds a report structure matching report_schema.json.
Fills in metadata and formats sources; summary and key_points are set to
placeholder values for the Agent to fill in using prompt templates.

Outputs JSON report to stdout.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any


def load_json_file(path: str) -> Any:
    """Load and parse a JSON file."""
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(json.dumps({"error": f"File not found: {path}"}), file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as exc:
        print(json.dumps({"error": f"Invalid JSON in {path}: {exc}"}), file=sys.stderr)
        sys.exit(1)


def load_sources(sources_json: str) -> list[dict[str, str]]:
    """Load sources from a file path or stdin."""
    if sources_json == "-":
        raw = sys.stdin.read()
    else:
        raw = Path(sources_json).read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, list):
        print(json.dumps({"error": "sources-json must be a JSON array"}), file=sys.stderr)
        sys.exit(1)
    return data


def build_title(topic: str) -> str:
    """Build a report title from the topic."""
    return f"{topic} — 每日摘要"


def slugify(text: str) -> str:
    """Convert topic text to a filename-safe slug."""
    import re
    slug = re.sub(r"[^\w\u4e00-\u9fff]+", "_", text)
    return slug.strip("_").lower()


def format_sources(raw_sources: list[dict[str, str]]) -> list[dict[str, str]]:
    """Format raw search results into the schema's source structure."""
    formatted: list[dict[str, str]] = []
    for src in raw_sources:
        entry: dict[str, str] = {
            "title": src.get("title", ""),
            "url": src.get("url", ""),
        }
        if entry["title"] and entry["url"]:
            formatted.append(entry)
    return formatted


def generate_report(
    topic: str,
    date: str,
    output_format: str,
    sources: list[dict[str, str]],
    schema: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the report skeleton.

    The summary and key_points are placeholders — the Agent fills these in
    based on prompt_templates.md.
    """
    formatted_sources = format_sources(sources)
    now = datetime.now(timezone(timedelta(hours=8)))

    # Determine placeholder text based on format
    if not formatted_sources:
        summary_placeholder = "今日無相關新資訊。搜尋未返回與此主題相關的結果，建議稍後重試或調整搜尋關鍵字。" + "　" * 20
        key_points_placeholder = [
            "今日無相關新資訊",
            "建議調整搜尋關鍵字後重試",
            "可嘗試擴大搜尋範圍或更換資料來源",
        ]
    else:
        summary_placeholder = "[AGENT_FILL: 請根據 prompt_templates.md 中對應的 System Prompt，從搜尋結果生成 100-200 字摘要]"
        key_points_placeholder = [
            "[AGENT_FILL: 重點 1 — 不超過 80 字]",
            "[AGENT_FILL: 重點 2 — 不超過 80 字]",
            "[AGENT_FILL: 重點 3 — 不超過 80 字]",
        ]

    report: dict[str, Any] = {
        "title": build_title(topic),
        "date": date,
        "topic": topic,
        "summary": summary_placeholder,
        "key_points": key_points_placeholder,
        "sources": formatted_sources,
        "generated_at": now.isoformat(),
    }

    return report


def validate_against_schema(report: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    """Basic validation of report against schema. Returns list of issues."""
    issues: list[str] = []

    required_fields = schema.get("required", [])
    for field in required_fields:
        if field not in report:
            issues.append(f"Missing required field: {field}")

    if "key_points" in report:
        points = report["key_points"]
        min_items = schema.get("properties", {}).get("key_points", {}).get("minItems", 3)
        max_items = schema.get("properties", {}).get("key_points", {}).get("maxItems", 5)
        if len(points) < min_items:
            issues.append(f"key_points has {len(points)} items, minimum is {min_items}")
        if len(points) > max_items:
            issues.append(f"key_points has {len(points)} items, maximum is {max_items}")

    if "sources" in report:
        sources = report["sources"]
        max_sources = schema.get("properties", {}).get("sources", {}).get("maxItems", 10)
        if len(sources) > max_sources:
            issues.append(f"sources has {len(sources)} items, maximum is {max_sources}")

    return issues


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a structured report skeleton from search results.",
    )
    parser.add_argument(
        "--topic",
        required=True,
        help="Report topic (e.g. 'AI 產業動態')",
    )
    parser.add_argument(
        "--date",
        default=datetime.now().strftime("%Y-%m-%d"),
        help="Report date in YYYY-MM-DD format (default: today)",
    )
    parser.add_argument(
        "--format",
        dest="output_format",
        choices=["structured", "brief", "detailed"],
        default="structured",
        help="Output format (default: structured)",
    )
    parser.add_argument(
        "--schema",
        default=None,
        help="Path to report_schema.json for validation",
    )
    parser.add_argument(
        "--sources-json",
        required=True,
        help="Path to search results JSON file, or '-' for stdin",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args()

    try:
        sources = load_sources(args.sources_json)
        schema = load_json_file(args.schema) if args.schema else None

        report = generate_report(
            topic=args.topic,
            date=args.date,
            output_format=args.output_format,
            sources=sources,
            schema=schema,
        )

        # Validate if schema provided
        if schema:
            issues = validate_against_schema(report, schema)
            if issues:
                print(
                    json.dumps({"warnings": issues}, ensure_ascii=False),
                    file=sys.stderr,
                )

        print(json.dumps(report, ensure_ascii=False, indent=2))

    except Exception as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        sys.exit(1)
