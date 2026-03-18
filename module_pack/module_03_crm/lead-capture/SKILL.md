---
name: lead-capture
description: "從對話、表單、Email 中擷取客戶資訊，計算 Lead Score，寫入 CRM（Notion 或 Google Sheets），自動指派 follow-up 任務。
  Use when: 使用者提及潛在客戶詢問、收到 lead、關鍵字如 客戶, 詢問, 潛在客戶, lead, 有人問, 新客, 有人來信, 客戶資料, CRM, 建立客戶, 記錄客戶。
  NOT for: 查詢現有 CRM 資料（無新 lead 脈絡）、修改已進行的交易階段、產生報表、管理既有客戶關係。
  Requires: Notion MCP 連線或 Google Sheets API 認證。"
metadata:
  openclaw:
    emoji: "📋"
    requires:
      bins: ["python3"]
---

# Lead Capture Skill

## 概述

完整客戶擷取流程：偵測 lead 意圖 → AI 提取客戶資訊 → 計算 Lead Score → 寫入 CRM（Notion 或 Google Sheets）→ 指派 follow-up → 通知負責人 → 回覆確認。

## 設定

每次流程開始時載入 `references/crm_fields.json`，包含：

| 欄位 | 說明 |
|------|------|
| `business_name` | 商家名稱，用於 system prompt |
| `timezone` | 時區（預設 Asia/Taipei） |
| `backend_type` | CRM 後端：`notion` 或 `sheets` |
| `notification_target` | 通知管道（預設 telegram） |
| `default_owner` | 預設負責人 |
| `confirmation_language` | 回覆語言（預設 zh-TW） |
| `notion.*` | Notion 後端設定（database_name、mcp_permissions） |
| `sheets.*` | Sheets 後端設定（spreadsheet_id、sheet_name、credentials/token） |
| `fields.*` | 狀態、來源、優先級選項 |
| `followup_rules` | 各優先級的 follow-up 天數與行動 |
| `escalation_rules` | 升級規則（價格詢問、投訴、冷名單等） |

若 `business_name` 為空，先進入初始化。

### 初始化（首次設定）

技能首次使用前需完成設定：**業務設定**（crm_fields.json）與 **CRM 後端連接**。

#### 初始化判斷邏輯（入口）

每次技能啟動時，依序檢查：

1. **`crm_fields.json` 是否已填寫** — 檢查 `business_name` 是否為空
   - 未填寫 → 進入 Step 0-A
   - 已填寫 → 跳到下一項
2. **`backend_type` 是否已選擇** — 空值則進入 Step 0-A
3. 依 `backend_type` 檢查後端連接：
   - `notion` → 確認 Notion MCP 已連接 → 進入 Path A
   - `sheets` → 確認 credentials 與 token 存在 → 進入 Path B
4. 全部通過 → 直接進入工作流程

#### Step 0-A：互動式業務設定

逐一詢問用戶以下欄位，**一次只問一個問題**：

1. **business_name**（必填）
   > 請問您的商家或工作室名稱是什麼？
   > 例如：「桑尼工作室」

2. **backend_type**（必填）
   > 您要使用哪個系統管理客戶？
   > 1. Notion（推薦，視覺化看板）
   > 2. Google Sheets（零成本，公式彈性大）
   > ⚠ 請只選一個，不要兩個一起用。

3. **default_owner**（選填）
   > 預設的客戶負責人是誰？
   > 例如：「@sunny」、「王小明」
   > 預設：留空

4. **timezone**（選填，預設 `Asia/Taipei`）
   > 您的時區是？預設：Asia/Taipei

5. **confirmation_language**（選填，預設 `zh-TW`）
   > 確認訊息要用什麼語言？
   > 可選：zh-TW / zh-CN / en / ja。預設：zh-TW

若選擇 **Notion**，額外詢問：
- **notion.database_name**（選填，預設「客戶管理 CRM」）

