# OpenClaw Skill 規格文件：scheduled_notify

## 基本資訊

| 欄位 | 內容 |
|------|------|
| **Skill 名稱** | `scheduled_notify` |
| **所屬模組** | Module 06 — 定時通知 / 紀錄 |
| **版本** | v1.0 |
| **最後更新** | 2026-03-10 |

---

## 功能描述

按排程執行指定任務（報告生成、CRM 提醒、行程提醒），完成後送通知，並寫入紀錄。

核心價值：**把「記得每天做某件事」這個人腦負擔，轉交給機器。排程到點就執行，執行完就通知你，全程有紀錄可查。**

---

## 觸發條件

| 觸發方式 | 說明 |
|----------|------|
| **cron 排程** | 每日固定時間執行（依任務設定） |
| **手動觸發** | 在 OpenClaw 對話中輸入指令手動執行特定任務 |

第一版只做 **每天固定時間跑一次** 的排程，不做複雜排程邏輯。

---

## 執行流程

```
┌─────────────────────────────────────┐
│         排程引擎（cron）              │
│   每分鐘檢查是否有任務需要執行         │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  [1] 排程到點，觸發任務               │
│      - 檢查任務設定                   │
│      - 確認目標 skill 可用             │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  [2] 執行任務                        │
│      - 呼叫對應的 skill               │
│        (daily_brief / weekly_report   │
│         / crm_remind / calendar)      │
│      - 等待執行結果                   │
└──────────────┬──────────────────────┘
               │
          ┌────┴────┐
          │         │
       成功       失敗
          │         │
          ▼         ▼
┌──────────┐  ┌──────────────┐
│ [3a] 送  │  │ [3b] 重試    │
│ 成功通知  │  │ 1 次         │
└────┬─────┘  └──────┬───────┘
     │               │
     │          ┌────┴────┐
     │       成功       仍失敗
     │          │         │
     │          ▼         ▼
     │   ┌──────────┐ ┌────────────┐
     │   │ 送成功   │ │ 送失敗通知  │
     │   │ 通知     │ │ 給管理員    │
     │   └────┬─────┘ └──────┬─────┘
     │        │              │
     ▼        ▼              ▼
┌─────────────────────────────────────┐
│  [4] 寫入執行紀錄                    │
│      - 任務名稱                      │
│      - 執行時間                      │
│      - 執行結果（成功/失敗）           │
│      - 錯誤訊息（如有）               │
└─────────────────────────────────────┘
```

---

## 支援的任務類型

| 任務類型 | 對應 Skill | 說明 |
|----------|-----------|------|
| **報告生成** | `daily_brief` / `weekly_report` | 定時產出報告 |
| **CRM 提醒** | `crm_followup`（Module 03） | 提醒跟進特定客戶 |
| **行程提醒** | `calendar_check` | 檢查下一小時的行程並提醒 |

---

## 通知管道

| 管道 | 適用情境 | 設定方式 |
|------|----------|----------|
| **Telegram 私訊** | 日常通知、任務完成通知 | 設定 Telegram Bot Token + Chat ID |
| **Email** | 重要通知、週報發送 | 設定 SMTP 伺服器 + 收件人 |

第一版只支援 **擇一管道**，不做多管道同時發送（重要/異常通知的雙管道由 `notification_rules.md` 定義，但第一版簡化為單管道）。

---

## 紀錄寫入

每次任務執行完畢，無論成功或失敗，都寫入一筆紀錄：

| 欄位 | 型別 | 說明 |
|------|------|------|
| `task_name` | string | 任務名稱 |
| `task_type` | string | 任務類型（report / crm_remind / calendar） |
| `scheduled_at` | ISO 8601 | 排定執行時間 |
| `executed_at` | ISO 8601 | 實際執行時間 |
| `status` | string | `success` / `failed` / `retried_success` / `retried_failed` |
| `error_message` | string | 錯誤訊息（僅失敗時） |
| `output_location` | string | 輸出位置（Notion page URL / Sheets URL / 檔案路徑） |
| `notification_sent` | boolean | 通知是否已發送 |

### 紀錄寫入位置

與 CRM 模組使用同一資料面：

- **Notion**：在同一個 Notion workspace 中的「排程紀錄」資料庫
- **Google Sheets**：在同一個 Spreadsheet 中的「排程紀錄」工作表

---

## 安全限制

### 第一版明確限制

