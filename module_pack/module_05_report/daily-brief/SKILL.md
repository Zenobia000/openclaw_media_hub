---
name: daily-brief
description: "定時或手動觸發，搜尋指定主題的最新資訊，生成結構化每日摘要報告。
  支援輸出至 Notion、Google Sheets、本地檔案，並可透過 Telegram 或 Email 發送通知。
  適用時機：使用者要求產出每日摘要、新聞整理、產業觀察，
  或提及關鍵字如 daily brief、每日摘要、早報、今日新聞、幫我整理今天的、每日報告。
  不適用：週報彙整（使用 weekly-report）、即時新聞查詢（使用一般對話）、
  歷史資料分析、非公開資訊的整理。
  前置需求：Web Search 功能可用。Notion/Sheets API 為選配。"
metadata:
  openclaw:
    emoji: "📋"
    requires:
      bins: ["python3", "curl"]
---

# Daily Brief Skill

## 概述

完整報告流程：解析主題 → 搜尋最新資訊 → 篩選去重 → 生成結構化摘要 → 寫入輸出目的地 → 發送通知。

核心價值：把「每天花 30 分鐘瀏覽新聞整理重點」自動化，變成每天準時出現的結構化報告。

## 設定

每次報告流程開始時載入 `references/report_schema.json`，包含：

| 欄位 | 說明 |
|------|------|
| `daily_brief` schema | 報告輸出的 JSON Schema 定義，含 title / date / topic / summary / key_points / sources / generated_at |
| `output_settings` | 全域輸出設定：語言、摘要字數上限、重點條數上限、是否附來源 |

### 初始化

技能首次使用前確認以下條件：

1. **`references/report_schema.json` 存在** — 不存在則提示用戶檢查模組安裝完整性
2. **`python3` 可用** — 執行 `python3 --version` 確認
3. **`curl` 可用** — 執行 `curl --version` 確認
4. **網路連線正常** — 執行 `curl -s -o /dev/null -w "%{http_code}" https://duckduckgo.com` 確認回傳 200

全部通過後進入報告工作流程。

## 工作流程

### Step 1：解析輸入參數

從使用者訊息中提取：

| 參數 | 必填 | 預設值 | 說明 |
|------|:----:|--------|------|
| `topic` | Y | — | 主題關鍵字，例如「AI 產業動態」 |
| `date` | N | 今天 | 報告日期，YYYY-MM-DD |
| `output_format` | N | `structured` | 輸出格式：`structured` / `brief` / `detailed` |
| `max_sources` | N | `5` | 最多引用幾個來源 |
| `language` | N | `zh-TW` | 輸出語言 |
| `output_destination` | N | `file` | 輸出目的地：`file` / `notion` / `sheets` |
| `output_path` | N | 當前目錄 | file 模式的輸出路徑 |

若 `topic` 缺失，詢問使用者：
> 請問您想要產出哪個主題的每日摘要？例如：「AI 產業動態」、「台股半導體」、「電動車趨勢」

### Step 2：搜尋最新資訊

```bash
python3 {skill_dir}/scripts/web_search.py \
  --topic "{topic}" \
  --max-results "{max_sources}" \
  --language "{language}"
```

輸出：JSON 陣列，每筆含 `title`、`url`、`snippet`。

若搜尋無結果，報告標注「今日無相關新資訊」，仍輸出空報告結構。

### Step 3：篩選與去重

Agent 根據搜尋結果進行：
- 移除重複報導（相同事件的不同來源只保留最具代表性的一則）
- 過濾過期或不相關的資訊
- 依相關度排序

將篩選後的結果存為暫存 JSON 檔案。

### Step 4：生成結構化報告

分兩步驟：

**4a. 建立報告骨架**

```bash
python3 {skill_dir}/scripts/generate_report.py \
  --topic "{topic}" \
  --date "{YYYY-MM-DD}" \
  --format "{output_format}" \
  --schema "{skill_dir}/references/report_schema.json" \
  --sources-json "{filtered_sources.json}"
```

輸出：JSON 報告結構（含 metadata、來源資訊，但 `summary` 和 `key_points` 為佔位符）。

**4b. Agent 填入摘要內容**

