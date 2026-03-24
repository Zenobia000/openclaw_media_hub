---
name: gcal
description: |
  透過 Google OAuth2 直接存取 Google Calendar API。查詢空檔時段、建立事件。
  使用時機：使用者需要操作 Google Calendar（查詢可用時段、建立日曆事件）。
  不適用：預約排程業務邏輯（使用 calendar-booking skill）、其他 Google 服務。
metadata:
  author: openclaw
  version: "1.0"
  openclaw:
    emoji: 📅
    requires:
      bins: ["python3"]
---

# Google Calendar

透過 Google OAuth2 直接存取 Google Calendar API，支援空檔查詢與事件建立。

## 前置條件

```bash
pip install google-auth google-auth-oauthlib google-api-python-client
```

## 設定流程

### 判斷是否已設定

檢查 `token.json` 是否存在於 skill 目錄中：
- **存在**：直接使用，跳至操作章節
- **不存在**：進入下方 OAuth 設定

### 取得 credentials.json

使用者需從 Google Cloud Console 下載 OAuth2 Desktop App 的 client secret JSON。
將下載的檔案放置於 skill 目錄，命名為 `credentials.json`。

### 三步驟 OAuth 初始化

```bash
# 步驟 1：產生授權網址
python3 skill_hub/gcal/scripts/gcal_setup.py \
    --credentials skill_hub/gcal/credentials.json \
    --token skill_hub/gcal/token.json \
    --step auth-url

# 步驟 2：使用者在瀏覽器完成授權後，用授權碼換取 token
python3 skill_hub/gcal/scripts/gcal_setup.py \
    --credentials skill_hub/gcal/credentials.json \
    --token skill_hub/gcal/token.json \
    --step exchange --code "使用者提供的授權碼"

# 步驟 3：驗證連線
python3 skill_hub/gcal/scripts/gcal_setup.py \
    --credentials skill_hub/gcal/credentials.json \
    --token skill_hub/gcal/token.json \
    --step verify --calendar-id primary
```

預設 scope：`calendar`。可用 `--scopes` 覆寫。

## 查詢空檔時段

```bash
python3 skill_hub/gcal/scripts/gcal_freebusy.py \
    --credentials skill_hub/gcal/credentials.json \
    --token skill_hub/gcal/token.json \
    --calendar-id primary \
    --date "2026-03-18" \
    --timezone "Asia/Taipei" \
    --start-hour "09:00" --end-hour "18:00" \
    --duration 60 --buffer 15
```

參數：
- `--calendar-id`（必要）：Google Calendar ID
- `--date`（必要）：查詢日期（YYYY-MM-DD）
- `--timezone`：時區（預設 `Asia/Taipei`）
- `--start-hour`：查詢開始時間（預設 `09:00`）
- `--end-hour`：查詢結束時間（預設 `18:00`）
- `--duration`：時段長度，分鐘（預設 60）
- `--buffer`：時段間隔，分鐘（預設 15）
- `--dry-run`：跳過 API，回傳所有可能時段

## 建立事件

```bash
python3 skill_hub/gcal/scripts/gcal_create_event.py \
    --credentials skill_hub/gcal/credentials.json \
    --token skill_hub/gcal/token.json \
    --calendar-id primary \
    --title "會議標題" \
    --start "2026-03-18T14:00:00" \
    --end "2026-03-18T15:00:00" \
    --timezone "Asia/Taipei"
```

參數：
- `--calendar-id`（必要）、`--title`（必要）、`--start`（必要）、`--end`（必要）
- `--timezone`：時區（預設 `Asia/Taipei`）
- `--description`：事件描述
- `--attendees`：參與者 email（逗號分隔）
- `--dry-run`：僅輸出事件內容，不實際建立

## 錯誤處理

所有腳本錯誤時回傳：
```json
{"ok": false, "error": "錯誤描述"}
```

常見錯誤：
- `google-api-python-client 未安裝`：執行 `pip install google-api-python-client`
- `找不到認證檔案`：確認 `--credentials` 路徑正確
- `Token 無效`：重新執行 `gcal_setup.py` 三步驟
- `權限不足`：確認 OAuth scopes 包含所需權限

## 通用參數

所有腳本共用：
- `--credentials`（必要）：OAuth2 client secret JSON 路徑
- `--token`（預設 `token.json`）：Token 儲存路徑
- `--dry-run`：不呼叫 API，僅驗證參數

## 腳本一覽

| 腳本 | 功能 |
|------|------|
| `gcal_auth.py` | OAuth2 認證模組（供其他腳本匯入） |
| `gcal_setup.py` | OAuth2 三步驟初始化 |
| `gcal_freebusy.py` | 查詢空檔時段 |
| `gcal_create_event.py` | 建立日曆事件 |
