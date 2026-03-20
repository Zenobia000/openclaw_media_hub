---
name: email-triage
description: "讀取 Gmail 收件匣中的未讀電子郵件，產生 AI 摘要，將其分類（詢價/支援/預約/垃圾郵件/其他），分配優先等級（高/中/低），並輸出結構化的分類清單。
  使用時機：使用者想要檢查電子郵件，或提到如「看信」、「收信」、「信箱」、「有沒有新信」、「整理信箱」、「信件摘要」、「check email」、「inbox」、「email summary」、「triage」等關鍵字，或是意圖明確為檢視收到的電子郵件時。
  不適用於：回覆電子郵件（請使用 email-reply-draft）、發送新電子郵件、修改/刪除電子郵件、管理電子郵件設定，或閱讀特定已知主旨的電子郵件。
  需求：需要設定 Gmail API 憑證（gmail.modify + gmail.labels）。"
metadata:
  openclaw:
    emoji: "📧"
    requires:
      bins: ["python3"]
---

# Email Triage Skill

## 概述

讀信分類流程：連線 Gmail → 取得未讀郵件 → 逐封讀取 → AI 摘要 → 分類 → 優先級標註 → 輸出結構化清單 → （可選）加標籤。

## 設定

每次執行時載入 `references/email_fields.json`，包含：

| 欄位 | 說明 |
|------|------|
| `business_name` | 商家名稱，用於 system prompt |
| `business_email` | 商家信箱 |
| `timezone` | 時區（預設 Asia/Taipei） |
| `max_emails` | 單次最多處理幾封（預設 20） |
| `unread_only` | 是否只處理未讀（預設 true） |
| `time_range` | 往回查看時間範圍（預設 24h） |
| `body_truncate_chars` | 內文截斷字數（預設 500） |
| `categories` | 分類陣列（詢價/售後/預約/垃圾/其他） |
| `priority_rules` | 優先級判斷關鍵字 |
| `gmail_scopes` | Gmail API scopes |
| `credentials_file` / `token_file` | OAuth2 認證路徑（相對於 skill 目錄） |

若 `business_name` 為空，先請用戶設定。

### 初始化（首次設定）

技能首次使用前需完成兩階段設定：**基本設定**（email_fields.json）與 **OAuth2 授權**。

#### 初始化判斷邏輯（入口）

每次技能啟動時，依序檢查：

1. **`email_fields.json` 是否已填寫** — 檢查 `business_name` 是否為空字串
   - 未填寫 → 進入「Step 0-A：互動式設定」
   - 已填寫 → 跳到 Step 0-B
2. **`{skill_dir}/{credentials_file}` 是否存在** → 不存在則進入 Step 0-B
3. **`{skill_dir}/{token_file}` 是否存在** → 不存在則進入 Step 1（OAuth2 授權）
4. 全部存在 → 直接進入分類工作流程

#### Step 0-A：互動式設定

逐一詢問用戶以下欄位，**一次只問一個問題**，每個問題附上說明與範例。用戶可跳過選填項（使用預設值）。

1. **business_name**（必填）
   > 請問您的商家或工作室名稱是什麼？
   > 例如：「桑尼工作室」

2. **business_email**（必填）
   > 您的商業信箱是什麼？
   > 例如：「hello@sunny-studio.com」

3. **timezone**（選填，預設 `Asia/Taipei`）
   > 您的時區是？預設：Asia/Taipei

4. **max_emails**（選填，預設 20）
   > 每次最多處理幾封信？預設：20

5. **time_range**（選填，預設 `24h`）
   > 預設查看多久以內的信？例如：24h、48h、7d
   > 預設：24h

收集完成後寫入 `references/email_fields.json`，顯示摘要讓用戶確認後儲存。

#### 前置條件

安裝 Python 依賴：

```bash
python3 -m pip install --break-system-packages google-api-python-client google-auth-oauthlib
```

#### Step 0-B：確認 credentials 檔案