Agent 載入 `references/prompt_templates.md` 中對應的 System Prompt，根據搜尋結果填入：
- `summary`：100-200 字的整體摘要
- `key_points`：3-5 條重點，每條不超過 80 字

填入時嚴格遵循 `references/report_schema.json` 的格式定義。

### Step 5：寫入輸出目的地

```bash
python3 {skill_dir}/scripts/output_writer.py \
  --input "{report.json}" \
  --destination "{output_destination}" \
  --output-path "{output_path}"
```

輸出：JSON 含 `status` 和 `location`。

- **file 模式**：同時寫出 JSON 和 Markdown 兩個版本
- **notion 模式**：透過 Notion API 寫入指定頁面（需預先設定 API key）
- **sheets 模式**：透過 Google Sheets API 寫入指定試算表（需預先設定認證）

### Step 6：發送通知（選配）

若使用者設定了 `recipients`，Agent 透過對應的通知管道發送報告摘要。此步驟為選配，失敗不影響報告生成。

### Step 7：回覆確認

向使用者回覆報告已生成，包含：
- 報告標題與日期
- 摘要預覽（前 100 字）
- 輸出位置（檔案路徑或 URL）
- 來源數量

## 輸出格式

每次報告輸出固定結構，不讓每次報告長得不一樣。

### 文字格式

```
📋 每日摘要：[主題]
📅 日期：YYYY-MM-DD

📝 摘要
[100-200 字的整體摘要]

🔑 重點清單
1. [重點一]
2. [重點二]
3. [重點三]

🔗 來源
- [來源標題 1](URL)
- [來源標題 2](URL)

⏰ 生成時間：ISO 8601 timestamp
```

### JSON 格式

嚴格遵循 `references/report_schema.json` 中 `daily_brief` 的定義。

### 檔名規則

```
daily_brief_YYYY-MM-DD_[topic_slug].json
daily_brief_YYYY-MM-DD_[topic_slug].md
```

## 安全限制

1. **只讀取公開資訊** — 不存取付費牆後的內容、不繞過登入驗證
2. **不存取付費內容** — 遇到付費牆時跳過該來源，標記為「無法存取」
3. **不編造資訊** — 找不到足夠資料時，報告中明確標注「資料不足」
4. **來源必須標注** — 每條資訊都必須附上來源連結
5. **輸出前不自動發佈** — 預設為草稿模式，除非設定中明確開啟

## 錯誤處理

| 情況 | 處理 |
|------|------|
| Web Search 無結果 | 報告標注「今日無相關新資訊」，仍輸出空報告結構 |
| 搜尋部分失敗 | 使用已取得的結果繼續生成，報告中標注資料可能不完整 |
| 報告結構不符 schema | 重新生成，確保欄位完整 |
| Notion API 失敗 | 重試 1 次，仍失敗則改寫到本地檔案，通知使用者 |
| Sheets API 失敗 | 重試 1 次，仍失敗則改寫到本地檔案，通知使用者 |
| 通知發送失敗 | 記錄錯誤日誌，不影響報告生成 |
| 資料來源全部無法存取 | 輸出空報告結構，附異常說明 |
| 網路連線中斷 | 提示使用者檢查網路連線後重試 |

## 腳本架構

```
scripts/
├── web_search.py        # 搜尋最新資訊（DuckDuckGo HTML search via curl）
├── generate_report.py   # 建立報告骨架（填入 metadata、格式化來源）
└── output_writer.py     # 寫入輸出目的地（file / notion / sheets）
```

- `web_search.py` 使用 `subprocess` 呼叫 `curl` 搜尋 DuckDuckGo，無需 API key。
- `generate_report.py` 建立符合 schema 的報告結構，摘要內容由 Agent 根據 prompt templates 填入。
- `output_writer.py` 支援多種輸出目的地，file 模式同時產出 JSON 和 Markdown。

## 參考資源

- `references/report_schema.json` — 每次報告流程開始時載入，包含 daily_brief 的 JSON Schema 定義與全域輸出設定。用於驗證報告結構。
- `references/prompt_templates.md` — Step 4b 生成摘要內容時載入，包含各題材（新聞摘要、產業觀察、專案日報）的 System Prompt 與 User Prompt 模板。Agent 根據題材選擇對應模板。
