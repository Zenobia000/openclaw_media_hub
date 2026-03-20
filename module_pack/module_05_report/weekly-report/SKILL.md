---
name: weekly-report
description: "每週自動彙整日報、CRM 數據、任務完成情況，生成結構化週報。
  含業務數據週環比、風險識別、下週待辦推導。
  適用時機：使用者要求產出週報、本週總結，
  或提及關鍵字如 週報、weekly report、本週摘要、這週總結、幫我產週報。
  不適用：每日摘要（使用 daily-brief）、月報（目前不支援）、
  即時數據查詢、歷史趨勢分析。
  前置需求：daily-brief skill 已運作。CRM 資料（Module 03）為選配。"
metadata:
  openclaw:
    emoji: "📊"
    requires:
      bins: ["python3"]
---

# Weekly Report Skill

## 概述

完整週報流程：收集日報 → 收集指標 → 生成重點摘要 → 與上週比較 → 識別風險 → 推導下週待辦 → 輸出報告。

## 設定

每次週報流程開始時載入 `references/report_schema.json` 與 `references/risk_rules.json`，包含：

| 檔案 | 說明 |
|------|------|
| `report_schema.json` | 週報輸出結構定義，所有欄位與型別約束 |
| `risk_rules.json` | 風險識別規則，定義指標閾值與嚴重等級 |
| `prompt_templates.md` | 週報彙整 Prompt 模板（System / User / 輸出範例） |

## 資料來源

| 資料來源 | 取得方式 | 資料內容 |
|----------|----------|----------|
| **本週 daily_brief 紀錄** | 從 Notion / Google Sheets / 本地 JSON 檔讀取 | 每日重點摘要、趨勢變化 |
| **CRM 數據（Module 03）** | 從 CRM 模組的 Notion / Sheets / 本地檔案讀取 | 新 Lead 數、跟進數、成交數 |
| **任務清單** | 從任務管理工具或本地檔案讀取 | 任務完成數、任務總數、未完成項目 |

本地模式下，daily_brief 紀錄以 `daily_brief_YYYY-MM-DD_*.json` 格式存放於 `--data-dir` 目錄；CRM 與任務數據以 JSON 檔提供。

## 工作流程

### Step 1：計算週日期範圍

根據當前日期或使用者指定日期，計算本週（週一 ~ 週五）與上週的日期範圍。

### Step 2：收集本週日報

```bash
python3 {skill_dir}/scripts/collect_dailies.py \
  --source local \
  --week-start "{YYYY-MM-DD}" \
  --week-end "{YYYY-MM-DD}" \
  --data-dir "{path_to_daily_briefs}"
```

輸出：JSON 陣列，包含本週所有 daily_brief 紀錄。

### Step 3：收集業務指標

```bash
python3 {skill_dir}/scripts/collect_metrics.py \
  --source local \
  --week-start "{YYYY-MM-DD}" \
  --week-end "{YYYY-MM-DD}" \
  --last-week-start "{YYYY-MM-DD}" \
  --last-week-end "{YYYY-MM-DD}"
```

輸出：JSON 物件，包含 `this_week` 與 `last_week` 的 CRM 和任務指標。

### Step 4：生成週報

```bash
python3 {skill_dir}/scripts/generate_weekly.py \
  --dailies-json "{dailies_output}" \
  --metrics-json "{metrics_output}" \
  --risk-rules "{skill_dir}/references/risk_rules.json" \
  --week-range "{YYYY-MM-DD} ~ {YYYY-MM-DD}"
```

輸出：完整 JSON 週報，結構符合 `report_schema.json`。

### Step 5：輸出報告

```bash
python3 {skill_dir}/scripts/output_writer.py \
  --input "{weekly_report_json}" \
  --destination file \
  --output-path "{output_dir}/weekly_report_{YYYY-MM-DD}.json"
```

輸出 JSON 與 Markdown 兩種格式。

## 數據彙整規則

### 重點摘要生成邏輯

1. 從本週日報中，提取每份日報的 Top 1 重點（`key_points[0]`）
2. 合併重複主題（相似度高的合併為一條）
3. 按重要性排序，保留 3-5 條
4. 每條重點不超過 100 字

### 業務數據計算

| 指標 | 計算方式 |
|------|----------|
| 新 Lead 數 | CRM 中本週新增的 lead 筆數 |
| 跟進數 | CRM 中本週有跟進紀錄的 lead 筆數 |
| 成交數 | CRM 中本週狀態轉為「成交」的筆數 |
| 任務完成率 | (本週完成任務數 / 本週任務總數) * 100% |
| 週環比變化 | (本週數據 - 上週數據) / 上週數據 * 100% |

### 風險識別

依據 `references/risk_rules.json` 中的規則，自動掃描所有指標：

- 每條規則定義 `metric`、`threshold`、`condition`（above / below）、`severity`、`message`
- 觸發條件成立時，將 `message` 加入風險清單
- 風險清單最多 5 條

## 輸出格式

固定結構，對應 `references/report_schema.json`：

```
週報：[YYYY-MM-DD] ~ [YYYY-MM-DD]

本週重點摘要
1. [重點一]
...

業務數據
| 指標 | 本週 | 上週 | 變化 |
...

下週待辦事項
- [ ] [待辦一]
...

風險提醒
- [風險一：描述 + 建議動作]
...

生成時間：ISO 8601 timestamp
```

## 錯誤處理

| 情況 | 處理 |
|------|------|
| 本週無日報紀錄 | 重點摘要區塊標注「本週無日報紀錄」 |
| CRM 資料讀取失敗 | 業務數據區塊標注「資料讀取失敗」，指標設為 0 |
| 部分資料來源無數據 | 有數據的正常輸出，無數據的標注說明 |
| 上週無數據（無法計算週環比） | 變化欄位標注「N/A」 |
| 指標檔案格式錯誤 | 輸出錯誤訊息至 stderr，以空數據繼續 |
| 輸出目的地寫入失敗 | 重試 1 次，仍失敗則 fallback 至本地檔案 |

## 腳本架構

```
scripts/
├── collect_dailies.py      # 收集本週 daily brief 紀錄
├── collect_metrics.py      # 收集 CRM + 任務指標
├── generate_weekly.py      # 生成週報結構（摘要、比較、風險、待辦）
└── output_writer.py        # 寫入報告至檔案 / Notion / Sheets
```

- `collect_dailies.py` 負責從不同來源收集日報，本地模式讀取 JSON 檔案。
- `collect_metrics.py` 負責收集業務與任務指標，支援本週 + 上週對比。
- `generate_weekly.py` 是核心彙整邏輯，接收日報與指標 JSON，產出完整週報。
- `output_writer.py` 負責將週報寫入不同目的地，支援 JSON + Markdown 雙輸出。

## 參考資源

- `references/report_schema.json` — 週報輸出結構定義（提取自 report_output_schema.json 的 weekly_report 型別）。
- `references/prompt_templates.md` — 週報彙整 Prompt 模板，含 System Prompt、User Prompt、輸出範例。
- `references/risk_rules.json` — 風險識別規則，定義指標閾值與觸發條件。
