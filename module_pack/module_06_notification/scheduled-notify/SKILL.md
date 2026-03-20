---
name: scheduled-notify
description: "按排程執行指定任務（報告生成、CRM 提醒、行程提醒），完成後送通知並寫入紀錄。
  支援 Telegram 私訊和 Email 通知管道，含靜默時段和防洪機制。
  適用時機：使用者要求設定定時任務、排程通知，
  或提及關鍵字如 排程、定時、每天跑、自動通知、cron、schedule、提醒我、定期執行。
  不適用：即時通知（直接用 Telegram/Email skill）、多群組廣播、
  複雜排程依賴鏈（A 完成後觸發 B）。
  前置需求：目標 skill 已可正常執行。Telegram Bot Token 或 SMTP 設定為選配。"
metadata:
  openclaw:
    emoji: "\U0001F514"
    requires:
      bins: ["python3"]
      env: ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"]
---

# Scheduled Notify Skill

## 概述

完整排程通知流程：檢查排程 → 執行任務 → 發送通知 → 寫入紀錄。

把「記得每天做某件事」這個人腦負擔，轉交給機器。排程到點就執行，執行完就通知你，全程有紀錄可查。

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ 檢查排程      │ ──→ │ 執行任務      │ ──→ │ 發送通知      │ ──→ │ 寫入紀錄      │
│ scheduler.py │     │ (目標 skill)  │     │ notify_*.py  │     │record_writer │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

## 初始化（首次設定）

### Step 0-A：確認排程設定檔

檢查 `references/schedule_config.yaml` 是否已依照實際需求修改。若為預設範本，引導用戶逐一設定：

1. **timezone** — 預設 `Asia/Taipei`
2. **notification_channel** — `telegram` 或 `email`
3. **tasks** — 至少設定一個排程任務（名稱、skill、cron 表達式、參數）

### Step 0-B：設定 Telegram Bot（若選 Telegram 管道）

