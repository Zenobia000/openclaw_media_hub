# AI 助理安裝包 — 模組包總規格書

> 版本：v1.0
> 最後更新：2026-03-10
> 適用課程：一日工作坊 — 用 Claude Code + OpenClaw 打造你的 AI 工作助理

---

## 1. 核心判斷

我們賣的是**「AI 助理安裝包」**，不是教開發。

學員不需要理解 API 串接、Prompt Engineering 原理、或任何程式碼。他們需要的是：

- 今天走進教室，帶著一個**能用的 AI 助理**離開
- 這個助理能處理他們每天最痛的 3-5 件重複性工作
- 他們只需要「填表單」，不需要「寫程式」

如果學員需要打開終端機輸入指令才能完成設定，那是我們的設計失敗，不是學員的能力問題。

---

## 2. 系統角色分層

| 層級 | 工具 | 角色定位 | 學員需要知道的 |
|------|------|----------|----------------|
| **Vibe Coding 層** | Claude Code | 改模板、生設定檔、除錯（可用 OpenRouter 免費模型或 Ollama 本地模型） | 不需要知道，講師操作 |
| **聊天入口層** | OpenClaw | 學員日常對話的唯一入口，任務編排中心 | 「跟它說話就好」 |
| **資料記錄層** | Notion / Google Sheets | CRM、客戶紀錄、報價紀錄 | 「你的客戶資料都在這裡」 |
| **預約層** | Google Calendar | 行事曆管理、時段查詢 | 「跟助理說要約，它會幫你排」 |
| **發信層** | Resend | Email 發信工具（設定極簡、有 MCP Server） | 「助理寫好信，確認後幫你寄」 |
| **讀信層** | Gmail | Email 讀信、分類、摘要（Gmail API 或 n8n Gmail node） | 「它會幫你整理收件匣」 |

### 架構原則

```
學員 ←→ OpenClaw（唯一入口）
              │
              ├── Google Calendar（預約）
              ├── Gmail（Email 收發）
              ├── Notion / Google Sheets（CRM）
              ├── 日報週報產生器
              └── 通知推送（Telegram / LINE）
```

---

## 3. 六大模組總覽

| # | 模組名稱 | 目的 | 最小可行流程 | 課堂版做法 | 發給學員的模板檔案 |
|---|----------|------|-------------|-----------|-------------------|
| 1 | **預約模組** | 客戶說「我要約時間」→ AI 查空檔 → 建立事件 → 回覆確認 | 對話 → 查日曆 → 建事件 → 確認訊息 | 填 `calendar_fields.json` → 講師用 Claude Code 部署 Skill | `calendar_booking_skill.md`, `calendar_confirmation_prompt.md`, `calendar_fields.json` |
| 2 | **Email 收發模組** | 收件匣 AI 分類 + 摘要 → 草擬回覆 → 人工確認送出 | 讀信 → 分類 → 草擬 → 發送 | 讀信用 Gmail API（或 n8n Gmail node）+ 發信用 Resend MCP Server → 雙 provider 各司其職 → 測試一封信 | `email_triage_skill.md`, `email_reply_draft_skill.md`, `reply_style_claude.md`, `gmail_scope_minimal.json`, `resend_config.json` |
| 3 | **CRM 模組** | 每次互動自動寫入客戶紀錄，可查詢歷史 | 對話觸發 → 寫入 Sheet/Notion → 回覆確認 | 建立 CRM 模板 → 設定欄位對應 → 測試寫入 | `crm_schema.json`, `crm_append_skill.md`, `crm_query_skill.md` |
| 4 | **客服模組** | 常見問題自動回覆 + 複雜問題轉人工 | 收到問題 → 比對知識庫 → 回覆或轉派 | 填 FAQ 表 → 設定轉派規則 → 測試 | `faq_knowledge_base.md`, `customer_service_skill.md`, `escalation_rules.json` |
| 5 | **日報週報模組** | 彙整當日/當週活動，產生結構化報告 | 拉資料 → 彙整 → 格式化 → 推送 | 選報告頻率 → 選資料來源 → 測試產出 | `report_template.md`, `report_schedule.json`, `report_skill.md` |
| 6 | **通知模組** | 關鍵事件即時推送到 Telegram / LINE | 事件觸發 → 格式化訊息 → 推送 | 設定 Telegram Bot Token → 測試推送 | `notification_skill.md`, `notification_channels.json`, `notification_templates.md` |

---

## 4. 課程三階段定義

### 第一階段：安裝版（今天跑起來）

- **目標**：學員帶走一個能用的 AI 助理
- **範圍**：6 個模組各跑通最小可行流程
- **學員動作**：填 JSON 設定欄位、測試對話、確認結果
- **講師動作**：用 Claude Code 部署模板、排除技術問題
- **交付物**：可運行的 OpenClaw 助理 + 所有設定檔

### 第二階段：客製版（變成他的工作）

- **目標**：AI 助理完全適配學員的商業場景
- **範圍**：調整 Prompt、增加分類規則、客製回覆模板、串接更多資料源
- **學員動作**：提供商業資訊（FAQ、價目表、服務流程）
- **講師動作**：遠端調整設定、迭代 Prompt
- **交付物**：客製化的完整 AI 助理
- **計費**：一次性客製費

### 第三階段：代維運版（Recurring Revenue）

- **目標**：持續維護、監控、優化 AI 助理
- **範圍**：每月健檢報告、Prompt 優化、新功能上架、故障排除
- **學員動作**：回報問題、提出新需求
- **講師動作**：定期維護、主動優化
- **交付物**：月度維運報告
- **計費**：月費制

