---
name: gsheets
description: |
  透過 Google OAuth2 直接存取 Google Sheets API。讀取、寫入、查詢、更新試算表資料。
  使用時機：使用者需要操作 Google Sheets（新增列、查詢資料、更新欄位）。
  不適用：CRM 業務邏輯與 Lead 評分（使用 lead-capture skill）、其他 Google 服務。
metadata:
  author: openclaw
  version: "1.0"
  openclaw:
    emoji: 📊
    requires:
      bins: ["python3"]
---

# Google Sheets

透過 Google OAuth2 直接存取 Google Sheets API，支援新增列、查詢、更新欄位。

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
啟用 Google Sheets API，將下載的檔案放置於 skill 目錄，命名為 `credentials.json`。

### 三步驟 OAuth 初始化

```bash
# 步驟 1：產生授權網址
python3 skill_hub/gsheets/scripts/gsheets_setup.py \
    --credentials skill_hub/gsheets/credentials.json \
    --token skill_hub/gsheets/token.json \
    --step auth-url

# 步驟 2：使用者在瀏覽器完成授權後，用授權碼換取 token
python3 skill_hub/gsheets/scripts/gsheets_setup.py \
    --credentials skill_hub/gsheets/credentials.json \
    --token skill_hub/gsheets/token.json \
    --step exchange --code "使用者提供的授權碼"

# 步驟 3：驗證連線
python3 skill_hub/gsheets/scripts/gsheets_setup.py \
    --credentials skill_hub/gsheets/credentials.json \
    --token skill_hub/gsheets/token.json \
    --step verify --spreadsheet-id "SPREADSHEET_ID"
```

## 新增資料列

```bash
python3 skill_hub/gsheets/scripts/gsheets_append.py \
    --credentials skill_hub/gsheets/credentials.json \
    --token skill_hub/gsheets/token.json \
    --spreadsheet-id "SPREADSHEET_ID" \
    --sheet-name "Sheet1" \
    --fields "name,email,date,notes" \
    --data '{"name":"王大明","email":"wang@example.com","date":"2026-03-18","notes":"備註"}'
```

參數：
- `--spreadsheet-id`（必要）：Google Sheets ID
- `--sheet-name`：目標 Sheet 名稱（預設 `Sheet1`）
- `--fields`（必要）：欄位順序（逗號分隔），對應 A, B, C... 欄
- `--data`（必要）：JSON 字串，含欄位資料
- `--dry-run`：僅顯示將寫入的資料，不實際執行

## 查詢資料

```bash
python3 skill_hub/gsheets/scripts/gsheets_query.py \
    --credentials skill_hub/gsheets/credentials.json \
    --token skill_hub/gsheets/token.json \
    --spreadsheet-id "SPREADSHEET_ID" \
    --sheet-name "Sheet1" \
    --fields "name,email,status,followup_date"
```

參數：
- `--fields`（必要）：欄位名稱（逗號分隔），對應表頭 A, B, C...
- `--filter-field` / `--filter-value`：按欄位值過濾
- `--overdue-field`：逾期判斷用的日期欄位名稱
- `--closed-statuses`：結案狀態（逗號分隔），逾期過濾時排除
- `--status-field`：狀態欄位名稱（預設 `status`）
- `--tz-offset`：時區偏移小時數（預設 `8`）
- `--dry-run`：僅顯示查詢參數

## 更新欄位

```bash
python3 skill_hub/gsheets/scripts/gsheets_update.py \
    --credentials skill_hub/gsheets/credentials.json \
    --token skill_hub/gsheets/token.json \
    --spreadsheet-id "SPREADSHEET_ID" \
    --sheet-name "Sheet1" \
    --field-map '{"name":"A","email":"B","status":"C","notes":"D"}' \
    --row 5 --field status --value "active"
```

參數：
- `--field-map`（必要）：欄位→欄號對應 JSON
- `--row`（必要）：列號（1-based，含表頭，須 >= 2）
- `--field`（必要）：要更新的欄位名稱
- `--value`（必要）：新值
- `--protected-fields`：受保護欄位（逗號分隔），拒絕更新
- `--append-mode`：追加模式（在現有值後追加，非覆蓋）
- `--dry-run`：僅顯示將更新的內容

## 錯誤處理

所有腳本錯誤時回傳：
```json
{"ok": false, "error": "錯誤描述"}
```

## 通用參數

所有腳本共用：
- `--credentials`（必要）：OAuth2 client secret JSON 路徑
- `--token`（必要）：Token 儲存路徑
- `--dry-run`：不呼叫 API，僅驗證參數

## 腳本一覽

| 腳本 | 功能 |
|------|------|
| `gsheets_auth.py` | OAuth2 認證模組（供其他腳本匯入） |
| `gsheets_setup.py` | OAuth2 三步驟初始化 |
| `gsheets_append.py` | 新增一列資料 |
| `gsheets_query.py` | 查詢/過濾/逾期追蹤 |
| `gsheets_update.py` | 更新單一欄位（支援保護欄位、追加模式） |
