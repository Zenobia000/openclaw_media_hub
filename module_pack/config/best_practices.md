# 五大最佳實務完整指南

> 本文件是「AI 自動化一日工作坊」的核心教學原則。
> 所有模組的設計、教學順序、工具選擇都遵循以下五大原則。

---

## 1. 用模板包取代從零教學

### 原則

Claude Code 支援 skills、CLAUDE.md、custom commands 與 hooks，這些機制讓我們可以把完整的自動化流程封裝成一個 `/install-xxx` 命令。學員不需要從零開始寫程式碼或設定——他們只需要「改」。

### 學員操作流程

```
下載模板包 → 執行 /install-xxx 安裝模組 → 填寫商業設定表 → Claude Code 自動改參數 → 測試驗證
```

### 為什麼這樣做

Vibe Coding 的核心價值是**「改」而不是「寫」**。

- 從零教學需要解釋太多技術概念，一天根本教不完
- 模板包已經把架構、權限、prompt 都設計好了
- 學員只需要把商業邏輯填進去，技術層全部由模板處理
- 這跟「用 WordPress 主題」是同一個思路——你不需要會寫 PHP，你需要會改設定

### 實際做法

| 傳統教學 | 模板包教學 |
|----------|-----------|
| 教 OAuth 原理 | `/install-booking` 自動設定好授權 |
| 教 API 串接 | Skill 已封裝好所有 API 呼叫 |
| 教 prompt engineering | 模板 prompt 已寫好，學員只改商業欄位 |
| 3 天才能完成一個流程 | 1 小時完成安裝 + 設定 + 測試 |

---

## 2. 一個入口、一個主資料面、一個通知面

### 原則

工具不是越多越好。對非技術背景的學員來說，**每多一個工具就多一個放棄的理由**。

### 三面原則

| 面向 | 選擇 | 說明 |
|------|------|------|
| **入口面** | Telegram 或單一聊天介面 | 所有操作從一個地方開始，不要三種入口同時教 |
| **主資料面** | Notion 或 Google Sheets 擇一 | 所有資料匯集到一個地方，不要兩個一起用 |
| **通知面** | Email 或 Telegram 擇一 | 通知只走一個管道，避免分散注意力 |

### 失敗案例

> 「我同時用了 Notion 記客戶資料、Google Sheets 做報表、Telegram 收通知、Email 也收通知、LINE 也設了 Bot... 最後全部都沒在維護。」

這是最常見的自動化失敗模式：**工具太多，維護成本超過自動化帶來的效益**。

### 建議組合

**組合 A（推薦給個人工作者）**
- 入口：Telegram Bot
- 資料：Google Sheets
- 通知：Telegram

**組合 B（推薦給小團隊）**
- 入口：Telegram Bot
- 資料：Notion
- 通知：Email

**原則：先跑通一條線，再擴展。**

---

## 3. Skill 只用白名單

### 風險說明

ClawHub（OpenClaw 的 Skill 市集）目前有 5,700+ Skills，但生態系仍在早期階段：

- 已有社群通報惡意 skill 案例（竊取 API Key、注入 prompt）
- 部分 skill 缺乏維護，API 版本過時會導致錯誤
- 未經審查的 skill 可能觸發非預期的 API 呼叫，造成費用暴增

### 課堂規則

1. **只安裝講師審核過的 skills** — 不開放自由搜尋安裝
2. **所有 skill 都有版本號與備份** — 確保課堂環境一致
3. **安裝前檢查 skill 的權限需求** — 拒絕過度要求權限的 skill

### 白名單清單

以下是本課程使用的所有 skills，均已通過講師審查：

| Skill 名稱 | 版本 | 用途 | 對應模組 |
|------------|------|------|----------|
| `google-calendar-mcp` | v1.2.x | Google Calendar 讀寫 | Module 01 - 預約 |
| `gmail-mcp` | v1.3.x | Gmail 讀取、草稿、標籤 | Module 02 - Email |
| `email-triage-skill` | v0.9.x | Email 自動分類與摘要 | Module 02 - Email |
| `notion-mcp` | v1.1.x | Notion Database 讀寫 | Module 03 - CRM |
| `google-sheets-mcp` | v1.0.x | Google Sheets 讀寫 | Module 03 - CRM |
| `telegram-bot-mcp` | v1.4.x | Telegram Bot 收發訊息 | Module 04 - 客服 |
| `web-search-skill` | v1.0.x | 網路搜尋與摘要 | Module 05 - 報告 |
| `cron-scheduler` | v0.8.x | 排程觸發任務 | Module 05 / 06 |

