#!/usr/bin/env python3
"""Parse schedule config YAML and check which tasks are due at a given time.

Output: JSON array of due tasks to stdout.
Dependencies: Python stdlib only (no pip install needed).
"""

import argparse
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Minimal YAML parser (handles the subset used by schedule_config.yaml)
# ---------------------------------------------------------------------------

def _parse_yaml_value(raw: str) -> Any:
    """Convert a raw YAML scalar string to a Python value."""
    stripped = raw.strip()
    if stripped in ("true", "True", "yes"):
        return True
    if stripped in ("false", "False", "no"):
        return False
    if stripped in ("null", "~", ""):
        return None
    # Remove surrounding quotes
    if (stripped.startswith('"') and stripped.endswith('"')) or \
       (stripped.startswith("'") and stripped.endswith("'")):
        return stripped[1:-1]
    # Try int / float
    try:
        return int(stripped)
    except ValueError:
        pass
    try:
        return float(stripped)
    except ValueError:
        pass
    return stripped


def _indent_level(line: str) -> int:
    return len(line) - len(line.lstrip())


def parse_simple_yaml(text: str) -> dict[str, Any]:
    """Very small YAML-subset parser sufficient for schedule_config.yaml.

    Supports: mappings, sequences (``- value`` and ``- key: value``),
    scalars, quoted strings, inline lists ``[a, b]``, env-var references,
    and comments.  Does NOT support anchors, merge keys, multi-line scalars,
    or flow mappings beyond inline lists.
    """
    lines: list[str] = []
    for raw_line in text.splitlines():
        # Strip comments (but not inside quotes)
        stripped = raw_line.rstrip()
        if not stripped or stripped.lstrip().startswith("#"):
            continue
        lines.append(stripped)

    def _parse_inline_list(s: str) -> list[Any]:
        """Parse ``[a, b, c]`` into a list."""
        inner = s.strip()[1:-1]
        items: list[Any] = []
        for part in inner.split(","):
            items.append(_parse_yaml_value(part))
        return items

    def _parse_block(idx: int, base_indent: int) -> tuple[Any, int]:
        """Recursively parse a YAML block starting at *idx*."""
        # Determine if this block is a sequence or mapping
        if idx >= len(lines):
            return {}, idx

        first_content = lines[idx].lstrip()
        if first_content.startswith("- "):
            # Sequence block
            result_list: list[Any] = []
            while idx < len(lines):
                line = lines[idx]
                ind = _indent_level(line)
                if ind < base_indent:
                    break
                if ind == base_indent and line.lstrip().startswith("- "):
                    item_text = line.lstrip()[2:]  # after "- "
                    if ":" in item_text and not item_text.strip().startswith("["):
                        # Mapping inside sequence item
                        item_dict: dict[str, Any] = {}
                        k, v = item_text.split(":", 1)
                        k = k.strip()
                        v = v.strip()
                        if v:
                            if v.startswith("[") and v.endswith("]"):
                                item_dict[k] = _parse_inline_list(v)
                            else:
                                item_dict[k] = _parse_yaml_value(v)
                        idx += 1
                        # Collect indented children of this sequence item
                        child_indent = base_indent + 2  # typical indent
                        if idx < len(lines):
                            child_indent = _indent_level(lines[idx])
                        while idx < len(lines) and _indent_level(lines[idx]) > base_indent:
                            cline = lines[idx]
                            cind = _indent_level(cline)
                            ccontent = cline.strip()
                            if ":" in ccontent and not ccontent.startswith("- "):
                                ck, cv = ccontent.split(":", 1)
                                ck = ck.strip()
                                cv = cv.strip()
                                if cv == "":
                                    # Sub-block
                                    idx += 1
                                    sub_val, idx = _parse_block(idx, cind + 2 if idx < len(lines) else cind + 2)
                                    item_dict[ck] = sub_val
                                elif cv.startswith("[") and cv.endswith("]"):
                                    item_dict[ck] = _parse_inline_list(cv)
                                    idx += 1
                                else:
                                    item_dict[ck] = _parse_yaml_value(cv)
                                    idx += 1
                            elif ccontent.startswith("- "):
                                # Sub-sequence
                                sub_list, idx = _parse_block(idx, cind)
                                # Attach to last key with empty value?
                                # Heuristic: find the last key added with list value
                                # Actually this should be handled above; skip for safety
                                # Just collect as unnamed
                                last_key = list(item_dict.keys())[-1] if item_dict else None
                                if last_key and item_dict[last_key] is None:
                                    item_dict[last_key] = sub_list
                                else:
                                    idx += 1  # skip unhandled
                            else:
                                idx += 1
                        result_list.append(item_dict)
                    else:
                        if item_text.startswith("[") and item_text.endswith("]"):
                            result_list.append(_parse_inline_list(item_text))
                        else:
                            result_list.append(_parse_yaml_value(item_text))
                        idx += 1
                else:
                    break
            return result_list, idx

        # Mapping block
        result_dict: dict[str, Any] = {}
        while idx < len(lines):
            line = lines[idx]
            ind = _indent_level(line)
            if ind < base_indent:
                break
            if ind > base_indent:
                idx += 1
                continue
            content = line.strip()
            if ":" not in content:
                idx += 1
                continue
            key, val = content.split(":", 1)
            key = key.strip()
            val = val.strip()
            if val == "":
                # Sub-block
                idx += 1
                if idx < len(lines):
                    next_ind = _indent_level(lines[idx])
                    sub_val, idx = _parse_block(idx, next_ind)
                    result_dict[key] = sub_val
                else:
                    result_dict[key] = None
            elif val.startswith("[") and val.endswith("]"):
                result_dict[key] = _parse_inline_list(val)
                idx += 1
            else:
                result_dict[key] = _parse_yaml_value(val)
                idx += 1

        return result_dict, idx

    result, _ = _parse_block(0, 0)
    return result if isinstance(result, dict) else {}