若選擇 **Sheets**，額外詢問：
- **sheets.spreadsheet_id**（必填）
  > 請提供 Google Sheets 試算表的 ID（網址中 `/d/` 和 `/edit` 之間的部分）

收集完成後寫入 `references/crm_fields.json`，顯示摘要讓用戶確認。

#### Path A：Notion MCP 設定

1. 確認 Notion MCP 已連接到 workspace
2. 使用 Notion MCP 建立「客戶管理 CRM」資料庫（依 `notion_crm_database_template.md` 的 11 個欄位）
3. 驗證：透過 MCP 讀取資料庫確認可存取
4. 完成

#### Path B：Google Sheets OAuth 設定

前置條件：
```bash
python3 -m pip install --break-system-packages google-api-python-client google-auth-oauthlib
```

##### Step 0-B：確認 credentials 檔案

檢查 `{skill_dir}/{sheets.credentials_file}` 是否存在。若不存在，請用戶：
1. 前往 [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. 建立 OAuth 2.0 Client ID（Desktop App 類型）
3. 啟用 Google Sheets API
4. 下載 client secret JSON 檔案
5. 將 JSON 內容直接貼上，由 agent 寫入 `{skill_dir}/{sheets.credentials_file}`

##### Step 1：產生授權網址

```bash
python3 {skill_dir}/scripts/gsheets_setup.py \
  --credentials "{skill_dir}/{sheets.credentials_file}" \
  --token "{skill_dir}/{sheets.token_file}" \
  --step auth-url
```

輸出 JSON 含 `auth_url`。提供給用戶開啟並完成授權，複製授權碼。

##### Step 2：用授權碼換取 Token

```bash
python3 {skill_dir}/scripts/gsheets_setup.py \
  --credentials "{skill_dir}/{sheets.credentials_file}" \
  --token "{skill_dir}/{sheets.token_file}" \
  --step exchange \
  --code "{AUTHORIZATION_CODE}"
```

##### Step 3：驗證連線

```bash
python3 {skill_dir}/scripts/gsheets_setup.py \
  --credentials "{skill_dir}/{sheets.credentials_file}" \
  --token "{skill_dir}/{sheets.token_file}" \
  --step verify \
  --spreadsheet-id "{sheets.spreadsheet_id}"
```

確認可讀取目標試算表。初始化完成。

## 工作流程

### Step 1：偵測 lead 意圖

觸發關鍵字：客戶、詢問、潛在客戶、lead、有人問、新客、有人來信、客戶資料、CRM、建立客戶、記錄客戶。

當使用者轉述客戶訊息、轉發詢問郵件、或明確表達「有新的客戶詢問」時觸發。僅查詢 CRM 或管理既有客戶時不觸發。

### Step 2：擷取 lead 資訊

從訊息內容中 AI 提取以下 5 欄位：

| 欄位 | 必填 | 缺少時 |
|------|:----:|--------|
| `client_name` | 是 | 標記「未提供」 |
| `contact` | 是 | 標記「未提供」 |
| `source` | 是 | 依脈絡判斷或標記「其他」 |
| `needs_summary` | 是 | AI 生成 2-3 句摘要（≤100 字） |
| `date` | 自動 | 使用當前日期 |

### Step 3：計算 Lead Score

載入 `references/lead_score_config.json`，根據對話內容判斷四維度等級，呼叫：

```bash
python3 {skill_dir}/scripts/lead_scorer.py \
  --lead-json '{"source":"{level}","needs_clarity":"{level}","interaction_frequency":"{level}","client_scale":"{level}"}' \
  --config "{skill_dir}/references/lead_score_config.json"
```

取得 `total_score`、`priority`、`priority_label`、`followup_days`、`score_log`。

### Step 4：建立 CRM 紀錄

依 `backend_type` 分路：

**Path A — Notion MCP：**

使用 Notion MCP 的 create page 功能，對應 `notion_crm_database_template.md` 的 11 個欄位。

**Path B — Google Sheets：**

```bash
python3 {skill_dir}/scripts/gsheets_append.py \
  --credentials "{skill_dir}/{sheets.credentials_file}" \
  --token "{skill_dir}/{sheets.token_file}" \
  --spreadsheet-id "{sheets.spreadsheet_id}" \
  --sheet-name "{sheets.sheet_name}" \
  --data '{"date":"{date}","client_name":"{name}","contact":"{contact}","source":"{source}","needs_summary":"{summary}","status":"新詢問","priority":"{priority}","owner":"{owner}","followup_date":"{followup_date}","notes":"","ai_log":"{score_log}"}'
```

### Step 5：指派 Follow-up

根據 `followup_days` 計算 follow-up 日期（今天 + N 天）。對照 `crm_fields.json` 的 `followup_rules`：

| 優先級 | 天數 | 行動 |
|--------|------|------|
| 高 | 1 | 立即通知負責人 |
| 中 | 3 | AI 先跟進 |
| 低 | 7 | AI 輕觸跟進 |

### Step 6：通知負責人

高優先級客戶：立即向 `default_owner` 發送通知（透過 `notification_target` 管道），使用 `capture_prompts.md` § 2.2 格式。

中/低優先級：不即時通知，依 follow-up 排程處理。

### Step 7：回覆確認

載入 `references/capture_prompts.md`，使用 § 2.1 格式回覆用戶，確認紀錄已建立。

## 安全限制

| 規則 | 說明 |
|------|------|
| 只做 Append | 只新增紀錄，絕不刪除既有資料 |
| 不修改核心欄位 | 建立後的 client_name、contact、date、source 不可被 AI 覆寫 |
| 狀態只能前進 | AI 只能將狀態從「新詢問」推進，不可回退 |
| 敏感資訊過濾 | 信用卡號、身分證字號等不寫入 CRM，僅標記「客戶有提供敏感資訊，請人工確認」 |
| 單一資料源 | Notion 或 Sheets 擇一，不做雙向同步 |

## 錯誤處理

| 情況 | 處理 |
|------|------|
| CRM 後端未設定 | 引導進入初始化流程（§ 4.4） |
| API / MCP 連線失敗 | 告知用戶稍後再試（§ 4.2） |
| 授權過期（Sheets） | 自動觸發 gsheets_setup.py 重新授權 |
| 缺少客戶欄位 | 標記「未提供」，紀錄仍建立（§ 4.1） |
| 偵測到敏感資訊 | 過濾後標記，通知人工處理（§ 4.3） |
| 重複客戶 | 顯示既有紀錄，由用戶決定處理方式（§ 2.5） |

## 參考資源

- `references/crm_fields.json` — 每次流程開始時載入，包含所有業務設定、後端連接、欄位選項。
- `references/lead_score_config.json` — Step 3 計算評分時載入，包含四維度權重、分數、等級定義、AI 判斷提示。
- `references/capture_prompts.md` — Step 7 組合回覆時載入，包含 system prompt、回覆模板、邊界處理模板。

## 腳本架構

```
scripts/
├── gsheets_auth.py     # 共用認證模組（OAuth2 + Service Account，scopes 參數化）
├── gsheets_setup.py    # OAuth2 初始化（auth-url → exchange → verify）
├── gsheets_append.py   # 新增 lead 至 CRM Sheet
├── gsheets_query.py    # 查詢 leads（按欄位過濾、逾期追蹤）
├── gsheets_update.py   # 更新紀錄欄位（僅限可更新欄位，支援 append-mode）
└── lead_scorer.py      # Lead 評分計算器（純運算，無 API 依賴）
```

- `gsheets_setup.py` 負責首次授權流程，分三步驟執行（非互動式，適合 agent 調用）。
- `gsheets_auth.py` 提供 `load_credentials()` 函數，自動偵測認證類型，供 append/query/update 共用。
- `lead_scorer.py` 為純運算腳本，接受四維度等級 JSON 與設定檔，輸出評分結果。