1. 與 [@BotFather](https://t.me/BotFather) 建立 Bot，取得 Bot Token
2. 向 Bot 發送任意訊息，取得 Chat ID（可透過 `https://api.telegram.org/bot{TOKEN}/getUpdates`）
3. 設定環境變數 `TELEGRAM_BOT_TOKEN` 和 `TELEGRAM_CHAT_ID`

### Step 0-C：驗證通知管道

```bash
python3 {skill_dir}/scripts/notify_telegram.py \
  --bot-token "${TELEGRAM_BOT_TOKEN}" \
  --chat-id "${TELEGRAM_CHAT_ID}" \
  --message "OpenClaw scheduled-notify 測試通知：設定成功！"
```

確認 Telegram 收到訊息後，初始化完成。

## 支援的任務類型

| 任務類型 | 對應 Skill | cron 範例 | 說明 |
|----------|-----------|-----------|------|
| 報告生成 | `daily_brief` | `0 8 * * *` | 每日早報 |
| CRM 提醒 | `crm_followup` | `0 9 * * 1-5` | 工作日跟進提醒 |
| 週報彙整 | `weekly_report` | `0 17 * * 5` | 每週五下午產出週報 |
| 行程提醒 | `calendar_check` | `0 * * * *` | 每小時檢查下一小時行程 |

## 工作流程

### Step 1：檢查排程

```bash
python3 {skill_dir}/scripts/scheduler.py \
  --config "{skill_dir}/references/schedule_config.yaml" \
  --timezone "Asia/Taipei"
```

輸出 JSON 陣列，包含所有當前時間到期的任務：

```json
[{"name": "每日早報", "skill": "daily_brief", "params": {"topic": "AI 產業動態"}}]
```

空陣列 `[]` 表示無到期任務。可傳入 `--check-time "2026-03-10T08:00:00"` 模擬特定時間。

### Step 2：執行目標 Skill

依照 `scheduler.py` 輸出的每個任務，呼叫對應的 skill 執行。此步驟由 agent 根據 `skill` 名稱分派，不由本 skill 的腳本處理。

等待 skill 執行完成，收集執行結果（成功/失敗、輸出位置、錯誤訊息）。

若執行失敗，等待 30 秒後重試 1 次。

### Step 3：發送通知

#### Telegram 通知

```bash
python3 {skill_dir}/scripts/notify_telegram.py \
  --bot-token "${TELEGRAM_BOT_TOKEN}" \
  --chat-id "${TELEGRAM_CHAT_ID}" \
  --message "{notification_message}" \
  --quiet-start "23:00" \
  --quiet-end "07:00" \
  --timezone "Asia/Taipei"
```

#### Email 通知（異常時使用）

```bash
python3 {skill_dir}/scripts/notify_email.py \
  --smtp-host "smtp.gmail.com" \
  --smtp-port 587 \
  --smtp-user "${EMAIL_USER}" \
  --smtp-password "${EMAIL_APP_PASSWORD}" \
  --from "${EMAIL_USER}" \
  --to "admin@example.com" \
  --subject "[OpenClaw] 排程任務異常通知" \
  --body "{failure_message}"
```

### Step 4：寫入紀錄

```bash
python3 {skill_dir}/scripts/record_writer.py \
  --task-name "每日早報" \
  --task-type "report" \
  --scheduled-at "2026-03-10T08:00:00+08:00" \
  --executed-at "2026-03-10T08:01:23+08:00" \
  --status "success" \
  --output-location "https://notion.so/daily-brief-20260310" \
  --notification-sent \
  --destination "file" \
  --output-dir "{skill_dir}"
```

## 通知管道

### Telegram 私訊

用於日常通知與任務完成通知。

**成功通知格式：**

```
[完成] 每日早報
時間：2026-03-10 08:01:23
結果：成功
摘要：已生成 AI 產業動態每日摘要，共 5 條重點
位置：https://notion.so/daily-brief-20260310
```

**失敗通知格式：**

```
[失敗] 每日早報
時間：2026-03-10 08:01:23
結果：失敗（已重試 1 次）
錯誤：Web Search API 連線逾時
行動：請檢查網路連線或 API 狀態
```

### Email

用於異常通知，確保重要錯誤不被遺漏。

**Email 格式：**

```
主旨：[OpenClaw][異常] 每日早報 執行失敗

每日早報 執行失敗

執行時間：2026-03-10 08:01:23
失敗原因：Web Search API 回傳 429 Too Many Requests
重試次數：1
影響範圍：今日早報未生成

建議行動：
請檢查 API 額度，或稍後手動觸發重跑

---
此通知由 OpenClaw scheduled_notify 自動發送
```

## 靜默時段與防洪機制

詳細規則見 `references/notification_rules.md`。摘要如下：

| 規則 | 說明 |
|------|------|
| 靜默時段 | 23:00–07:00 不發送一般通知（異常通知除外） |
| 靜默時段暫存 | 靜默期間的一般通知於 07:00 統一彙整發送 |
| 最短間隔 | 同類型通知至少間隔 5 分鐘 |
| 每小時上限 | 每小時最多 10 則通知（異常除外） |
| 去重 | 60 秒內完全相同的通知只發一則 |

## 紀錄寫入

每次任務執行完畢，寫入一筆 JSON 紀錄：

| 欄位 | 型別 | 說明 |
|------|------|------|
| `task_name` | string | 任務名稱 |
| `task_type` | string | report / crm_remind / calendar |
| `scheduled_at` | ISO 8601 | 排定執行時間 |
| `executed_at` | ISO 8601 | 實際執行時間 |
| `status` | string | success / failed / retried_success / retried_failed / missed |
| `error_message` | string | 錯誤訊息（僅失敗時） |
| `output_location` | string | 輸出位置（URL 或檔案路徑） |
| `notification_sent` | boolean | 通知是否已發送 |

紀錄以 JSONL 格式 append 至 `schedule_log.jsonl`。Notion 寫入為第二版功能（目前為 stub）。

## 安全限制

### 第一版明確限制

| 限制 | 原因 |
|------|------|
| 只做每天固定時間跑一次 | 簡單可靠，避免複雜排程的邊界情況 |
| 不做多群組廣播 | OpenClaw 的 announce 行為有已知 issue |
| 不做 Telegram topic 派送 | topic 功能仍有回歸問題 |
| 不做多代理共享排程 | 多代理排程協調複雜度過高 |
| 不做重啟後嚴格續跑 | 採「錯過就跳過」策略，記錄為 missed |
| 不做排程依賴鏈 | A 完成後觸發 B 的串接，第一版不處理 |
| 不做動態排程修改 | 改設定後重啟即可 |

### 其他安全規則

| 規則 | 說明 |
|------|------|
| 靜默時段 | 23:00–07:00 不發一般通知 |
| 重試上限 | 失敗最多重試 1 次，間隔 30 秒 |
| 錯過不補 | 排程時間已過不補執行，記錄為 missed |
| 單管道通知 | 第一版擇一管道，不做多管道同時發送 |

## 錯誤處理

| 錯誤情境 | 處理方式 |
|----------|----------|
| 目標 skill 不存在 | 記錄錯誤，通知管理員，不重試 |
| 目標 skill 執行失敗 | 重試 1 次（30 秒後），仍失敗則通知管理員 |
| 通知發送失敗 | 記錄錯誤，不影響紀錄寫入 |
| 紀錄寫入失敗 | 寫入本地日誌檔作為備份 |
| 排程時間已過 | 記錄為 missed，不補執行 |
| YAML 設定檔格式錯誤 | 輸出錯誤訊息至 stderr，exit code 1 |
| Telegram Bot Token 無效 | 回傳 failed 狀態與錯誤訊息 |
| SMTP 連線失敗 | 回傳 failed 狀態與錯誤訊息 |

## 腳本架構

```
scripts/
├── scheduler.py         # 解析 cron 設定，檢查哪些任務到期
├── notify_telegram.py   # 透過 Telegram Bot API 發送通知
├── notify_email.py      # 透過 SMTP 發送 Email 通知
└── record_writer.py     # 將執行紀錄寫入 JSONL 檔案或 Notion
```

- `scheduler.py` — 讀取 YAML 設定檔，內建 cron 表達式解析器（無外部依賴），輸出到期任務的 JSON 陣列。
- `notify_telegram.py` — 使用 `urllib.request` 呼叫 Telegram Bot API，支援靜默時段檢查。
- `notify_email.py` — 使用 Python 標準庫 `smtplib` + `email.mime` 發送郵件。
- `record_writer.py` — 將紀錄以 JSONL 格式 append 至檔案，Notion 寫入為 stub。

所有腳本：stdlib only，無需 pip install。

## 參考資源

- `references/notification_rules.md` — 通知類型、格式模板、靜默時段、防洪規則。排程流程中組合通知訊息時載入。
- `references/cron_reference.md` — cron 表達式速查表。設定排程時參考。
- `references/schedule_config.yaml` — 預設排程設定範本。初始化時載入並修改。
