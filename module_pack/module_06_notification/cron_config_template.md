# 排程設定模板文件

## 概述

本文件定義 `scheduled_notify` 的排程設定方式，包含排程表格、cron 表達式速查、預設範例，以及第一版的限制說明。

---

## 排程設定表格

| 任務名稱 | cron 表達式 | 執行內容 | 通知對象 | 紀錄位置 |
|----------|------------|----------|----------|----------|
| 每日早報 | `0 8 * * *` | 執行 `daily_brief` skill，產出今日摘要 | Telegram 私訊 | Notion 排程紀錄 |
| CRM 跟進提醒 | `0 9 * * 1-5` | 查詢待跟進客戶，發送提醒清單 | Telegram 私訊 | Notion 排程紀錄 |
| 週報彙整 | `0 17 * * 5` | 執行 `weekly_report` skill，產出週報 | Telegram + Email | Notion 排程紀錄 |
| 行程提醒 | `0 * * * *` | 檢查下一小時行程，有行程則提醒 | Telegram 私訊 | Notion 排程紀錄 |

---

## 預設排程範例

### 1. 每日早報

```yaml
task:
  name: "每日早報"
  skill: "daily_brief"
  schedule: "0 8 * * *"           # 每天 08:00
  timezone: "Asia/Taipei"
  params:
    topic: "AI 產業動態"
    output_destination: "notion"
  notification:
    channel: "telegram"
    on_success: true
    on_failure: true
  record:
    destination: "notion"
    database: "排程紀錄"
```

### 2. CRM 跟進提醒

```yaml
task:
  name: "CRM 跟進提醒"
  skill: "crm_followup"
  schedule: "0 9 * * 1-5"         # 週一到週五 09:00
  timezone: "Asia/Taipei"
  params:
    filter: "status=待跟進 AND days_since_last_contact>=3"
    sort: "priority DESC"
  notification:
    channel: "telegram"
    on_success: true               # 有待跟進客戶時通知
    on_failure: true
    skip_if_empty: true            # 無待跟進客戶時不通知
  record:
    destination: "notion"
    database: "排程紀錄"
```

### 3. 週報彙整

```yaml
task:
  name: "週報彙整"
  skill: "weekly_report"
  schedule: "0 17 * * 5"          # 每週五 17:00
  timezone: "Asia/Taipei"
  params:
    data_sources:
      - daily_brief
      - crm
      - tasks
    output_destination: "notion"
  notification:
    channel: "telegram"
    on_success: true
    on_failure: true
  record:
    destination: "notion"
    database: "排程紀錄"
```

### 4. 行程提醒

```yaml
task:
  name: "行程提醒"
  skill: "calendar_check"
  schedule: "0 * * * *"           # 每小時整點
  timezone: "Asia/Taipei"
  params:
    lookahead_minutes: 60          # 檢查未來 60 分鐘的行程
    calendar_source: "google"
  notification:
    channel: "telegram"
    on_success: true
    on_failure: false              # 行程檢查失敗不通知（避免每小時轟炸）
    skip_if_empty: true            # 無行程時不通知
  record:
    destination: "notion"
    database: "排程紀錄"
```

---

## cron 表達式速查表

### 格式

```
┌───────────── 分鐘 (0-59)
│ ┌───────────── 小時 (0-23)
│ │ ┌───────────── 日期 (1-31)
│ │ │ ┌───────────── 月份 (1-12)
│ │ │ │ ┌───────────── 星期 (0-7，0 和 7 都是星期日)
│ │ │ │ │
* * * * *
```

### 特殊字元

| 字元 | 意義 | 範例 |
|------|------|------|
| `*` | 任意值 | `* * * * *`（每分鐘） |
| `,` | 列舉 | `0,30 * * * *`（每小時的 0 分和 30 分） |
| `-` | 範圍 | `0 9-17 * * *`（9:00 到 17:00 的每小時整點） |
| `/` | 間隔 | `*/15 * * * *`（每 15 分鐘） |

### 常用範例

| 說明 | cron 表達式 | 備註 |
|------|------------|------|
| 每天早上 8 點 | `0 8 * * *` | 最常用的日報排程 |
| 每天早上 9 點 | `0 9 * * *` | 適合工作開始時的提醒 |
| 週一到週五早上 9 點 | `0 9 * * 1-5` | 工作日才執行 |
| 每週五下午 5 點 | `0 17 * * 5` | 週報排程 |
| 每小時整點 | `0 * * * *` | 行程提醒 |
| 每 30 分鐘 | `*/30 * * * *` | 頻繁檢查用 |
| 每月 1 號早上 10 點 | `0 10 1 * *` | 月報排程 |
| 每天早上 8 點和下午 6 點 | `0 8,18 * * *` | 早晚各一次 |
| 週一早上 9 點 | `0 9 * * 1` | 每週開始的提醒 |
| 每天凌晨 2 點 | `0 2 * * *` | 適合跑批次作業 |

### 星期對照

