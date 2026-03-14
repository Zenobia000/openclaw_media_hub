# OpenClaw Skill 規格文件：daily_brief

## 基本資訊

| 欄位 | 內容 |
|------|------|
| **Skill 名稱** | `daily_brief` |
| **所屬模組** | Module 05 — 查找資訊 → 整理 → 產報告 |
| **版本** | v1.0 |
| **最後更新** | 2026-03-10 |

---

## 功能描述

定時觸發（每天指定時間），自動查找指定主題的最新資訊，生成結構化摘要，寫入 Notion/Sheets 或發送 Email/Telegram 通知。

核心價值：**把「每天花 30 分鐘瀏覽新聞整理重點」這件事自動化，變成每天準時出現在你面前的結構化報告。**

---

## 觸發條件

| 觸發方式 | 說明 |
|----------|------|
| **cron 排程** | 每日固定時間執行（預設 `0 8 * * *`，每天 08:00） |
| **手動觸發** | 在 OpenClaw 對話中輸入指令手動執行 |

### 手動觸發範例

```
幫我跑一次今天的 daily brief，主題是「AI 產業動態」
```

---

## 報告題材選項

根據使用情境，`daily_brief` 支援以下預設題材：

| 題材 | 適用對象 | 資料來源 |
|------|----------|----------|
| **每日新聞摘要** | 一般使用者、主管 | 新聞網站、RSS、社群媒體 |
| **股票產業觀察** | 投資者、財務人員 | 財經新聞、股市資訊、產業報告 |
| **專案日報** | PM、團隊成員 | 任務清單、Git commits、會議記錄 |

---

## 輸入參數

| 參數名稱 | 型別 | 必填 | 預設值 | 說明 |
|----------|------|------|--------|------|
| `topic` | string | Y | — | 主題關鍵字，例如「AI 產業動態」「台股半導體」 |
| `sources` | string[] | N | `["web_search"]` | 資料來源清單，可指定特定網站或 RSS |
| `output_format` | string | N | `"structured"` | 輸出格式：`structured` / `brief` / `detailed` |
| `recipients` | string[] | N | `["self"]` | 發送對象，支援 email / telegram_id |
| `output_destination` | string | N | `"notion"` | 輸出目的地：`notion` / `sheets` / `email` / `telegram` |
| `language` | string | N | `"zh-TW"` | 輸出語言 |
| `max_sources` | number | N | `5` | 最多引用幾個來源 |

---

## 輸出格式

每次報告輸出固定結構，**不讓每次報告長得不一樣**：

```
📋 每日摘要：[主題]
📅 日期：YYYY-MM-DD

📝 摘要
[100-200 字的整體摘要]

🔑 重點清單
1. [重點一]
2. [重點二]
3. [重點三]
4. [重點四]
5. [重點五]

🔗 來源
- [來源標題 1](URL)
- [來源標題 2](URL)
- [來源標題 3](URL)

⏰ 生成時間：ISO 8601 timestamp
```

### 對應 JSON Schema

請參照 `report_output_schema.json` 中的 `daily_brief` 型別定義。

---

## 執行流程

```
排程到點 / 手動觸發
       │
       ▼
[1] 解析輸入參數（主題、來源、格式）
       │
       ▼
[2] 呼叫 Web Search skill 搜尋最新資訊
       │
       ▼
[3] 篩選 & 去重（移除重複報導、過期資訊）
       │
       ▼
[4] 生成結構化摘要（套用固定格式模板）
       │
       ▼
[5] 寫入輸出目的地（Notion / Sheets）
       │
       ▼
[6] 發送通知（Telegram / Email）
       │
       ▼
[7] 寫入執行紀錄
```

---

## 依賴

| 依賴項目 | 用途 | 必要性 |
|----------|------|--------|
| **Web Search skill** | 搜尋最新資訊 | 必要 |
| **Notion API** | 寫入報告到 Notion | 擇一 |
| **Google Sheets API** | 寫入報告到 Sheets | 擇一 |
| **Telegram Bot API** | 發送通知 | 擇一 |
| **Email (SMTP)** | 發送通知 | 擇一 |

---

## 安全限制

| 規則 | 說明 |
|------|------|
| **只讀取公開資訊** | 不存取付費牆後的內容、不繞過登入驗證 |
| **不存取付費內容** | 遇到付費牆時跳過該來源，標記為「無法存取」 |
| **輸出前不自動發佈** | 預設為草稿模式，除非設定中明確開啟 `auto_publish: true` |
| **不編造資訊** | 找不到足夠資料時，報告中明確標注「資料不足」 |
| **來源必須標注** | 每條資訊都必須附上來源連結 |

---

## 關鍵設計：鎖定輸出格式

這是整個 Skill 最重要的設計原則：

> **固定輸出格式，不讓每次報告長得不一樣。**

### 為什麼要鎖格式？

- LLM 天性喜歡「每次寫不一樣的東西」，這在報告場景是災難
- 使用者需要的是**可預期、可比較、可掃讀**的固定結構
- 如果每天報告格式不同，根本無法快速瀏覽

### 如何用 Claude Code 鎖格式？

#### 1. Skills 設定

在 `.claude/skills/daily_brief.md` 中定義固定格式模板，Claude Code 每次生成報告時都會參照這個模板。

#### 2. CLAUDE.md 指令

在專案的 `CLAUDE.md` 中加入：

```markdown
## 報告生成規則
- 所有 daily_brief 報告必須嚴格遵循 report_output_schema.json 的格式
- 摘要不超過 200 字
- 重點清單固定 3-5 條
- 來源固定附上標題和 URL
- 不得加入 schema 未定義的額外欄位
```

#### 3. Hooks 驗證

使用 Claude Code hooks 在輸出後自動驗證格式：

```json
{
  "hooks": {
    "post_generate": {
      "command": "python validate_report.py --schema report_output_schema.json",
      "on_failure": "reject_and_retry"
    }
  }
}
```

#### 4. 檔名鎖定

輸出檔名也固定格式：

```
daily_brief_YYYY-MM-DD_[topic_slug].json
daily_brief_YYYY-MM-DD_[topic_slug].md
```

---

## 設定範例

```yaml
daily_brief:
  schedule: "0 8 * * *"
  timezone: "Asia/Taipei"
  topic: "AI 產業動態"
  sources:
    - web_search
  output_format: structured
  output_destination: notion
  auto_publish: false
  recipients:
    - telegram: "@your_username"
  language: "zh-TW"
  max_sources: 5
```

---

## 錯誤處理

| 錯誤情境 | 處理方式 |
|----------|----------|
| Web Search 無結果 | 報告標注「今日無相關新資訊」，仍輸出空報告結構 |
| Notion API 失敗 | 重試 1 次，仍失敗則改寫到本地檔案 + 通知管理員 |
| 通知發送失敗 | 記錄錯誤日誌，不影響報告生成 |
| 資料來源全部無法存取 | 輸出空報告 + 異常通知 |

---

## 教學重點

1. **Web Search 是基礎** — 先確保 Web Search skill 能正常運作
2. **格式比內容重要** — 先把固定格式跑通，再優化內容品質
3. **從手動到自動** — 先手動觸發確認結果，再開排程
4. **輸出目的地可替換** — 先用最簡單的（本地檔案），再接 Notion/Sheets
