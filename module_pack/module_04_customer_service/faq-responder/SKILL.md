---
name: faq-responder
description: "Telegram DM 客服的 fallback 處理器：比對 FAQ 知識庫自動回覆常見問題，
  偵測升級觸發條件轉人工，透過 Telegram 通知負責人，並將對話記錄寫入 CRM。
  Use when: 客戶透過 Telegram DM 提問，且未被其他 Skill 匹配時進入。
  關鍵字：客服, FAQ, 常見問題, 自動回覆, 升級, 轉人工, customer service, support。
  NOT for: 主動行銷推播、多群組廣播、語音/圖片處理、既有客戶關係管理。
  Requires: TELEGRAM_BOT_TOKEN 與 NOTIFY_CHAT_ID 環境變數。"
metadata:
  openclaw:
    emoji: "💬"
    requires:
      bins: ["python3"]
      env: ["TELEGRAM_BOT_TOKEN", "NOTIFY_CHAT_ID"]
---

# FAQ Responder Skill

## 概述

客服自動回覆流程：檢查工作時間 → 載入 FAQ 知識庫 → 語意匹配 → 檢查升級觸發 → 自動回覆或升級轉人工 → 通知負責人 → 寫入 CRM。

## 設定

每次收到客戶訊息時載入 `references/faq_responder_config.json`，包含：

| 欄位 | 說明 |
|------|------|
| `business_name` | 商家名稱，用於 system prompt |
| `timezone` | 時區（預設 Asia/Taipei） |
| `working_hours` | 上下班時間（start / end） |
| `working_days` | 工作日陣列 |
| `confirmation_language` | 回覆語言（預設 zh-TW） |
| `crm_skill_dir` | lead-capture skill 的相對路徑 |
| `default_handler` | 預設升級負責人 |
| `escalation_handlers` | 各情境升級負責人（default / complaint / technical） |
| `faq_files` | FAQ 知識庫檔案列表 |
| `reply_settings` | 回覆長度上限、語氣風格 |

若 `business_name` 為空，先進入初始化。

### 初始化（首次設定）

技能首次使用前需完成：**業務設定**（faq_responder_config.json）、**環境變數確認**、**通知測試**、**CRM 驗證**。

#### 初始化判斷邏輯（入口）

每次技能啟動時，依序檢查：

1. **`faq_responder_config.json` 是否已填寫** — 檢查 `business_name` 是否為空
   - 未填寫 → 進入 Step 0-A
   - 已填寫 → 跳到 Step 0-B
2. **環境變數是否存在** — `TELEGRAM_BOT_TOKEN`、`NOTIFY_CHAT_ID`
   - 缺少 → 進入 Step 0-B
3. **CRM skill 是否可用** — 檢查 `{crm_skill_dir}/references/crm_fields.json` 存在且 `business_name` 非空
   - 未設定 → 進入 Step 0-D
4. 全部通過 → 直接進入工作流程

#### Step 0-A：互動式業務設定

逐一詢問用戶以下欄位，**一次只問一個問題**：

1. **business_name**（必填）
   > 請問您的商家或工作室名稱是什麼？
   > 例如：「桑尼工作室」

2. **default_handler**（必填）
   > 客服升級時，預設通知誰？
   > 例如：「@sunny」、「王小明」

3. **escalation_handlers.complaint**（選填）
   > 客訴問題要通知誰？（留空則使用預設負責人）

4. **escalation_handlers.technical**（選填）
   > 技術問題要通知誰？（留空則使用預設負責人）

5. **timezone**（選填，預設 `Asia/Taipei`）
   > 您的時區是？預設：Asia/Taipei

6. **working_hours**（選填，預設 09:00-18:00）
   > 您的服務時段是幾點到幾點？
   > 預設：09:00 - 18:00

7. **working_days**（選填，預設週一至週五）
   > 您的服務日是哪幾天？
   > 預設：Mon, Tue, Wed, Thu, Fri

8. **confirmation_language**（選填，預設 `zh-TW`）
   > 回覆語言？可選：zh-TW / zh-CN / en / ja。預設：zh-TW

收集完成後寫入 `references/faq_responder_config.json`，顯示摘要讓用戶確認。
`escalation_handlers.default` 自動設為 `default_handler` 的值。

#### Step 0-B：確認環境變數

