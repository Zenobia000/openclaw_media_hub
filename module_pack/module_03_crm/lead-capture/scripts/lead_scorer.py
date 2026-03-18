#!/usr/bin/env python3
"""Lead 評分計算器。

純運算，無 API 依賴。根據四個維度（來源管道、需求明確度、互動頻率、客戶規模）
的等級輸入，計算加權總分並輸出優先級。

用法：
    python3 lead_scorer.py \
        --lead-json '{"source":"high","needs_clarity":"high","interaction_frequency":"medium","client_scale":"high"}' \
        --config path/to/lead_score_config.json

輸出：JSON 格式（stdout）。
"""

import argparse
import json
import sys
from datetime import datetime, timezone, timedelta


FOLLOWUP_DAYS = {"high": 1, "medium": 3, "low": 7}

DIMENSION_NAMES_ZH = {
    "source": "來源",
    "needs_clarity": "需求",
    "interaction_frequency": "互動",
    "client_scale": "規模",
}


def compute_score(lead: dict, config: dict) -> dict:
    """計算 lead score 並回傳結構化結果。"""
    dimensions = config["dimensions"]
    thresholds = config["priority_thresholds"]

    breakdown = {}
    total = 0

    for dim_key, dim_cfg in dimensions.items():
        level = lead.get(dim_key, dim_cfg.get("default", "medium"))
        if level not in dim_cfg["levels"]:
            level = dim_cfg.get("default", "medium")
        score = dim_cfg["levels"][level]["score"]
        breakdown[dim_key] = {
            "level": level,
            "score": score,
            "max_score": dim_cfg["max_score"],
            "weight": dim_cfg["weight"],
        }
        total += score

    # 決定優先級
    priority_label = "low"
    priority_zh = thresholds["low"]["label"]
    for key in ("high", "medium", "low"):
        t = thresholds[key]
        if t["min"] <= total <= t["max"]:
            priority_label = key
            priority_zh = t["label"]
            break

    followup_days = FOLLOWUP_DAYS.get(priority_label, 7)

    # 產生 score_log
    now = datetime.now(timezone(timedelta(hours=8)))
    parts = " + ".join(
        f"{DIMENSION_NAMES_ZH[k]}:{breakdown[k]['score']}" for k in dimensions
    )
    score_log = (
        f"[{now.strftime('%Y-%m-%d %H:%M')}] Lead Score: {total} 分"
        f"（{parts}）→ 優先級：{priority_zh}"
    )

    return {
        "ok": True,
        "total_score": total,
        "priority": priority_zh,
        "priority_label": priority_label,
        "followup_days": followup_days,
        "breakdown": breakdown,
        "score_log": score_log,
    }


def main():
    parser = argparse.ArgumentParser(description="Lead 評分計算器")
    parser.add_argument(
        "--lead-json",
        required=True,
        help='JSON 字串，含四維度等級。例如：\'{"source":"high","needs_clarity":"high","interaction_frequency":"medium","client_scale":"high"}\'',
    )
    parser.add_argument(
        "--config",
        required=True,
        help="lead_score_config.json 路徑",
    )
    args = parser.parse_args()

    try:
        lead = json.loads(args.lead_json)
    except json.JSONDecodeError as e:
        print(json.dumps({"ok": False, "error": f"無效的 lead JSON：{e}"}, ensure_ascii=False))
        sys.exit(1)

    try:
        with open(args.config, "r", encoding="utf-8") as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(json.dumps({"ok": False, "error": f"無法載入設定檔：{e}"}, ensure_ascii=False))
        sys.exit(1)

    result = compute_score(lead, config)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(0 if result.get("ok") else 1)


if __name__ == "__main__":
    main()
