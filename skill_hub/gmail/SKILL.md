---
name: gmail
description: |
  透過 Google OAuth2 直接存取 Gmail API。讀取、寄送、管理郵件、對話串、標籤與草稿。
  使用時機：使用者需要操作 Gmail（收發信、搜尋郵件、管理標籤、處理草稿、查看對話串）。
  不適用：信件分類與 AI 摘要（使用 email-triage skill）、
  草擬專業回覆（使用 email-reply-draft skill）、其他 Google 服務。
metadata:
  author: openclaw
  version: "2.0"
  openclaw:
    emoji: 📧
    requires:
      bins: ["python3"]
---

# Gmail

透過 Google OAuth2 直接存取 Gmail API，支援郵件讀取、寄送、管理、對話串、標籤與草稿操作。

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
詳細步驟請參考：`2.金鑰取得/3.Google/文件.md`

將下載的檔案放置於 skill 目錄，命名為 `credentials.json`。

### 三步驟 OAuth 初始化

```bash
# 步驟 1：產生授權網址
python3 skill_hub/gmail/scripts/gmail_setup.py \
    --credentials skill_hub/gmail/credentials.json \
    --token skill_hub/gmail/token.json \
    --step auth-url

# 步驟 2：使用者在瀏覽器完成授權後，用授權碼換取 token
python3 skill_hub/gmail/scripts/gmail_setup.py \
    --credentials skill_hub/gmail/credentials.json \
    --token skill_hub/gmail/token.json \
    --step exchange --code "使用者提供的授權碼"

# 步驟 3：驗證連線
python3 skill_hub/gmail/scripts/gmail_setup.py \
    --credentials skill_hub/gmail/credentials.json \
    --token skill_hub/gmail/token.json \
    --step verify
```

預設 scopes：`gmail.modify`、`gmail.compose`、`gmail.labels`。可用 `--scopes` 覆寫。

## 郵件操作

### 列出郵件

```bash
python3 skill_hub/gmail/scripts/gmail_list_messages.py \
    --credentials skill_hub/gmail/credentials.json \
    --token skill_hub/gmail/token.json \
    --max-results 20 \
    --query "is:unread"
```

參數：
- `--query`：Gmail 查詢條件（預設空字串，全部郵件）
- `--max-results`：最多回傳幾封（預設 20）
- `--time-range`：往回查看的時間範圍（如 `24h`、`7d`）
- `--label-ids`：篩選標籤 ID（逗號分隔，如 `INBOX,UNREAD`）
- `--page-token`：分頁 token（從前次回應的 `next_page_token` 取得）

### 取得郵件詳情

```bash
python3 skill_hub/gmail/scripts/gmail_get_message.py \
    --credentials skill_hub/gmail/credentials.json \
    --token skill_hub/gmail/token.json \
    --message-id "MESSAGE_ID"
```

參數：
- `--format`：`full`（預設，含 body）| `metadata`（僅標頭）| `raw`（原始 MIME）
- `--metadata-headers`：選擇性取得的標頭（逗號分隔），僅 `metadata` 格式有效
- `--truncate`：內文截斷字數（預設 500）

### 寄送郵件

```bash
python3 skill_hub/gmail/scripts/gmail_send_message.py \
    --credentials skill_hub/gmail/credentials.json \
    --token skill_hub/gmail/token.json \
    --to "recipient@example.com" \
    --subject "郵件主旨" \
    --body "郵件內文"
```

參數：
- `--to`（必要）、`--subject`（必要）、`--body`（必要）
- `--cc`、`--bcc`：副本/密件副本收件人
- `--in-reply-to`、`--references`：回覆郵件時設定的 header
- `--thread-id`：確保回覆在同一對話串

### 管理郵件

```bash
# 修改標籤
python3 skill_hub/gmail/scripts/gmail_manage_message.py \
    --credentials skill_hub/gmail/credentials.json \
    --token skill_hub/gmail/token.json \
    --message-id "MESSAGE_ID" \
    --action modify-labels \
    --add-labels "STARRED" --remove-labels "UNREAD"

# 移至垃圾桶
python3 skill_hub/gmail/scripts/gmail_manage_message.py \
    --credentials skill_hub/gmail/credentials.json \
    --token skill_hub/gmail/token.json \
    --message-id "MESSAGE_ID" --action trash

# 從垃圾桶還原
python3 skill_hub/gmail/scripts/gmail_manage_message.py \
    --credentials skill_hub/gmail/credentials.json \
    --token skill_hub/gmail/token.json \
    --message-id "MESSAGE_ID" --action untrash

# 封存（從收件匣移除）
python3 skill_hub/gmail/scripts/gmail_manage_message.py \
    --credentials skill_hub/gmail/credentials.json \
    --token skill_hub/gmail/token.json \
    --message-id "MESSAGE_ID" --action archive
```

動作：
- `modify-labels`：修改標籤（搭配 `--add-labels`、`--remove-labels`、`--create-if-missing`）
- `trash`：移至垃圾桶
- `untrash`：從垃圾桶還原
- `archive`：封存（移除 INBOX 標籤）

## 對話串

### 列出對話串

```bash
python3 skill_hub/gmail/scripts/gmail_threads.py \
    --credentials skill_hub/gmail/credentials.json \
    --token skill_hub/gmail/token.json \
    --action list --max-results 10 --query "is:unread"
```

### 取得對話串詳情

```bash
python3 skill_hub/gmail/scripts/gmail_threads.py \
    --credentials skill_hub/gmail/credentials.json \
    --token skill_hub/gmail/token.json \
    --action get --thread-id "THREAD_ID"
```