| 限制 | 原因 |
|------|------|
| **只做每天固定時間跑一次** | 簡單可靠，避免複雜排程的邊界情況 |
| **不做多群組廣播** | OpenClaw 的 announce 行為有已知 issue（重複觸發） |
| **不做 Telegram topic 派送** | topic 功能在 OpenClaw 中仍有回歸問題 |
| **不做多代理共享排程** | 多代理的排程協調複雜度過高，第一版不處理 |
| **不做重啟後嚴格續跑** | 重啟後的排程恢復邏輯容易出 bug，第一版採「錯過就跳過」策略 |

### 為什麼這些限制是必要的

OpenClaw 作為一個持續演進的平台，其 cron / announce / topic 功能仍在迭代中。已知的問題包括：

1. **cron 重複觸發**：在某些情境下，同一個 cron 任務可能在同一時間點被觸發多次
2. **announce 回歸問題**：群組廣播功能在更新後偶爾出現行為不一致
3. **重啟後排程遺失**：服務重啟後，排程狀態可能無法完整恢復

因此，第一版採取保守策略：**簡單、可靠、可觀察**。等平台穩定後再逐步開放進階功能。

### 其他安全規則

| 規則 | 說明 |
|------|------|
| **靜默時段** | 23:00-07:00 不發通知（異常通知除外） |
| **重試上限** | 失敗最多重試 1 次 |
| **錯過不補** | 如果排程時間已過（如服務中斷），不補執行，記錄為 `missed` |

---

## 設定範例

```yaml
scheduled_notify:
  timezone: "Asia/Taipei"
  notification_channel: "telegram"
  telegram:
    bot_token: "${TELEGRAM_BOT_TOKEN}"
    chat_id: "${TELEGRAM_CHAT_ID}"
  record_destination: "notion"
  notion:
    database_id: "${NOTION_SCHEDULE_LOG_DB}"

  tasks:
    - name: "每日早報"
      skill: "daily_brief"
      schedule: "0 8 * * *"
      params:
        topic: "AI 產業動態"
      notify_on_success: true
      notify_on_failure: true

    - name: "CRM 跟進提醒"
      skill: "crm_followup"
      schedule: "0 9 * * 1-5"
      params:
        filter: "status=待跟進 AND last_contact<3days"
      notify_on_success: true
      notify_on_failure: true

    - name: "週報彙整"
      skill: "weekly_report"
      schedule: "0 17 * * 5"
      params:
        data_sources: ["daily_brief", "crm", "tasks"]
      notify_on_success: true
      notify_on_failure: true
```

---

## 通知訊息格式

### 成功通知

```
[完成] 每日早報
時間：2026-03-10 08:01:23
結果：成功
摘要：已生成 AI 產業動態每日摘要，共 5 條重點
位置：https://notion.so/xxx
```

### 失敗通知

```
[失敗] 每日早報
時間：2026-03-10 08:01:23
結果：失敗（已重試 1 次）
錯誤：Web Search API 連線逾時
行動：請檢查網路連線或 API 狀態
```

---

## 與其他模組的關係

```
Module 03 (CRM) ─────── crm_followup ──┐
                                        │
Module 05 (daily_brief) ────────────────┼──→ scheduled_notify ──→ Telegram / Email
                                        │           │
Module 05 (weekly_report) ──────────────┘           │
                                                    ▼
                                            排程紀錄（Notion / Sheets）
```

`scheduled_notify` 是所有模組的「執行層 + 通知層」，負責：
1. 按排程呼叫其他 skill
2. 收集執行結果
3. 發送通知
4. 寫入紀錄

---

## 錯誤處理

| 錯誤情境 | 處理方式 |
|----------|----------|
| 目標 skill 不存在 | 記錄錯誤，通知管理員，不重試 |
| 目標 skill 執行失敗 | 重試 1 次，仍失敗則通知管理員 |
| 通知發送失敗 | 記錄錯誤，不影響紀錄寫入 |
| 紀錄寫入失敗 | 寫入本地日誌檔作為備份 |
| 排程時間已過 | 記錄為 `missed`，不補執行 |

---

## 教學重點

1. **先手動，再排程** — 先確認每個 skill 手動執行正常，再接上排程
2. **通知管道從 Telegram 開始** — Telegram Bot 設定最簡單，適合教學
3. **紀錄是核心** — 沒有紀錄就無法追蹤和除錯，紀錄比通知更重要
4. **保守策略** — 第一版不追求功能完整，追求穩定可靠