檢查 `{skill_dir}/{credentials_file}` 是否存在。若不存在，請用戶：
1. 前往 [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. 建立 OAuth 2.0 Client ID（Desktop App 類型）
3. 啟用 Gmail API
4. 下載 client secret JSON 檔案
5. 將 JSON 內容直接貼上，由 agent 寫入 `{skill_dir}/{credentials_file}`

#### Step 1：產生授權網址

> ⚠️ **注意**：授權時必須包含 `gmail.modify` scope（而非 `gmail.readonly`），否則加標籤步驟會因權限不足（403 insufficientPermissions）失敗。`email_fields.json` 預設的 `gmail_scopes` 已設為 `gmail.modify` + `gmail.labels`，直接使用即可。

```bash
python3 {skill_dir}/scripts/gmail_setup.py \
  --credentials "{skill_dir}/{credentials_file}" \
  --token "{skill_dir}/{token_file}" \
  --scopes "{gmail_scopes 以逗號分隔}" \
  --step auth-url
```

輸出 JSON 含 `auth_url`。將此網址提供給用戶，請其在瀏覽器中開啟並完成 Google 帳號授權，然後複製頁面上的授權碼。

#### Step 2：用授權碼換取 Token

```bash
python3 {skill_dir}/scripts/gmail_setup.py \
  --credentials "{skill_dir}/{credentials_file}" \
  --token "{skill_dir}/{token_file}" \
  --scopes "{gmail_scopes 以逗號分隔}" \
  --step exchange \
  --code "{AUTHORIZATION_CODE}"
```

#### Step 3：驗證連線

```bash
python3 {skill_dir}/scripts/gmail_setup.py \
  --credentials "{skill_dir}/{credentials_file}" \
  --token "{skill_dir}/{token_file}" \
  --scopes "{gmail_scopes 以逗號分隔}" \
  --step verify
```

輸出含 email_address 與 messages_total，確認連線正常。

#### 初始化完成

三項檢查（email_fields 已填、credentials 存在、token 存在）全部通過後，進入分類工作流程。

## 工作流程

### Step 1：載入設定

讀取 `references/email_fields.json`，取得分類規則、優先級關鍵字、Gmail scopes 等設定。

### Step 2：列出未讀郵件

```bash
python3 {skill_dir}/scripts/gmail_list_messages.py \
  --credentials "{skill_dir}/{credentials_file}" \
  --token "{skill_dir}/{token_file}" \
  --scopes "{gmail_scopes 以逗號分隔}" \
  --max-results {max_emails} \
  --query "is:unread" \
  --time-range "{time_range}"
```

輸出 JSON 含 `messages` 陣列（`message_id` + `thread_id`）。若為空，回覆「沒有新信件」（見 `triage_prompts.md` § 4.1）。

### Step 3：逐封讀取詳情

對每個 message_id 執行：

```bash
python3 {skill_dir}/scripts/gmail_get_message.py \
  --credentials "{skill_dir}/{credentials_file}" \
  --token "{skill_dir}/{token_file}" \
  --scopes "{gmail_scopes 以逗號分隔}" \
  --message-id "{message_id}" \
  --truncate {body_truncate_chars}
```

取得 from、subject、date、body_snippet 等欄位。單封失敗時跳過並記錄。

### Step 4：AI 摘要與分類

根據每封郵件的 subject + body_snippet，由 Agent 自身能力判斷：
- **摘要**：1-2 句精準描述核心意圖
- **分類**：對照 `email_fields.json` 的 `categories` 歸類
- **優先級**：對照 `priority_rules` 的 `high_keywords` / `low_keywords` 判斷

分類信心度低時歸入「其他」，標註「AI 不確定」。

### Step 5：組合輸出

載入 `references/triage_prompts.md`，使用 § 2.1 人類可讀模板組合摘要清單回覆用戶。同時產生 § 2.2 結構化 JSON 供 email-reply-draft 使用（保存在對話 context 中）。

### Step 6：（可選）加標籤

若用戶同意，對每封郵件加上對應的 Gmail 標籤：

```bash
python3 {skill_dir}/scripts/gmail_modify_labels.py \
  --credentials "{skill_dir}/{credentials_file}" \
  --token "{skill_dir}/{token_file}" \
  --scopes "{gmail_scopes 以逗號分隔}" \
  --message-id "{message_id}" \
  --add-labels "{category_label}" \
  --create-if-missing
```

### Step 7：完成

輸出完整摘要清單，提示用戶可說「幫我回這封」觸發 email-reply-draft。

## 安全限制

1. **只讀不寫** — 不修改、不刪除、不封存、不移動郵件
2. **只加標籤** — 唯一的寫入操作是加 AI 分類標籤
3. **內文截斷** — 只讀取每封信的前 `body_truncate_chars` 字
4. **附件不讀** — 不下載、不開啟、不解析附件
5. **不存原文** — 摘要後不保留郵件原文
6. **需用戶同意** — 加標籤前須取得同意

## 錯誤處理

| 情況 | 處理 |
|------|------|
| 無新郵件 | 回覆「沒有新信件」（§ 4.1） |
| API 連線失敗 | 告知用戶稍後再試（§ 4.2） |
| 授權過期 | 自動觸發重新授權流程（§ 4.3） |
| 單封處理失敗 | 跳過並標註，繼續處理其他（§ 4.4） |
| 分類信心度低 | 歸入「其他」，標註不確定（§ 4.5） |

## 參考資源

- `references/email_fields.json` — 每次流程開始時載入，包含分類規則、Gmail 設定等。
- `references/triage_prompts.md` — 組合輸出時載入，包含 system prompt、輸出模板、邊界處理模板。

## 腳本架構

```
scripts/
├── gmail_setup.py          # OAuth2 初始化（auth-url → exchange → verify）
├── gmail_auth.py           # 共用認證模組（OAuth2 + Service Account，scopes 參數化）
├── gmail_list_messages.py  # 列出未讀郵件
├── gmail_get_message.py    # 取得單封郵件詳情
└── gmail_modify_labels.py  # 為郵件加標籤
```

- `gmail_setup.py` 負責首次授權流程，分三步驟執行（非互動式，適合 agent 調用）。
- `gmail_auth.py` 提供 `load_credentials(credentials_path, token_path, scopes)` 函數，scopes 由呼叫端傳入。