參數：
- `--format`：`full`（預設）| `metadata`
- `--truncate`：每封郵件內文截斷字數（預設 500）
- `--page-token`：分頁 token（list 動作用）

## 標籤

```bash
# 列出所有標籤
python3 skill_hub/gmail/scripts/gmail_labels.py \
    --credentials skill_hub/gmail/credentials.json \
    --token skill_hub/gmail/token.json \
    --action list

# 建立標籤
python3 skill_hub/gmail/scripts/gmail_labels.py \
    --credentials skill_hub/gmail/credentials.json \
    --token skill_hub/gmail/token.json \
    --action create --label-name "AI/Reports"

# 取得標籤詳情
python3 skill_hub/gmail/scripts/gmail_labels.py \
    --credentials skill_hub/gmail/credentials.json \
    --token skill_hub/gmail/token.json \
    --action get --label-id "Label_123"

# 更新標籤
python3 skill_hub/gmail/scripts/gmail_labels.py \
    --credentials skill_hub/gmail/credentials.json \
    --token skill_hub/gmail/token.json \
    --action update --label-id "Label_123" --label-name "AI/Summary"

# 刪除標籤
python3 skill_hub/gmail/scripts/gmail_labels.py \
    --credentials skill_hub/gmail/credentials.json \
    --token skill_hub/gmail/token.json \
    --action delete --label-id "Label_123"
```

動作：`list` | `create` | `get` | `update` | `delete`
參數：`--label-id`、`--label-name`、`--visibility`（labelShow/labelShowIfUnread/labelHide）、`--message-visibility`（show/hide）

## 草稿

```bash
# 建立草稿
python3 skill_hub/gmail/scripts/gmail_drafts.py \
    --credentials skill_hub/gmail/credentials.json \
    --token skill_hub/gmail/token.json \
    --action create --to "user@example.com" \
    --subject "草稿主旨" --body "草稿內文"

# 列出草稿
python3 skill_hub/gmail/scripts/gmail_drafts.py \
    --credentials skill_hub/gmail/credentials.json \
    --token skill_hub/gmail/token.json \
    --action list

# 取得草稿
python3 skill_hub/gmail/scripts/gmail_drafts.py \
    --credentials skill_hub/gmail/credentials.json \
    --token skill_hub/gmail/token.json \
    --action get --draft-id "DRAFT_ID"

# 寄送草稿
python3 skill_hub/gmail/scripts/gmail_drafts.py \
    --credentials skill_hub/gmail/credentials.json \
    --token skill_hub/gmail/token.json \
    --action send --draft-id "DRAFT_ID"

# 刪除草稿
python3 skill_hub/gmail/scripts/gmail_drafts.py \
    --credentials skill_hub/gmail/credentials.json \
    --token skill_hub/gmail/token.json \
    --action delete --draft-id "DRAFT_ID"
```

動作：`create` | `list` | `get` | `send` | `delete`
create 參數：`--to`、`--subject`、`--body`、`--cc`、`--bcc`、`--in-reply-to`、`--thread-id`

## 個人資料

```bash
python3 skill_hub/gmail/scripts/gmail_profile.py \
    --credentials skill_hub/gmail/credentials.json \
    --token skill_hub/gmail/token.json
```

回傳：`email_address`、`messages_total`、`threads_total`、`history_id`

## 查詢運算子

用於 `--query` 參數：

| 運算子                  | 說明         |
| ----------------------- | ------------ |
| `is:unread`             | 未讀郵件     |
| `is:starred`            | 已加星號     |
| `from:user@example.com` | 指定寄件者   |
| `to:user@example.com`   | 指定收件者   |
| `subject:keyword`       | 主旨含關鍵字 |
| `after:2024/01/01`      | 指定日期之後 |
| `before:2024/12/31`     | 指定日期之前 |
| `has:attachment`         | 含附件       |
| `label:標籤名稱`        | 指定標籤     |

可組合使用：`is:unread from:boss@company.com after:2024/03/01`

## 錯誤處理

所有腳本錯誤時回傳：
```json
{"ok": false, "error": "錯誤描述"}
```

常見錯誤：
- `google-api-python-client 未安裝`：執行 `pip install google-api-python-client`
- `找不到認證檔案`：確認 `--credentials` 路徑正確
- `Token 無效`：重新執行 `gmail_setup.py` 三步驟
- `權限不足`：確認 OAuth scopes 包含所需權限

## 通用參數

所有腳本共用：
- `--credentials`（必要）：OAuth2 client secret JSON 路徑
- `--token`（預設 `token.json`）：Token 儲存路徑
- `--scopes`（選填）：覆寫預設 scopes（逗號分隔）
- `--dry-run`：不呼叫 API，僅驗證參數並回傳設定 JSON

## 腳本一覽

| 腳本 | 功能 |
|------|------|
| `gmail_auth.py` | OAuth2 認證模組（供其他腳本匯入） |
| `gmail_setup.py` | OAuth2 三步驟初始化 |
| `gmail_profile.py` | 取得個人資料 |
| `gmail_list_messages.py` | 列出/搜尋/篩選郵件 |
| `gmail_get_message.py` | 取得單封郵件詳情 |
| `gmail_send_message.py` | 撰寫並寄送郵件 |
| `gmail_manage_message.py` | 修改標籤/垃圾桶/封存 |
| `gmail_threads.py` | 對話串列出/取得 |
| `gmail_labels.py` | 標籤 CRUD |
| `gmail_drafts.py` | 草稿 CRUD + 寄送 |
