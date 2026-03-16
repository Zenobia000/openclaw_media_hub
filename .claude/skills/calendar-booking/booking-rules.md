# 預約規則與限制快速參考

---

## 輸入參數表

| 參數 | 類型 | 必填 | 預設值 | 說明 |
|------|------|------|--------|------|
| `date` | string / date | 否 | — | 用戶指定的日期，支援自然語言（「下週三」「3/15」） |
| `time` | string / time | 否 | — | 用戶指定的時間，支援模糊表達（「下午」「三點」） |
| `duration` | integer (minutes) | 否 | `calendar_fields.json → default_duration_minutes` | 預約時長 |
| `subject` | string | 否 | 自動生成（使用 `event_title_format`） | 預約主題 |
| `participants` | array of strings | 否 | [] | 參與者 email 或姓名 |
| `client_name` | string | 否 | — | 客戶姓名（用於事件標題和 CRM） |
| `client_phone` | string | 否 | — | 客戶電話（用於 CRM） |
| `notes` | string | 否 | — | 備註 |

---

## 參數解析規則

| 情況 | 處理方式 |
|------|---------|
| 日期未指定 | 詢問用戶 |
| 時間未指定但日期已知 | 列出該日所有可用時段 |
| 時長未指定 | 使用 `calendar_fields.json` 中的 `default_duration_minutes` |
| 主題未指定 | 使用 `calendar_fields.json` 中的 `event_title_format` |

---

## 安全硬性限制（不可變更）

1. **只能建立事件**：不能刪除、修改、或批量操作任何現有事件
2. **只操作指定行事曆**：只能操作 `calendar_fields.json` 中指定的 `calendar_id`，不能存取其他日曆
3. **時段限制**：只能在 `available_days` 和 `available_hours` 範圍內建立事件
4. **緩衝時間**：事件之間必須保留 `booking_buffer_minutes` 的間隔

---

## 錯誤處理表

| 錯誤情況 | 回應策略 |
|----------|---------|
| 用戶指定的時間已被佔用 | 列出最近的 3 個可用時段 |
| 用戶指定的日期不在營業日 | 告知營業日，推薦最近的營業日 |
| 用戶指定的時間不在營業時段 | 告知營業時段，推薦可用時段 |
| 日期時間資訊不完整 | 追問缺少的資訊，一次只問一個問題 |
| Calendar API 連線失敗 | 告知用戶稍後再試，記錄錯誤 |
| 事件建立失敗 | 告知用戶失敗，提供手動預約方式 |

---

## v1 範圍界定

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