```
安裝版（一日工作坊）→ 客製版（1-2 週交付）→ 代維運版（月費）
     ↑ 入口                ↑ 追售                 ↑ 持續收入
```

---

## 5. 五大 Best Practices

### BP-1：用模板包取代從零教學

不要教學員寫 Prompt，給他們填好的模板。

- Claude Code 的 `skills/`、`CLAUDE.md`、custom commands、hooks 全部模板化
- 學員只需要改 JSON 裡的商業欄位（店名、營業時間、服務項目）
- Claude Code 讀取 JSON，自動改寫所有模板

```
學員填 calendar_fields.json
  → Claude Code 讀取
  → 自動更新 Skill 設定、Prompt 模板、確認訊息格式
  → 部署到 OpenClaw
```

### BP-2：一個入口、一個主資料面、一個通知面

- **一個入口**：OpenClaw 是學員唯一需要打開的介面
- **一個主資料面**：所有紀錄寫入同一個 Notion / Google Sheets
- **一個通知面**：所有提醒推到同一個 Telegram / LINE

絕對不要讓學員在 5 個平台之間切換。

### BP-3：Skill 只用白名單

OpenClaw 的 Skill 生態（ClawHub）有惡意 Skill 風險：

- 只安裝本課程提供的 Skill
- 不從 ClawHub 安裝未經審核的第三方 Skill
- 每個 Skill 的 API scope 必須明確列出且最小化
- 課程提供的每個 Skill 都附帶安全審查文件

### BP-4：權限最小化

| 服務 | 第一版權限 | 明確不開的權限 | 理由 |
|------|-----------|---------------|------|
| Gmail | readonly + labels + compose | send, modify, settings | Draft-first，人工確認再寄 |
| Calendar | events.insert | events.delete, events.update (bulk) | 只建立，不刪不批量改 |
| Sheets/Notion | append | delete, bulk update | 只新增紀錄，不刪不批量改 |
| Telegram | sendMessage | 管理群組、踢人 | 只推送，不管理 |

### BP-5：把「設定」變成表單而非教學負擔

學員的認知負擔必須是零。

- 每個模組提供一個 JSON 設定檔
- JSON 裡只有商業欄位（店名、時間、分類規則），沒有技術欄位
- 講師用 Claude Code 讀取 JSON 後自動完成所有技術設定
- 如果某個欄位需要解釋超過一句話，那這個欄位的設計有問題

### BP-6：Provider 選擇原則

每個功能選最簡單、門檻最低的 provider，不要為了統一而犧牲簡潔：

| 功能 | 推薦 Provider | 理由 |
|------|--------------|------|
| 發信 | Resend | 設定極簡（一個 API Key）、有現成 MCP Server、免費額度夠用 |
| 讀信 | Gmail API / n8n Gmail node | Google 帳號人人有、OAuth 流程成熟 |
| AI（Vibe Coding） | OpenRouter 免費模型（qwen3-coder:free、deepseek-r1:free）或 Ollama 本地模型 | 學員不需要 Claude Pro/Max 訂閱，零成本即可使用 Claude Code |
| AI（付費進階） | Anthropic API | 需要更高品質輸出時，講師或進階學員使用 |

原則：**一個功能一個 provider，不混搭、不多繞**。如果某個 provider 需要超過 3 步設定，換一個更簡單的。

---

## 6. 口訣

> **先模板後客製** — 今天先跑起來，之後再調
>
> **先 Draft 後 Auto-send** — AI 草擬，人工確認，絕不自動寄信
>
> **先單入口後多通道** — 先把一個入口做好，再串更多平台

---

## 7. 學員帶走清單

課程結束時，每位學員必須帶走以下項目：

| # | 項目 | 形式 | 驗收標準 |
|---|------|------|---------|
| 1 | AI 助理入口 | OpenClaw 帳號 + 已部署的助理 | 能對話、能執行任務 |
| 2 | CRM 模板 | Google Sheets / Notion 模板 | 有欄位定義、有範例資料 |
| 3 | 預約模板 | Google Calendar + Skill 設定 | 能建立事件、能回覆確認 |
| 4 | Email 草稿模板 | Gmail Draft Skill + 回信風格設定 | 能分類信件、能草擬回覆 |
| 5 | 日報週報模板 | 報告 Skill + 排程設定 | 能產出結構化報告 |
| 6 | 自己的設定檔 | 所有 `*_fields.json` 設定檔 | 已填入自己的商業資訊 |
| 7 | 故障排除 SOP | `troubleshooting/` 資料夾 | 常見問題 + 解法 + 聯絡方式 |

---

## 8. 檔案結構

```
module_pack/
├── module_pack_spec.md              ← 你正在看的這份文件
├── config/                          ← 全域設定
├── module_01_booking/               ← 預約模組
│   ├── calendar_booking_skill.md
│   ├── calendar_confirmation_prompt.md
│   └── calendar_fields.json
├── module_02_email/                 ← Email 收發模組
│   ├── email_triage_skill.md
│   ├── email_reply_draft_skill.md
│   ├── reply_style_claude.md
│   └── gmail_scope_minimal.json
├── module_03_crm/                   ← CRM 模組
├── module_04_customer_service/      ← 客服模組
├── module_05_report/                ← 日報週報模組
├── module_06_notification/          ← 通知模組
└── troubleshooting/                 ← 故障排除 SOP
```