| 數字 | 星期 |
|------|------|
| 0 | 星期日 |
| 1 | 星期一 |
| 2 | 星期二 |
| 3 | 星期三 |
| 4 | 星期四 |
| 5 | 星期五 |
| 6 | 星期六 |
| 7 | 星期日（同 0） |

---

## 時區設定

```yaml
timezone: "Asia/Taipei"    # UTC+8
```

所有 cron 表達式的時間都基於此時區。例如 `0 8 * * *` 表示台北時間早上 8 點。

### 注意事項

- OpenClaw 伺服器可能運行在不同時區，務必明確設定 `timezone`
- 日光節約時間（DST）：`Asia/Taipei` 不使用 DST，無需擔心時間跳轉問題
- 如果需要 UTC 時間，設定為 `timezone: "UTC"`

---

## 失敗處理

### 重試策略

```yaml
failure_handling:
  max_retries: 1                   # 最多重試 1 次
  retry_delay_seconds: 30          # 重試間隔 30 秒
  on_final_failure: "notify_admin" # 仍失敗時通知管理員
  missed_execution: "skip"         # 錯過的排程不補執行
```

### 失敗處理流程

```
任務執行失敗
     │
     ▼
等待 30 秒後重試
     │
     ├── 重試成功 → 記錄為 retried_success → 送成功通知
     │
     └── 重試失敗 → 記錄為 retried_failed → 送失敗通知給管理員
```

### 失敗通知內容

```
[失敗] 任務名稱
時間：YYYY-MM-DD HH:mm:ss
狀態：執行失敗（已重試 1 次）
錯誤：具體錯誤訊息
建議：下一步行動建議
```

---

## 第一版限制說明

### 不做複雜排程

| 不做的功能 | 原因 |
|-----------|------|
| **分鐘級精確排程** | 第一版只需要小時級精度，分鐘級排程增加複雜度但無明顯收益 |
| **動態排程修改** | 排程修改需要重啟或熱載入機制，第一版改設定後重啟即可 |
| **排程依賴鏈** | 例如「A 完成後再跑 B」的串接，第一版每個任務獨立執行 |
| **排程佇列** | 同時間多任務的排隊機制，第一版假設不會有排程衝突 |

### 不做 announce 模式

| 不做的功能 | 原因 |
|-----------|------|
| **多群組廣播** | OpenClaw 的 announce 功能有已知的重複觸發問題 |
| **Telegram topic 派送** | topic 功能在 OpenClaw 中仍有回歸問題，行為不穩定 |
| **頻道（Channel）發布** | 頻道發布需要額外的權限管理，第一版不處理 |

### 為什麼保守策略是對的

1. **可觀察性** — 簡單的排程容易 debug，出問題時能快速定位原因
2. **可靠性** — 功能少但穩定，比功能多但偶爾出錯更有價值
3. **漸進式** — 第一版跑穩後，第二版再加入進階功能
4. **教學友善** — 學員需要的是「能動」的東西，不是「功能完整但設定複雜」的東西

### 第二版規劃（參考用）

當第一版穩定運行後，可考慮加入：

- 排程依賴鏈（A 完成後觸發 B）
- 動態排程修改（透過對話修改排程，無需重啟）
- 多管道同時通知
- 排程衝突處理
- 執行歷史分析（成功率、平均執行時間）

---

## 完整設定檔範例

```yaml
# scheduled_notify_config.yaml

global:
  timezone: "Asia/Taipei"
  notification_channel: "telegram"
  record_destination: "notion"

telegram:
  bot_token: "${TELEGRAM_BOT_TOKEN}"
  chat_id: "${TELEGRAM_CHAT_ID}"

notion:
  api_key: "${NOTION_API_KEY}"
  schedule_log_db: "${NOTION_SCHEDULE_LOG_DB}"

failure_handling:
  max_retries: 1
  retry_delay_seconds: 30
  on_final_failure: "notify_admin"
  missed_execution: "skip"

quiet_hours:
  start: "23:00"
  end: "07:00"
  exceptions: ["failure_notification"]

tasks:
  - name: "每日早報"
    skill: "daily_brief"
    schedule: "0 8 * * *"
    params:
      topic: "AI 產業動態"
      output_destination: "notion"
    notification:
      on_success: true
      on_failure: true

  - name: "CRM 跟進提醒"
    skill: "crm_followup"
    schedule: "0 9 * * 1-5"
    params:
      filter: "status=待跟進 AND days_since_last_contact>=3"
    notification:
      on_success: true
      on_failure: true
      skip_if_empty: true

  - name: "週報彙整"
    skill: "weekly_report"
    schedule: "0 17 * * 5"
    params:
      data_sources: ["daily_brief", "crm", "tasks"]
      output_destination: "notion"
    notification:
      on_success: true
      on_failure: true

  - name: "行程提醒"
    skill: "calendar_check"
    schedule: "0 * * * *"
    params:
      lookahead_minutes: 60
    notification:
      on_success: true
      on_failure: false
      skip_if_empty: true
```