檢查以下環境變數是否存在：

1. **`TELEGRAM_BOT_TOKEN`** — Telegram Bot Token（從 BotFather 取得）
2. **`NOTIFY_CHAT_ID`** — 負責人的 Telegram Chat ID（從 @userinfobot 取得）

若缺少，引導用戶設定 `.env` 檔案：
```
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
NOTIFY_CHAT_ID=987654321
```

#### Step 0-C：測試通知

```bash
python3 {skill_dir}/scripts/tg_notify.py \
  --bot-token "$TELEGRAM_BOT_TOKEN" \
  --chat-id "$NOTIFY_CHAT_ID" \
  --message "✅ FAQ Responder 通知測試成功"
```

確認負責人收到測試訊息。若失敗，檢查 Token 與 Chat ID。

#### Step 0-D：驗證 CRM

檢查 `{crm_skill_dir}/references/crm_fields.json` 是否存在且 `business_name` 非空。
若 CRM 尚未初始化，提示用戶先完成 lead-capture skill 的設定。

初始化完成後進入工作流程。

## 工作流程

### Step 1：檢查工作時間

```bash
python3 {skill_dir}/scripts/check_hours.py \
  --timezone "{timezone}" \
  --start "{working_hours.start}" \
  --end "{working_hours.end}" \
  --days "{working_days_joined}"
```

輸出 JSON 含 `is_working_hours`、`current_time`、`current_day`、`next_working_time`。
此結果影響後續回覆模板選擇（工作時間 vs 非工作時間）。

### Step 2：載入 FAQ 知識庫並語意匹配

從 `references/` 載入 `faq_files` 中列出的所有 `faq_*.md` 檔案。

匹配邏輯（AI 原生處理）：
1. 讀取所有 FAQ 文件的 Q&A 對
2. 根據客戶訊息進行語意匹配（非純關鍵字匹配）
3. 匹配結果分為：明確匹配、部分匹配、無匹配

### Step 3：檢查升級觸發

載入 `references/escalation_rules.json`，依序檢查：

1. **關鍵字掃描** — 客戶訊息是否包含 `escalation_levels.high.keywords` 或 `medium.keywords`
2. **語意判斷** — 根據 `context_rules`，理解上下文語意（如「定價策略」也應升級）
3. **情緒偵測** — 客戶是否表達不滿或情緒性語言

判斷結果：
- 需升級（高/中優先級）→ 跳到 Step 5
- 不需升級 → 進入 Step 4

### Step 4：自動回覆（FAQ 匹配，無升級）

載入 `references/response_templates.md`，使用 § 2.1 或 § 2.2 模板。

回覆規則：
- 答案 100% 來自知識庫，零編造
- 回覆長度控制在 `reply_settings.max_length` 字以內
- 結尾附上「還有其他問題嗎？」
- 語氣遵守 system prompt 規範

若無匹配，使用 § 5.1 模板轉人工。

### Step 5：升級處理

升級時執行三個動作：

**5-A. 回覆客戶：**

依情境選擇模板（`references/response_templates.md`）：
- 一般升級 → § 3.1
- 客訴 → § 3.2
- 非工作時間 → § 3.3

**5-B. 通知負責人：**

組合通知內容（§ 4.1 模板），選擇對應負責人（`escalation_handlers`），發送：

```bash
python3 {skill_dir}/scripts/tg_notify.py \
  --bot-token "$TELEGRAM_BOT_TOKEN" \
  --chat-id "{handler_chat_id}" \
  --message "{notification_content}"
```

負責人選擇邏輯：
- 客訴 → `escalation_handlers.complaint`（若空則 `default`）
- 技術問題 → `escalation_handlers.technical`（若空則 `default`）
- 其他 → `escalation_handlers.default`

**5-C. 寫入 CRM：**

見 Step 7。

### Step 6：處理等待狀態

若客戶已進入升級等待，在人工接手前繼續發訊息：
- 使用 § 3.4 模板回覆
- 不嘗試回答升級範圍的問題
- 將補充訊息一併轉達（追加通知或更新 CRM）

### Step 7：寫入 CRM

透過 lead-capture skill 的腳本記錄對話，路徑由 `crm_skill_dir` 指定。

讀取 CRM 設定：`{crm_skill_dir}/references/crm_fields.json` 取得 `sheets.spreadsheet_id`、`sheets.sheet_name`、`sheets.credentials_file`、`sheets.token_file`。