# ---------------------------------------------------------------------------
# Cron expression matcher
# ---------------------------------------------------------------------------

def _parse_cron_field(field: str, min_val: int, max_val: int) -> set[int]:
    """Parse a single cron field into a set of matching integer values.

    Supports: * (any), N (literal), N-M (range), N/S (step), N-M/S, */S,
    and comma-separated combinations.
    """
    values: set[int] = set()
    for part in field.split(","):
        part = part.strip()
        if "/" in part:
            base, step_str = part.split("/", 1)
            step = int(step_str)
            if base == "*":
                start, end = min_val, max_val
            elif "-" in base:
                start, end = (int(x) for x in base.split("-", 1))
            else:
                start, end = int(base), max_val
            values.update(range(start, end + 1, step))
        elif part == "*":
            values.update(range(min_val, max_val + 1))
        elif "-" in part:
            lo, hi = (int(x) for x in part.split("-", 1))
            values.update(range(lo, hi + 1))
        else:
            values.add(int(part))
    return values


def cron_matches(expression: str, dt: datetime) -> bool:
    """Return True if *expression* (5-field cron) matches *dt*."""
    fields = expression.split()
    if len(fields) != 5:
        return False

    minute_set = _parse_cron_field(fields[0], 0, 59)
    hour_set = _parse_cron_field(fields[1], 0, 23)
    dom_set = _parse_cron_field(fields[2], 1, 31)
    month_set = _parse_cron_field(fields[3], 1, 12)
    dow_set = _parse_cron_field(fields[4], 0, 7)

    # Normalise Sunday: both 0 and 7 mean Sunday (isoweekday 7 → 0)
    py_dow = dt.isoweekday() % 7  # Mon=1..Sat=6, Sun=0

    return (
        dt.minute in minute_set
        and dt.hour in hour_set
        and dt.day in dom_set
        and dt.month in month_set
        and py_dow in dow_set
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Check which scheduled tasks are due at a given time."
    )
    p.add_argument(
        "--config", required=True,
        help="Path to schedule_config.yaml",
    )
    p.add_argument(
        "--check-time", default=None,
        help="ISO 8601 datetime to check against (defaults to now).",
    )
    p.add_argument(
        "--timezone", default="Asia/Taipei",
        help="IANA timezone name. Only fixed-offset zones supported "
             "(default: Asia/Taipei = UTC+8).",
    )
    return p


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
    # Fallback: try to parse "+HH:MM" or just use UTC
    return timezone.utc


def main() -> None:
    args = build_parser().parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        print(json.dumps({"error": f"Config file not found: {config_path}"}),
              file=sys.stderr)
        sys.exit(1)

    config = parse_simple_yaml(config_path.read_text(encoding="utf-8"))

    tz = _resolve_tz(args.timezone)

    if args.check_time:
        # Parse ISO 8601 — support both offset-aware and naive
        raw = args.check_time
        try:
            check_dt = datetime.fromisoformat(raw)
        except ValueError:
            print(json.dumps({"error": f"Invalid --check-time: {raw}"}),
                  file=sys.stderr)
            sys.exit(1)
        if check_dt.tzinfo is None:
            check_dt = check_dt.replace(tzinfo=tz)
        else:
            check_dt = check_dt.astimezone(tz)
    else:
        check_dt = datetime.now(tz)

    tasks = config.get("tasks", [])
    if not isinstance(tasks, list):
        tasks = []

    due: list[dict[str, Any]] = []
    for task in tasks:
        if not isinstance(task, dict):
            continue
        schedule_expr = task.get("schedule", "")
        if not schedule_expr:
            continue
        if cron_matches(str(schedule_expr), check_dt):
            due.append({
                "name": task.get("name", ""),
                "skill": task.get("skill", ""),
                "params": task.get("params", {}),
            })

    print(json.dumps(due, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
