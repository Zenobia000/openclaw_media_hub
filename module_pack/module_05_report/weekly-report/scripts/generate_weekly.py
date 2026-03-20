#!/usr/bin/env python3
"""Generate a structured weekly report from daily briefs and metrics.

Usage:
    python3 generate_weekly.py \
        --dailies-json dailies.json \
        --metrics-json metrics.json \
        --risk-rules ../references/risk_rules.json \
        --week-range "2026-03-16 ~ 2026-03-20"

Output: JSON weekly report matching report_schema.json to stdout.
"""

import argparse
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate weekly report from dailies and metrics."
    )
    parser.add_argument(
        "--dailies-json",
        required=True,
        help="Path to JSON file containing daily brief records array",
    )
    parser.add_argument(
        "--metrics-json",
        required=True,
        help="Path to JSON file containing this_week/last_week metrics",
    )
    parser.add_argument(
        "--risk-rules",
        required=True,
        help="Path to risk_rules.json",
    )
    parser.add_argument(
        "--week-range",
        required=True,
        help="Week range string, e.g. '2026-03-16 ~ 2026-03-20'",
    )
    return parser.parse_args()


def load_json(path: str) -> dict | list:
    """Load and parse a JSON file."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# --- Highlights ---

def extract_highlights(dailies: list[dict], max_items: int = 5) -> list[str]:
    """Extract top highlights from daily brief records.

    Strategy:
    1. Take key_points[0] from each daily (top 1 per day)
    2. Deduplicate by simple substring check
    3. Keep up to max_items
    """
    if not dailies:
        return ["本週無日報紀錄"]

    candidates: list[str] = []
    for daily in dailies:
        key_points = daily.get("key_points", [])
        if key_points:
            candidates.append(key_points[0])

    # Deduplicate: skip if a candidate is a substring of an existing one
    unique: list[str] = []
    for candidate in candidates:
        is_dup = False
        for existing in unique:
            if candidate in existing or existing in candidate:
                is_dup = True
                break
        if not is_dup:
            unique.append(candidate)

    # Truncate each to 100 chars
    unique = [h[:100] for h in unique]

    # Pad to minimum 3 if we have dailies but few unique highlights
    if len(unique) < 3 and len(dailies) > 0:
        for daily in dailies:
            for point in daily.get("key_points", [])[1:]:
                if point not in unique and len(unique) < 3:
                    unique.append(point[:100])

    return unique[:max_items] if unique else ["本週無日報紀錄"]


# --- Metrics comparison ---

def calc_change_pct(current: float, previous: float) -> float | None:
    """Calculate percentage change. Returns None if previous is 0."""
    if previous == 0:
        return None
    return (current - previous) / previous


def format_change(current: int, previous: int) -> str:
    """Format a metric change as a human-readable string."""
    diff = current - previous
    pct = calc_change_pct(current, previous)
    sign = "+" if diff >= 0 else ""
    if pct is not None:
        return f"{sign}{diff} ({sign}{pct:.0%})"
    return f"{sign}{diff}"


# --- Risk identification ---

def identify_risks(metrics: dict, risk_rules: list[dict]) -> list[str]:
    """Evaluate risk rules against computed metrics and return triggered messages."""
    this_week = metrics.get("this_week", {})
    last_week = metrics.get("last_week", {})

    # Pre-compute derived metrics for rule evaluation
    tasks_total = this_week.get("tasks_total", 0)
    tasks_completed = this_week.get("tasks_completed", 0)
    task_completion_rate = tasks_completed / tasks_total if tasks_total > 0 else 1.0

    last_new_leads = last_week.get("new_leads", 0)
    this_new_leads = this_week.get("new_leads", 0)
    new_leads_change_pct = calc_change_pct(this_new_leads, last_new_leads)

    computed = {
        "task_completion_rate": task_completion_rate,
        "new_leads_change_pct": new_leads_change_pct if new_leads_change_pct is not None else 0.0,
        # These require richer data sources; default to 0 when unavailable
        "days_without_followup": this_week.get("days_without_followup", 0),
        "overdue_tasks_next_week": this_week.get("overdue_tasks_next_week", 0),
    }

    triggered: list[str] = []
    for rule in risk_rules:
        metric_name = rule["metric"]
        threshold = rule["threshold"]
        condition = rule["condition"]
        message = rule["message"]

        value = computed.get(metric_name)
        if value is None:
            continue

        if condition == "below" and value < threshold:
            triggered.append(message)
        elif condition == "above" and value > threshold:
            triggered.append(message)

    return triggered[:5]


# --- Next week todos ---

def generate_todos(dailies: list[dict], risks: list[str], metrics: dict) -> list[str]:
    """Derive next week's todos from incomplete tasks and risk items.

    Sources:
    1. Blockers / unfinished items mentioned in dailies
    2. Action items implied by risks
    3. Follow-up on low metrics
    """
    todos: list[str] = []

    # From dailies: look for blockers or tomorrow_plan from the last daily
    if dailies:
        last_daily = dailies[-1]
        for item in last_daily.get("blockers", []):
            todos.append(f"[延續] {item}")
        for item in last_daily.get("tomorrow_plan", []):
            todos.append(item)

    # From risks: add follow-up actions
    for risk in risks:
        todos.append(f"[風險跟進] {risk}")

    # If no todos generated, add a generic one
    if not todos:
        todos.append("回顧本週進度，規劃下週重點任務")

    return todos[:10]


# --- Main report generation ---

def generate_report(dailies: list[dict], metrics: dict,
                    risk_rules: list[dict], week_range: str) -> dict:
    """Assemble the complete weekly report structure."""
    this_week = metrics.get("this_week", {})

    highlights = extract_highlights(dailies)
    risks = identify_risks(metrics, risk_rules)
    todos = generate_todos(dailies, risks, metrics)

    # Ensure highlights has at least 3 items (schema minimum)
    while len(highlights) < 3:
        highlights.append("（無額外重點）")

    tz = timezone(timedelta(hours=8))  # Asia/Taipei
    generated_at = datetime.now(tz).isoformat()

    return {
        "title": "週報",
        "week_range": week_range,
        "highlights": highlights,
        "metrics": {
            "new_leads": this_week.get("new_leads", 0),
            "follow_ups": this_week.get("follow_ups", 0),
            "conversions": this_week.get("conversions", 0),
            "tasks_completed": this_week.get("tasks_completed", 0),
            "tasks_total": this_week.get("tasks_total", 0),
        },
        "next_week_todos": todos,
        "risks": risks,
        "generated_at": generated_at,
    }


def main() -> None:
    args = parse_args()

    try:
        dailies = load_json(args.dailies_json)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Error: failed to load dailies: {e}", file=sys.stderr)
        dailies = []

    try:
        metrics = load_json(args.metrics_json)
    except (json.JSONDecodeError, OSError) as e:
        print(f"Error: failed to load metrics: {e}", file=sys.stderr)
        metrics = {"this_week": {}, "last_week": {}}

    try:
        rules_data = load_json(args.risk_rules)
        risk_rules = rules_data.get("rules", [])
    except (json.JSONDecodeError, OSError) as e:
        print(f"Error: failed to load risk rules: {e}", file=sys.stderr)
        risk_rules = []

    report = generate_report(dailies, metrics, risk_rules, args.week_range)
    json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()
