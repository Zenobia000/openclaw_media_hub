# 通知規則設定

## 目錄

1. [概述](#概述)
2. [通知類型定義](#通知類型定義)
   - [任務完成通知](#1-任務完成通知-task_complete)
   - [提醒通知](#2-提醒通知-reminder)
   - [異常通知](#3-異常通知-failure)
3. [通知管道設定](#通知管道設定)
4. [通知格式模板](#通知格式模板)
   - [任務完成通知格式](#任務完成通知格式)
   - [提醒通知格式](#提醒通知格式)
   - [異常通知格式](#異常通知格式)
5. [靜默時段](#靜默時段)
6. [防洪規則](#防洪規則)
7. [通知狀態追蹤](#通知狀態追蹤)
8. [完整設定範例](#完整設定範例)

---

## 概述

本文件定義 `scheduled_notify` 的通知行為規則，包含通知類型、管道設定、格式模板、靜默時段、防洪規則。

---

## 通知類型定義

### 1. 任務完成通知 (task_complete)

當排程任務執行成功時發送。

| 欄位 | 說明 |
|------|------|
| **觸發條件** | 任務執行成功（status = `success` 或 `retried_success`） |
| **通知內容** | 任務名稱、完成時間、執行結果摘要、輸出位置 |
| **優先級** | 一般 |
| **管道** | Telegram 私訊 |
| **靜默時段適用** | 是（23:00-07:00 不發送） |

適用場景：
- 每日早報已生成
- 週報已完成
- CRM 數據已更新

### 2. 提醒通知 (reminder)

主動提醒使用者需要注意或採取行動的事項。

| 欄位 | 說明 |
|------|------|
| **觸發條件** | 排程到點且有需要提醒的事項 |
| **通知內容** | 提醒類型、相關項目、建議動作 |
| **優先級** | 一般 |
| **管道** | Telegram 私訊 |
| **靜默時段適用** | 是 |

適用場景：
- **行程提醒**：下一小時有會議或活動
- **CRM 跟進提醒**：有客戶超過 3 天未跟進
- **截止日提醒**：有任務即將到期（24 小時內）

### 3. 異常通知 (failure)

任務執行失敗或系統異常時發送。

| 欄位 | 說明 |
|------|------|
| **觸發條件** | 任務執行失敗（重試後仍失敗）、API 連線失敗、額度即將用完 |
| **通知內容** | 錯誤類型、錯誤訊息、影響範圍、建議行動 |
| **優先級** | 高 |
| **管道** | Telegram + Email 雙管道 |
| **靜默時段適用** | 否（異常通知不受靜默時段限制） |

適用場景：
- 任務執行失敗（重試 1 次後仍失敗）
- API 連線逾時或回傳錯誤
- Notion / Sheets API 額度即將用完（剩餘 < 10%）
- Telegram Bot 被封鎖或 Token 失效

---

## 通知管道設定

### 管道選擇規則

| 通知類型 | Telegram 私訊 | Email |
|----------|:------------:|:-----:|
| 任務完成通知 | V | -- |
| 提醒通知 | V | -- |
| 異常通知 | V | V |

### Telegram 私訊設定

```yaml
telegram:
  bot_token: "${TELEGRAM_BOT_TOKEN}"
  chat_id: "${TELEGRAM_CHAT_ID}"
  parse_mode: "Markdown"
  disable_web_page_preview: true
```

### Email 設定

```yaml
email:
  smtp_host: "smtp.gmail.com"
  smtp_port: 587
  smtp_user: "${EMAIL_USER}"
  smtp_password: "${EMAIL_APP_PASSWORD}"
  from: "${EMAIL_USER}"
  to:
    - "admin@example.com"
  subject_prefix: "[OpenClaw]"
```

---

## 通知格式模板

### 任務完成通知格式

**Telegram：**

```
[完成] {task_name}
時間：{executed_at}
結果：成功
摘要：{result_summary}
位置：{output_location}
```

**範例：**

```
[完成] 每日早報
時間：2026-03-10 08:01:23
結果：成功
摘要：已生成「AI 產業動態」每日摘要，共 5 條重點
位置：https://notion.so/daily-brief-20260310
```

### 提醒通知格式

**Telegram：**

```
[提醒] {reminder_type}
時間：{current_time}
內容：{reminder_content}
行動：{suggested_action}
```

**範例 -- 行程提醒：**

```
[提醒] 行程提醒
時間：2026-03-10 09:00
內容：10:00-11:00 產品週會（Google Meet）
行動：會議連結 https://meet.google.com/xxx
```

**範例 -- CRM 跟進提醒：**

```
[提醒] CRM 跟進
時間：2026-03-10 09:00
內容：以下客戶超過 3 天未跟進：
  1. 王小明（上次聯繫：3/6，詢問課程方案）
  2. 李小華（上次聯繫：3/5，等待報價回覆）
行動：請今日完成跟進，CRM 連結 https://notion.so/crm
```

### 異常通知格式

**Telegram：**

```
[異常] {task_name}
時間：{executed_at}
結果：失敗（已重試 {retry_count} 次）
錯誤：{error_message}
影響：{impact_description}
行動：{suggested_action}
```

**Email：**

```
主旨：[OpenClaw][異常] {task_name} 執行失敗

{task_name} 執行失敗

執行時間：{executed_at}
失敗原因：{error_message}
重試次數：{retry_count}
影響範圍：{impact_description}

建議行動：
{suggested_action}

---
此通知由 OpenClaw scheduled_notify 自動發送
```

---

## 靜默時段

### 規則

```yaml
quiet_hours:
  start: "23:00"
  end: "07:00"
  timezone: "Asia/Taipei"
  exceptions:
    - "failure_notification"    # 異常通知不受靜默時段限制
```

### 行為說明

| 時段 | 任務完成通知 | 提醒通知 | 異常通知 |
|------|:----------:|:-------:|:-------:|
| 07:00 - 23:00 | 正常發送 | 正常發送 | 正常發送 |
| 23:00 - 07:00 | 暫存，07:00 統一發送 | 暫存，07:00 統一發送 | 立即發送 |

### 暫存通知的處理

在靜默時段內產生的非異常通知，會暫存起來，在靜默時段結束後（07:00）統一發送一則彙整通知：

```
[彙整] 靜默時段通知摘要
時段：23:00 - 07:00
共 {count} 則通知：

1. [完成] 凌晨批次任務 — 02:00 執行成功
2. [提醒] 今日行程 — 09:00 有產品週會

詳細內容請查看排程紀錄。
```

---

## 防洪規則

### 目的

避免同類型通知在短時間內連續發送，造成通知轟炸。

### 規則

```yaml
flood_control:
  min_interval_seconds: 300        # 同類型通知最短間隔 5 分鐘
  max_per_hour: 10                 # 每小時最多 10 則通知（異常通知除外）
  dedup_window_seconds: 60         # 60 秒內完全相同的通知去重
```

### 行為說明

| 規則 | 觸發條件 | 處理方式 |
|------|----------|----------|
| **最短間隔** | 同類型通知在 5 分鐘內再次觸發 | 後者暫存，等間隔時間到後發送 |
| **每小時上限** | 同一小時內通知數超過 10 則 | 超出的通知合併為一則摘要 |
| **去重** | 60 秒內完全相同的通知 | 丟棄重複通知 |

### 範例

**場景：行程提醒每小時觸發但無行程**

```
08:00 行程檢查 -> 無行程 -> skip_if_empty -> 不通知
09:00 行程檢查 -> 有行程 -> 發送提醒
10:00 行程檢查 -> 無行程 -> skip_if_empty -> 不通知
```

**場景：API 連線問題導致多任務失敗**

```
08:00:00 每日早報失敗 -> 發送異常通知
08:00:05 CRM 提醒失敗 -> 同類型通知 5 分鐘內 -> 暫存
08:05:00 暫存通知到期 -> 發送彙整異常通知（含 2 個失敗任務）
```

---

## 通知狀態追蹤

每則通知的發送狀態都記錄在排程紀錄中：

| 欄位 | 型別 | 說明 |
|------|------|------|
| `notification_id` | string | 通知唯一識別碼 |
| `notification_type` | string | `task_complete` / `reminder` / `failure` |
| `channel` | string | `telegram` / `email` |
| `sent_at` | ISO 8601 | 發送時間 |
| `status` | string | `sent` / `queued` / `suppressed` / `failed` |
| `suppression_reason` | string | 被抑制的原因（靜默時段 / 防洪 / 去重） |

---

## 完整設定範例

```yaml
notification_rules:
  types:
    task_complete:
      priority: "normal"
      channels: ["telegram"]
      quiet_hours: true
      template: "task_complete"

    reminder:
      priority: "normal"
      channels: ["telegram"]
      quiet_hours: true
      template: "reminder"

    failure:
      priority: "high"
      channels: ["telegram", "email"]
      quiet_hours: false
      template: "failure"

  quiet_hours:
    start: "23:00"
    end: "07:00"
    timezone: "Asia/Taipei"
    buffer_notifications: true
    send_summary_at: "07:00"

  flood_control:
    min_interval_seconds: 300
    max_per_hour: 10
    dedup_window_seconds: 60

  templates:
    task_complete: |
      [完成] {task_name}
      時間：{executed_at}
      結果：成功
      摘要：{result_summary}
      位置：{output_location}

    reminder: |
      [提醒] {reminder_type}
      時間：{current_time}
      內容：{reminder_content}
      行動：{suggested_action}

    failure: |
      [異常] {task_name}
      時間：{executed_at}
      結果：失敗（已重試 {retry_count} 次）
      錯誤：{error_message}
      影響：{impact_description}
      行動：{suggested_action}
```