**新客戶（首次互動）：**

```bash
python3 {crm_skill_dir}/scripts/gsheets_append.py \
  --credentials "{crm_skill_dir}/{sheets.credentials_file}" \
  --token "{crm_skill_dir}/{sheets.token_file}" \
  --spreadsheet-id "{sheets.spreadsheet_id}" \
  --sheet-name "{sheets.sheet_name}" \
  --data '{"date":"{date}","client_name":"{name}","contact":"{contact}","source":"Telegram","needs_summary":"{summary}","status":"{status}","priority":"","owner":"{default_handler}","followup_date":"","notes":"","ai_log":"{ai_log}"}'
```

- FAQ 自動回覆：`status` = `"新詢問"`
- 升級轉人工：`status` = `"需人工處理"`

**既有客戶（追加記錄）：**

先查詢是否已存在：
```bash
python3 {crm_skill_dir}/scripts/gsheets_query.py \
  --credentials "{crm_skill_dir}/{sheets.credentials_file}" \
  --token "{crm_skill_dir}/{sheets.token_file}" \
  --spreadsheet-id "{sheets.spreadsheet_id}" \
  --sheet-name "{sheets.sheet_name}" \
  --filter-field "contact" --filter-value "{contact}"
```

若已存在，更新 AI 互動記錄：
```bash
python3 {crm_skill_dir}/scripts/gsheets_update.py \
  --credentials "{crm_skill_dir}/{sheets.credentials_file}" \
  --token "{crm_skill_dir}/{sheets.token_file}" \
  --spreadsheet-id "{sheets.spreadsheet_id}" \
  --sheet-name "{sheets.sheet_name}" \
  --row "{existing_row}" \
  --field "ai_log" --value "{ai_log_entry}" --append-mode
```

## 安全限制

| 規則 | 說明 |
|------|------|
| 只回答知識庫內容 | 不根據「一般常識」回答業務相關問題 |
| 不編造答案 | 知識庫無匹配 → 轉人工 |
| 不報價格 | 除非知識庫有明確公開價目表 |
| 不承諾交期 | 任何時程承諾需人工確認 |
| 不處理客訴 | 客戶表達不滿或投訴 → 立即轉人工 |
| 不處理退款 | 退款相關請求 → 立即轉人工 |
| 不提供法律建議 | 合約、法律、責任相關 → 轉人工 |
| 所有對話回寫 CRM | 確保每次互動都有記錄 |
| 升級寧嚴勿鬆 | 不確定時優先轉人工 |

## 錯誤處理

| 情況 | 處理 |
|------|------|
| FAQ 無匹配 | 使用 § 5.1 模板轉人工 |
| Telegram 通知失敗 | 使用 § 5.2 模板，記錄錯誤，下次重試 |
| CRM 寫入失敗 | 使用 § 5.3 模板，記錄待補寫 |
| CRM 未初始化 | 引導用戶先完成 lead-capture 設定 |
| 環境變數缺失 | 引導用戶設定 .env |
| 429 Rate Limit | 等待 `retry_after` 秒後重試 |

## 參考資源

| 檔案 | 載入時機 |
|------|---------|
| `references/faq_responder_config.json` | 每次收到訊息時載入 |
| `references/escalation_rules.json` | Step 3 檢查升級觸發時載入 |
| `references/response_templates.md` | Step 4/5 組合回覆時載入 |
| `references/faq_general.md` | Step 2 語意匹配時載入 |
| `references/faq_service.md` | Step 2 語意匹配時載入 |
| `references/faq_process.md` | Step 2 語意匹配時載入 |

## 腳本架構

```
scripts/
├── check_hours.py    # 檢查工作時間（timezone-aware，stdlib only）
└── tg_notify.py      # Telegram Bot API 通知（stdlib only，無外部依賴）
```

- `check_hours.py` 使用 `zoneinfo` + `datetime` 計算當前是否為工作時間，輸出 JSON。
- `tg_notify.py` 使用 `urllib.request` POST 到 Telegram Bot API，支援 rate limit 處理。
- CRM 操作複用 `lead-capture/scripts/` 的 `gsheets_append.py`、`gsheets_query.py`、`gsheets_update.py`，不重複實作。
