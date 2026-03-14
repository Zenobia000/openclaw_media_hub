# OpenClaw Skill 規格：calendar_booking

> 模組：Module 01 — 預約模組
> 版本：v1.0
> 最後更新：2026-03-10

---

## 1. 基本資訊

| 欄位 | 值 |
|------|-----|
| **Skill Name** | `calendar_booking` |
| **Skill ID** | `mod01_calendar_booking` |
| **Category** | Scheduling / Booking |
| **Status** | v1 — 最小可行版 |
| **Author** | Sunny Data Science |

---

## 2. 功能描述

解析用戶對話中的日期時間需求，查詢 Google Calendar 可用時段，建立日曆事件，回覆確認訊息，並將預約紀錄寫入 CRM。

### 完整流程

```
用戶：「我想約下週三下午」
  │
  ▼
Step 1：解析意圖 — 辨識為預約請求
  │
  ▼
Step 2：提取參數 — 日期：下週三、時段：下午、時長：預設值
  │
  ▼
Step 3：查詢空檔 — 呼叫 Calendar API (freebusy.query)
  │
  ▼
Step 4：推薦時段 — 回覆 2-3 個可用時段供選擇
  │
  ▼
Step 5：用戶確認 — 用戶選擇其中一個時段
  │
  ▼
Step 6：建立事件 — 呼叫 Calendar API (events.insert)
  │
  ▼
Step 7：回覆確認 — 發送確認訊息（含事件詳情 + Calendar 連結）
  │
  ▼
Step 8：寫入 CRM — 將預約紀錄 append 到 CRM（模組 3）
```

---

## 3. 觸發條件

### 關鍵字觸發

當用戶訊息中包含以下關鍵字時觸發本 Skill：

- 繁體中文：`預約`、`約時間`、`排時間`、`訂時間`、`安排`、`約一下`
- 英文：`book`、`schedule`、`appointment`、`reserve`

### 意圖觸發

即使沒有明確關鍵字，當 AI 判斷用戶意圖為「安排見面/會議/服務時間」時也應觸發。

### 不觸發的情況

- 用戶只是在聊天中提到日期但沒有預約意圖
- 用戶詢問行事曆但不是要新建預約（如「我明天有什麼行程」→ 這是查詢，不是建立）

---

## 4. 輸入參數

| 參數 | 類型 | 必填 | 預設值 | 說明 |
|------|------|------|--------|------|
| `date` | string / date | 否 | — | 用戶指定的日期，支援自然語言（「下週三」「3/15」） |
| `time` | string / time | 否 | — | 用戶指定的時間，支援模糊表達（「下午」「三點」） |
| `duration` | integer (minutes) | 否 | `calendar_fields.json → default_duration_minutes` | 預約時長 |
| `subject` | string | 否 | 自動生成 | 預約主題 |
| `participants` | array of strings | 否 | [] | 參與者 email 或姓名 |
| `client_name` | string | 否 | — | 客戶姓名（用於事件標題和 CRM） |
| `client_phone` | string | 否 | — | 客戶電話（用於 CRM） |
| `notes` | string | 否 | — | 備註 |

### 參數解析規則

- 日期未指定：詢問用戶
- 時間未指定但日期已知：列出該日所有可用時段
- 時長未指定：使用 `calendar_fields.json` 中的 `default_duration_minutes`
- 主題未指定：使用 `calendar_fields.json` 中的 `event_title_format`

---

## 5. 輸出

### 成功回應

```
確認訊息內容：
- 日期與時間：2026-03-15（週日）14:00 - 15:00
- 事件標題：桑尼工作室 - 王小明 預約
- 參與者：wang@example.com
- Google Calendar 連結：https://calendar.google.com/event?eid=xxxxx
- 下一步提示：如需改期或取消，請直接告訴我
```

### 寫入 CRM 的資料

```json
{
  "timestamp": "2026-03-10T10:30:00+08:00",
  "type": "booking",
  "client_name": "王小明",
  "client_phone": "0912-345-678",
  "booking_date": "2026-03-15",
  "booking_time": "14:00",
  "duration_minutes": 60,
  "subject": "桑尼工作室 - 王小明 預約",
  "status": "confirmed",
  "calendar_event_id": "abc123xyz"
}
```

---

## 6. API 依賴

| API | Scope | 用途 | 權限等級 |
|-----|-------|------|---------|
| Google Calendar API | `calendar.events.readonly` | 查詢空檔（freebusy） | 唯讀 |
| Google Calendar API | `calendar.events` | 建立事件（events.insert） | 寫入 |

### 明確不使用的 Scope

| Scope | 理由 |
|-------|------|
| `calendar.events`（delete） | v1 不支援刪除事件 |
| `calendar.events`（bulk update） | v1 不支援批量修改 |
| `calendar.settings` | 不修改日曆設定 |

---

## 7. 安全限制

### 硬性限制（不可變更）

1. **只能建立事件**：不能刪除、修改、或批量操作任何現有事件
2. **只操作指定行事曆**：只能操作 `calendar_fields.json` 中指定的 `calendar_id`，不能存取其他日曆
3. **時段限制**：只能在 `available_days` 和 `available_hours` 範圍內建立事件
4. **緩衝時間**：事件之間必須保留 `booking_buffer_minutes` 的間隔

### 軟性限制（可在客製版調整）

1. 每日預約上限：預設無上限，客製版可設定
2. 提前預約天數：預設無限制，客製版可設定
3. 重複預約檢測：v1 不檢查，客製版可啟用

---

## 8. 第一版範圍（v1 Scope）

### 包含

- 解析自然語言日期時間
- 查詢 Google Calendar 空檔
- 建立單一事件
- 回覆確認訊息（含 Calendar 連結）
- 寫入 CRM 紀錄

### 不包含（v2 再做）

- 改期功能
- 取消預約功能
- 多人同步（找共同空檔）
- 重複性預約（每週固定時間）
- 自動提醒（預約前一天/一小時提醒）
- 候補名單

---

## 9. 錯誤處理

| 錯誤情況 | 回應策略 |
|----------|---------|
| 用戶指定的時間已被佔用 | 列出最近的 3 個可用時段 |
| 用戶指定的日期不在營業日 | 告知營業日，推薦最近的營業日 |
| 用戶指定的時間不在營業時段 | 告知營業時段，推薦可用時段 |
| 日期時間資訊不完整 | 追問缺少的資訊，一次只問一個問題 |
| Calendar API 連線失敗 | 告知用戶稍後再試，記錄錯誤 |
| 事件建立失敗 | 告知用戶失敗，提供手動預約方式 |

---

## 10. 設定檔依賴

本 Skill 依賴 `calendar_fields.json`，學員必須在課堂上填寫該檔案。

詳見 → `calendar_fields.json`
