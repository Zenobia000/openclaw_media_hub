---
name: email-reply-draft
description: "根據 email-triage 分類結果草擬專業的電子郵件回覆，透過 Resend 發送（建議）或儲存為 Gmail 草稿（備用）。
  在發送任何電子郵件之前需經由使用者確認 — 絕不自動發送。
  使用時機：使用者想要回覆電子郵件，或提到如「幫我回這封信」、「回覆」、「幫我回」、「草擬回覆」、「reply to this email」、「draft a reply」、「reply」、「回覆第N封」、「幫我回所有詢價信」、「reply to all inquiries」等關鍵字，或是意圖明確為撰寫收到的電子郵件的回覆時。
  不適用於：閱讀/分類電子郵件（請使用 email-triage）、發送新電子郵件（非回覆）、轉寄電子郵件、管理電子郵件設定，或修改現有草稿。
  需求：草稿模式需要 Gmail API 憑證（gmail.readonly + gmail.compose）；Resend 模式需要設定 Resend MCP Server。"
metadata:
  openclaw:
    emoji: "✉️"
    requires:
      bins: ["python3"]
---

# Email Reply Draft Skill

## 概述

回覆草稿流程：取得原信 → 載入風格 → 選用模板 → AI 草擬 → 用戶預覽 → 確認 → 寄出（Resend）或存草稿（Gmail Draft）。

**核心原則：Confirm-first — AI 只草擬，人工確認後才送出。絕不自動寄信。**

## 設定

每次執行時載入 `references/reply_fields.json`，包含：

| 欄位 | 說明 |
|------|------|
| `business_name` | 商家名稱 |
| `sender_name` | 寄件人姓名 |
| `business_email` | 商家信箱 |
| `business_phone` | 聯絡電話 |
| `business_website` | 網站 |
| `tone` | 回信口吻（formal / semi-formal / friendly） |
| `send_method` | 發信方式（resend / gmail_draft） |
| `resend` | Resend 設定（api_key、from_email、from_name、reply_to） |
| `gmail_scopes` | Gmail API scopes |
| `credentials_file` / `token_file` | OAuth2 認證路徑 |
| `signature` | 簽名欄位 |

若 `business_name` 為空，先請用戶設定。

### 初始化（首次設定）

技能首次使用前需完成設定：**基本設定**（reply_fields.json）、**OAuth2 授權**（Gmail Draft 方案）、**Resend 設定**（Resend 方案）。

#### 初始化判斷邏輯（入口）

每次技能啟動時，依序檢查：

1. **`reply_fields.json` 是否已填寫** — 檢查 `business_name` 是否為空字串
   - 未填寫 → 進入「Step 0-A：互動式設定」
   - 已填寫 → 跳到 Step 0-B
2. **發信方式** — 根據 `send_method` 判斷：
   - `resend`：檢查 `resend.api_key` 是否已設定 → 未設定則進入 Resend 設定
   - `gmail_draft`：檢查 credentials + token 是否存在 → 不存在則進入 OAuth2 流程
3. 全部存在 → 直接進入回覆工作流程

#### Step 0-A：互動式設定

逐一詢問用戶以下欄位，**一次只問一個問題**：

1. **business_name**（必填）
   > 請問您的商家或工作室名稱是什麼？

2. **sender_name**（必填）
   > 回信署名用什麼名字？例如：「Sunny」

3. **business_email**（必填）
   > 簽名檔裡要顯示哪個聯絡信箱？（這是給對方看的聯絡方式，不是發信用的信箱）

4. **business_phone**（選填）
   > 聯絡電話？（可跳過）

5. **business_website**（選填）
   > 網站網址？（可跳過）

6. **tone**（選填，預設 `semi-formal`）
   > 回信口吻？可選：formal（正式）、semi-formal（半正式，預設）、friendly（親切）

7. **send_method**（選填，預設 `resend`）
   > 發信方式？可選：resend（直接寄出，推薦）、gmail_draft（存為 Gmail 草稿）

收集完成後寫入 `references/reply_fields.json`，同步更新 `signature` 欄位，顯示摘要讓用戶確認後儲存。

#### Resend 設定（send_method = resend 時）

