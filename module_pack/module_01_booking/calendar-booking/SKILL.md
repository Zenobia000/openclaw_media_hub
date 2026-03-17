---
name: calendar-booking
description: "Parse natural language date/time from user messages, query Google Calendar
  for available slots, create calendar events, and send booking confirmations.
  Use when: user wants to book/schedule an appointment, mentions keywords like
  預約, 約時間, 排時間, 訂時間, 安排, book, schedule, appointment, reserve,
  or when intent is clearly to arrange a meeting/service time.
  NOT for: querying existing calendar events, modifying/cancelling bookings,
  recurring schedules, or general date questions without booking intent.
  Requires: Google Calendar API credentials configured."
metadata:
  openclaw:
    emoji: "📅"
    requires:
      bins: ["python3"]
---

# Calendar Booking Skill

## 概述

完整預約流程：解析意圖 → 提取日期時間 → 查詢空檔 → 推薦時段 → 用戶確認 → 建立事件 → 回覆確認 → 寫入 CRM。

## 設定

每次預約流程開始時載入 `references/calendar_fields.json`，包含：

| 欄位 | 說明 |
|------|------|
| `business_name` | 事件標題用 |
| `calendar_id` | 目標 Google Calendar |
| `available_days` / `available_hours` | 可預約範圍 |
| `default_duration_minutes` | 未指定時長時的預設值 |
| `booking_buffer_minutes` | 事件間最小間隔 |
| `event_title_format` | 事件標題模板 |
| `timezone` | 時區 |
| `confirmation_language` | 回覆語言 |
| `credentials_file` / `token_file` | OAuth2 認證路徑（相對於 skill 目錄） |

若 `business_name` 為空，先請用戶設定。

### 初始化（首次設定）

技能首次使用前需完成 OAuth2 授權。按照以下步驟執行：

#### 前置條件

安裝 Python 依賴：

```bash
python3 -m pip install --break-system-packages google-api-python-client google-auth-oauthlib
```

#### Step 0：確認 credentials 檔案