> **注意：** 版本號以課堂發布的 `docker-compose.yml` 為準。請勿自行升級 skill 版本。

---

## 4. 權限最小化

### 原則

每個工具都走最小權限。教學上從最安全的起點開始，學員熟悉後再視需求開放。

### 各工具權限規範

#### Gmail

| 階段 | 權限 | 說明 |
|------|------|------|
| 起步 | `gmail.readonly` | 只能讀取信件，不能做任何修改 |
| 進階 | `gmail.compose` | 可以建立草稿（Draft），但不會自動寄出 |
| 完整 | `gmail.send` | 可直接寄信，僅在學員確認理解風險後開放 |

**鐵律：先 Draft 不 Auto-send、先 Read 不 Modify、先 Label 不 Delete。**

#### Google Calendar

| 階段 | 權限 | 說明 |
|------|------|------|
| 起步 | `calendar.readonly` | 只能查詢行事曆 |
| 進階 | `calendar.events` | 可建立單一事件 |
| 完整 | `calendar.events` + 指定行事曆 | 只操作指定的行事曆，不碰主行事曆 |

**鐵律：先 Create 不 Bulk update、只操作指定行事曆。**

#### CRM（Notion / Sheets）

| 階段 | 權限 | 說明 |
|------|------|------|
| 起步 | Read + Append | 只能讀取和新增資料 |
| 進階 | Read + Append + Update | 可修改非核心欄位 |
| 完整 | Full access | 僅在學員理解風險後開放 |

**鐵律：先 Append 不 Delete、不修改核心欄位。**

#### Claude Code

| 設定 | 說明 |
|------|------|
| 保留權限提示 | 每次執行敏感操作前都會詢問確認 |
| 不使用 `--dangerously-skip-permissions` | 這個 flag 會跳過所有安全確認，課堂上絕對不用 |

**鐵律：保留權限提示，不使用 `--dangerously-skip-permissions`。**

### 權限開放檢查清單

在開放更高權限前，學員必須確認：

- [ ] 我理解這個權限允許 AI 做什麼
- [ ] 我知道最壞情況會發生什麼
- [ ] 我有辦法在出問題時立即停止（知道怎麼停 container）
- [ ] 我已經在安全環境測試過

---

## 5. 把「設定」變成表單

### 原則

學員填的是**商業欄位**，不是技術參數。

### 對比

| 傳統做法（技術參數） | 本課程做法（商業欄位） |
|---------------------|----------------------|
| 修改 `CLAUDE.md` 的 system prompt | 填寫「客服口吻：親切友善」 |
| 設定 `calendar_id: "abc123@group..."` | 填寫「可預約時段：週一三五 10-17 點」 |
| 調整 `email_triage_rules.json` | 填寫「分類規則：報價/發票/會議」 |
| 修改 `cron expression: "0 8 * * *"` | 填寫「報告發送時間：每日 08:00」 |

### 流程

```
學員填寫 business_profile_form.md
        │
        ▼
Claude Code 讀取表單內容
        │
        ▼
自動修改以下技術檔案：
├── CLAUDE.md（system prompt、口吻、角色設定）
├── skill config（API 參數、資料庫 ID、行事曆 ID）
├── prompt templates（確認訊息、回覆模板、報告格式）
└── scheduling config（排程時間、提醒天數）
        │
        ▼
產出安裝確認報告
```

### 為什麼這是 Vibe Coding 最有價值的地方

Vibe Coding 的精髓不是讓非技術者學寫程式碼——而是讓他們**用自然語言描述需求，由 AI 處理技術設定**。

- 學員說「我的營業時間是週一到五 9 點到 6 點」→ Claude Code 自動改 calendar config
- 學員說「客服語氣要親切一點」→ Claude Code 自動改 system prompt
- 學員說「超過 3 天沒回的客戶要提醒我」→ Claude Code 自動改 follow-up rules

**這才是 AI 自動化真正普及的方式：不是教每個人寫程式，而是讓每個人都能設定自己的 AI 助手。**