如 `resend.api_key` 為空：
1. 請用戶前往 [Resend 官網](https://resend.com) 註冊帳號
2. 取得 API Key
3. 設定 MCP Server：在 Claude Code 的 MCP 設定中加入 `resend/mcp-send-email`
4. 將 API Key 貼上，由 agent 寫入 `reply_fields.json`
5. 設定 `from_email`、`from_name`、`reply_to`

#### 前置條件（Gmail Draft 方案）

安裝 Python 依賴：

```bash
python3 -m pip install --break-system-packages google-api-python-client google-auth-oauthlib
```

#### Step 0-B：確認 credentials 檔案（Gmail Draft 方案）

檢查 `{skill_dir}/{credentials_file}` 是否存在。若不存在，請用戶：
1. 前往 [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. 建立 OAuth 2.0 Client ID（Desktop App 類型）
3. 啟用 Gmail API
4. 下載 client secret JSON 檔案
5. 將 JSON 內容直接貼上，由 agent 寫入 `{skill_dir}/{credentials_file}`

#### Step 1：產生授權網址

```bash
python3 skill_hub/gmail/scripts/gmail_setup.py \
  --credentials "{skill_dir}/{credentials_file}" \
  --token "{skill_dir}/{token_file}" \
  --scopes "{gmail_scopes 以逗號分隔}" \
  --step auth-url
```

#### Step 2：用授權碼換取 Token

```bash
python3 skill_hub/gmail/scripts/gmail_setup.py \
  --credentials "{skill_dir}/{credentials_file}" \
  --token "{skill_dir}/{token_file}" \
  --scopes "{gmail_scopes 以逗號分隔}" \
  --step exchange \
  --code "{AUTHORIZATION_CODE}"
```

#### Step 3：驗證連線

```bash
python3 skill_hub/gmail/scripts/gmail_setup.py \
  --credentials "{skill_dir}/{credentials_file}" \
  --token "{skill_dir}/{token_file}" \
  --scopes "{gmail_scopes 以逗號分隔}" \
  --step verify
```

## 工作流程

### Step 1：取得原信

從 email-triage 的分類結果中找到用戶指定的郵件。若 context 中無 triage 結果，使用 gmail_get_message.py 直接取得：

```bash
python3 skill_hub/gmail/scripts/gmail_get_message.py \
  --credentials "{skill_dir}/{credentials_file}" \
  --token "{skill_dir}/{token_file}" \
  --scopes "{gmail_scopes 以逗號分隔}" \
  --message-id "{email_id}" \
  --truncate 500
```

### Step 2：載入風格

讀取 `references/reply_style.md`，取得回信口吻、模板、禁止事項。

### Step 3：載入分類模板

根據郵件分類（inquiry/support/booking/spam/other），選用 `reply_style.md` 中對應的回信模板。

### Step 4：AI 草擬回覆

由 Agent 自身能力根據：原信內容 + 風格設定 + 分類模板 + 用戶補充方向，草擬回覆。

草擬時遵循 `reply_style.md` 的 Quality Checklist 逐項檢查。

### Step 5：預覽

使用 `references/reply_prompts.md` § 2 的草稿預覽模板，將草稿展示給用戶，提供「OK / 修改 / 重寫」三個選項。

### Step 6：用戶確認

- **OK** → 進入 Step 7
- **修改** → 根據用戶指示修改後重新預覽（回到 Step 5）
- **重寫** → 回到 Step 4 重新草擬

### Step 7：寄出或存草稿

#### 方案 A：Resend 寄出

透過 Resend MCP Server（`resend/mcp-send-email`）寄出郵件。呼叫 MCP tool 時帶入：
- `from`：`{resend.from_name} <{resend.from_email}>`
- `to`：原信寄件人 email
- `subject`：`Re: {original_subject}`
- `text`：草稿內容
- `reply_to`：`{resend.reply_to}`

#### 方案 B：Gmail Draft

```bash
python3 skill_hub/gmail/scripts/gmail_drafts.py \
  --credentials "{skill_dir}/{credentials_file}" \
  --token "{skill_dir}/{token_file}" \
  --scopes "{gmail_scopes 以逗號分隔}" \
  --action create \
  --to "{from_email}" \
  --subject "Re: {original_subject}" \
  --body "{draft_body}" \
  --in-reply-to "{original_message_id_header}" \
  --thread-id "{thread_id}"
```

#### 降級策略

Resend 失敗 → 嘗試 Gmail Draft → 都失敗 → 以文字呈現草稿（§ 3.3 fallback）。

### Step 8：寄出確認

使用 `references/reply_prompts.md` § 3 的確認模板回覆用戶。

## 批量處理

用戶要求批量處理（如「回覆所有詢價信」）時：
1. 從 triage 結果篩選符合條件的郵件
2. **逐封**執行 Step 1-8
3. 每封都需用戶確認後才能寄出/存草稿
4. 提供跳過選項（「跳過這封」）

## 安全限制

1. **Confirm-first 鐵律** — 無論 Resend 或 Gmail Draft，必須用戶確認才能送出
2. **不自動送信** — 批量處理時，每封逐一確認
3. **不刪除原信** — 回覆後不刪除、不封存原信
4. **不修改原信** — 不標已讀、不加標籤（標籤由 triage 處理）
5. **不捏造資訊** — 無價目表不報價、不承諾時程
6. **簽名檔固定** — 使用 reply_fields.json 定義的簽名，不自行生成

## 錯誤處理

| 情況 | 處理 |
|------|------|
| 找不到郵件 | 建議重新執行 triage（§ 4.1） |
| 原信內容為空 | 詢問用戶是否仍要回覆（§ 4.2） |
| 「其他」分類且無方向 | 詢問用戶想回什麼（§ 4.3） |
| 垃圾信不回 | 告知建議不回覆（§ 4.4） |
| Resend 失敗 | 降級為 Gmail Draft → 文字 fallback（§ 4.5） |
| Gmail Draft 失敗 | 文字 fallback（§ 4.5） |
| 授權過期 | 自動觸發重新授權流程 |

## 參考資源

- `references/reply_fields.json` — 每次流程開始時載入，包含寄件人資訊、口吻、發信方式等。
- `references/reply_style.md` — 草擬回覆時載入，包含角色定義、口吻規則、分類模板、禁止事項。
- `references/reply_prompts.md` — 組合預覽與確認訊息時載入，包含草稿模板、確認模板、邊界處理。

## 工具依賴

本 Skill 使用 `skill_hub/gmail/` 提供的 Gmail API 工具，無自有腳本。

| 工具 | 用途 |
|------|------|
| `skill_hub/gmail/scripts/gmail_setup.py` | OAuth2 初始化 |
| `skill_hub/gmail/scripts/gmail_get_message.py` | 取得單封郵件詳情（補充上下文用） |
| `skill_hub/gmail/scripts/gmail_drafts.py` | 建立 Gmail 草稿（`--action create`） |

- Resend 發信透過 MCP Server（`resend/mcp-send-email`），無需自訂 script。