檢查 `{skill_dir}/{credentials_file}` 是否存在。若不存在，請用戶：
1. 前往 [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. 建立 OAuth 2.0 Client ID（Desktop App 類型）
3. 啟用 Google Calendar API
4. 下載 client secret JSON 檔案
5. 將檔案放至 `{skill_dir}/` 並更新 `calendar_fields.json` 中的 `credentials_file` 欄位

#### Step 1：產生授權網址

```bash
python3 {skill_dir}/scripts/gcal_setup.py \
  --credentials "{skill_dir}/{credentials_file}" \
  --token "{skill_dir}/{token_file}" \
  --step auth-url
```

輸出 JSON 含 `auth_url`。將此網址提供給用戶，請其在瀏覽器中開啟並完成 Google 帳號授權，然後複製頁面上的授權碼（authorization code）。

#### Step 2：用授權碼換取 Token

用戶提供授權碼後執行：

```bash
python3 {skill_dir}/scripts/gcal_setup.py \
  --credentials "{skill_dir}/{credentials_file}" \
  --token "{skill_dir}/{token_file}" \
  --step exchange \
  --code "{AUTHORIZATION_CODE}"
```

成功後 token 儲存至 `{skill_dir}/{token_file}`。

#### Step 3：驗證連線

```bash
python3 {skill_dir}/scripts/gcal_setup.py \
  --credentials "{skill_dir}/{credentials_file}" \
  --token "{skill_dir}/{token_file}" \
  --step verify \
  --calendar-id "{calendar_id}"
```

輸出含行事曆名稱與時區，確認連線正常。

#### 初始化判斷邏輯

每次預約流程開始時，先檢查 `{skill_dir}/{token_file}` 是否存在：
- **存在** → 直接進入預約流程（Step 1 起）
- **不存在** → 引導用戶完成上述初始化步驟

## 工作流程

### Step 1：偵測預約意圖

觸發關鍵字：預約、約時間、排時間、訂時間、安排、約一下、book、schedule、appointment、reserve。意圖明確時也觸發。僅查詢行事曆或隨意提及日期時不觸發。

### Step 2：提取參數

| 參數 | 必填 | 預設值 |
|------|:----:|--------|
| `date` | 否 — 缺則詢問 | — |
| `time` | 否 — 缺則列出所有時段 | — |
| `duration` | 否 | `default_duration_minutes` |
| `client_name` | 否 — 建立前詢問 | — |
| `client_phone` | 否 | — |
| `subject` | 否 | 由 `event_title_format` 生成 |
| `notes` | 否 | — |

自然語言日期解析基於當前日期與 `timezone`。**一次只問一個問題。**

### Step 3：查詢空檔

```bash
python3 {skill_dir}/scripts/gcal_freebusy.py \
  --credentials "{skill_dir}/{credentials_file}" \
  --token "{skill_dir}/{token_file}" \
  --calendar-id "{calendar_id}" \
  --date "{YYYY-MM-DD}" \
  --timezone "{timezone}" \
  --start-hour "{available_hours.start}" \
  --end-hour "{available_hours.end}" \
  --duration "{duration_minutes}" \
  --buffer "{booking_buffer_minutes}"
```

輸出：可用時段 JSON 陣列。

### Step 4：推薦時段

顯示 2–3 個可用時段，格式見 `references/confirmation_prompts.md` § 2.1。無可用時段則顯示最近可用日期（§ 4.2）。

### Step 5：確認

用戶選定後顯示確認摘要（§ 2.2），取得明確同意。若尚無 `client_name` 則詢問。

### Step 6：建立事件

```bash
python3 {skill_dir}/scripts/gcal_create_event.py \
  --credentials "{skill_dir}/{credentials_file}" \
  --token "{skill_dir}/{token_file}" \
  --calendar-id "{calendar_id}" \
  --title "{event_title}" \
  --start "{ISO-8601 start}" \
  --end "{ISO-8601 end}" \
  --timezone "{timezone}" \
  --description "{notes}" \
  --attendees "{comma-separated emails}"
```

輸出：JSON 含 `event_id` 與 `calendar_link`。

### Step 7：回覆確認

使用 `references/confirmation_prompts.md` § 2.3 格式，包含 Calendar 連結。

### Step 8：寫入 CRM

將以下紀錄 append 至 CRM 系統（Module 03）：

```json
{
  "timestamp": "{ISO-8601}",
  "type": "booking",
  "client_name": "{name}",
  "client_phone": "{phone}",
  "booking_date": "{YYYY-MM-DD}",
  "booking_time": "{HH:MM}",
  "duration_minutes": "{N}",
  "subject": "{title}",
  "status": "confirmed",
  "calendar_event_id": "{id}"
}
```

## 安全限制

1. **僅建立** — 不刪除、不修改、不批量操作現有事件
2. **單一行事曆** — 只操作 `calendar_id` 指定的日曆
3. **營業時段內** — 拒絕 `available_days` 和 `available_hours` 範圍外的預約
4. **強制緩衝** — 事件間隔 ≥ `booking_buffer_minutes`
5. **需用戶確認** — 建立前必須取得明確同意

## 錯誤處理

| 情況 | 處理 |
|------|------|
| 時間已佔用 | 顯示最近 3 個可用時段（§ 4.1） |
| 非營業日 | 告知營業日，推薦最近營業日（§ 4.3） |
| 非營業時段 | 告知時段，推薦可用時段（§ 4.4） |
| 缺日期 | 附範例詢問（§ 4.5） |
| 缺時間 | 列出該日時段（§ 4.6） |
| 缺姓名 | 詢問姓名（§ 4.7） |
| API 失敗 | 致歉並提供替代方案（§ 4.8） |

## 參考資源

- `references/calendar_fields.json` — 每次預約流程開始時載入，包含所有營業設定。
- `references/confirmation_prompts.md` — 組合回覆訊息時載入，包含 system prompt、回覆模板、邊界處理模板。

## 腳本架構

```
scripts/
├── gcal_setup.py          # OAuth2 初始化（auth-url → exchange → verify）
├── gcal_auth.py           # 共用認證模組（OAuth2 + Service Account）
├── gcal_freebusy.py       # 查詢空檔時段
└── gcal_create_event.py   # 建立日曆事件
```

- `gcal_setup.py` 負責首次授權流程，分三步驟執行（非互動式，適合 agent 調用）。
- `gcal_auth.py` 提供 `load_credentials()` 函數，自動偵測認證類型，供 freebusy 與 create_event 共用。
